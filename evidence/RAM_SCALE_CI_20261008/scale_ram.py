"""Measure real epochal rungs; stop before an unsafe allocation. No runtime edits."""
import argparse
import hashlib
import json
import platform
import re
import resource
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / 'evidence/E20_GITHUB_RUN_20261008'
GIB = 2**30

def sha(data):
    return hashlib.sha256(data).hexdigest()

def costs(width):
    if not 11 <= width <= 60:
        raise ValueError('Width must be in 11..60')
    steps = 3**(width-1)+1
    source = steps+1000
    cells = source+12
    capacity = 1
    while capacity*80//100 < source+16:
        capacity *= 2
    # u64 is a hypothetical representation, not implemented or measured here.
    cell_bytes = 4 if width <= 20 else 8 if width <= 40 else 16
    return dict(width=width, steps=steps, source_bytes=source, cells=cells,
                hypothetical_cell_bytes=cell_bytes,
                hypothetical_source_array_min_bytes=source+cells*cell_bytes,
                current_representation='dense_u32' if width<=20 else 'hash_u128',
                current_source_storage_min_bytes=source+cells*4 if width<=20 else source+capacity*33,
                hash_capacity=capacity, dense_u32_supported=width<=20)

def gate(width, available, disk, predicted):
    c = costs(width)
    budget = available*60//100
    reasons=[]
    if available<10*GIB: reasons.append('MEMAVAILABLE_BELOW_10_GIB')
    if disk<8*GIB: reasons.append('TEMP_DISK_BELOW_8_GIB')
    if predicted>budget: reasons.append('PREDICTED_PEAK_ABOVE_BUDGET')
    if c['current_source_storage_min_bytes']>budget: reasons.append('CURRENT_STORAGE_MIN_ABOVE_BUDGET')
    if not c['dense_u32_supported']: reasons.append('DENSE_U32_WIDTH_CEILING')
    return dict(**c, available_bytes=available, disk_free_bytes=disk,
                budget_bytes=budget, predicted_peak_with_25_percent_margin=predicted,
                decision='GO' if not reasons else 'NO_GO', reasons=reasons)

def projections():
    rows=[]
    for ram in [16,32,64,128]:
        budget=ram*GIB*60//100
        allowed_current=[w for w in range(11,61) if costs(w)['current_source_storage_min_bytes']*125//100<=budget]
        allowed_hypothetical=[w for w in range(11,61) if costs(w)['hypothetical_source_array_min_bytes']*125//100<=budget]
        rows.append(dict(total_ram_gib=ram,assumed_available_gib=ram,budget_bytes=budget,
                         current_storage_gate_max=max(allowed_current),
                         hypothetical_wider_dense_storage_gate_max=max(allowed_hypothetical),
                         status='PROJECTION_ONLY_NOT_A_CAPABILITY_DEMONSTRATION',
                         note='Optimistic available=total; source+array/storage minimum with25% margin. Runtime/output overhead can reduce this maximum.'))
    return rows

def parse_run(text, width):
    f=dict(x.split('=',1) for x in re.search(r'RESULT (.*)',text).group(1).split())
    h=dict(x.split('=',1) for x in re.search(r'HASH (.*)',text).group(1).split())
    need=costs(width)['steps']
    assert f['status']=='MAX_STEPS' and f['repr']=='dense'
    for key, val in dict(target=width,steps=need,padwidth=width,growth=width-10,final_c=need,cells=need+1012,capacity=0).items():
        assert int(f[key])==val,(key,f)
    assert int(h['final_d'])==need and h['assisted']=='0'
    assert 0<int(h['encrypted'])<=need
    for key in ['source','stdout']:
        assert re.fullmatch('[0-9a-f]{64}',h[key])
    events=[dict(x.split('=',1) for x in l.split()[1:]) for l in text.splitlines() if l.startswith('WIDEN ')]
    assert len(events)==width-10
    for old,event in zip(range(10,width),events):
        assert {k:int(v) for k,v in event.items()}==dict(step=3**old+1,c=3**old,d=3**old,old_w=old,new_w=old+1)
    rss=int(re.search(r'Maximum resident set size \(kbytes\): (\d+)',text).group(1))*1024
    return dict(width=width,fields=f,hashes=h,widen_events=events,peak_rss_bytes=rss)

def verify_seed():
    manifests=json.loads((SEED/'hashes.json').read_text())
    for name in ['instrumented_core.zig','probe.zig','e20_result.json','small_validation.json','provenance.json']:
        assert sha((SEED/name).read_bytes())==manifests[name],name
    provenance=json.loads((SEED/'provenance.json').read_text())
    assert sha((ROOT/'src/malbolge_free.zig').read_bytes())==provenance['hashes']['src/malbolge_free.zig']
    small=json.loads((SEED/'small_validation.json').read_text())
    assert small['original']['fields']==small['observed']['fields']==small['repeat']['fields']
    assert small['original']['hashes']==small['observed']['hashes']==small['repeat']['hashes']
    return provenance

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--estimate-only',action='store_true')
    args=parser.parse_args()
    out=args.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    def save(name,data): (out/name).write_text(json.dumps(data,indent=2)+'\n')
    runs=[]; commands=[]; gates=[]
    verdict=dict(status='NOT_DEMONSTRATED',measured_widths=[],next_rung_executed=False)
    def snapshot(label):
        mem={l.split(':')[0]:int(l.split()[1])*1024 for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith(('MemTotal:','MemAvailable:','SwapTotal:','SwapFree:'))}
        data=dict(memory=mem,disk_free_bytes=shutil.disk_usage(out).free,
                  pressure=Path('/proc/pressure/memory').read_text(),
                  process_limits=Path('/proc/self/limits').read_text())
        save(label+'.json',data)
        return data
    def execute(name,cmd,limit):
        def limits():
            resource.setrlimit(resource.RLIMIT_AS,(limit,limit))
            resource.setrlimit(resource.RLIMIT_CPU,(600,600))
            resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        start=time.monotonic()
        proc=subprocess.run(['/usr/bin/time','-v',*cmd],cwd=ROOT,capture_output=True,timeout=660,preexec_fn=limits)
        raw=proc.stdout+proc.stderr
        (out/(name+'.log')).write_bytes(raw)
        commands.append(dict(name=name,command=cmd,exit_code=proc.returncode,
                             elapsed_seconds=time.monotonic()-start,log_sha256=sha(raw),
                             address_space_limit_bytes=limit,cpu_seconds=600,wall_seconds=660))
        save('commands.json',commands)
        if proc.returncode: raise RuntimeError(f'{name} exit {proc.returncode}; classify from raw log')
        return raw.decode()
    try:
        provenance=verify_seed()
        save('projections.json',projections())
        save('costs_11_to_60.json',[costs(w) for w in range(11,61)])
        initial=snapshot('environment_initial')
        save('provenance.json',dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
            timestamp_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),platform=platform.platform(),
            harness_sha256=sha(Path(__file__).read_bytes()),seed=provenance,
            zig=None if args.estimate_only else subprocess.check_output(['zig','version']).decode().strip()))
        if args.estimate_only:
            verdict['status']='ESTIMATE_ONLY_NO_VM_EXECUTION'
            return
        for name in ['instrumented_core.zig','probe.zig']:
            shutil.copyfile(SEED/name,out/name)
        seed=json.loads((SEED/'e20_result.json').read_text())
        last_peak=seed['peak_rss_bytes']; last_width=20
        binaries={}
        for width in range(14,22):
            state=snapshot(f'environment_before_{width}')
            factor=3**(width-last_width) if width>=last_width else 1/3**(last_width-width)
            predicted=max(128*2**20,int(last_peak*factor*1.25))
            decision=gate(width,state['memory']['MemAvailable'],state['disk_free_bytes'],predicted)
            gates.append(decision); save('gates.json',gates)
            print(json.dumps(dict(width=width,gate=decision['decision'],reasons=decision['reasons'])),flush=True)
            if decision['decision']=='NO_GO':
                verdict.update(status='STOPPED_BEFORE_NEXT_ALLOCATION',next_width=width,reasons=decision['reasons'])
                break
            cfg=out/f'cfg{width}.zig'
            cfg.write_text(f'pub const target_w: u8 = {width};\npub const dense: bool = true;\n')
            binary=out/f'vm{width}'
            execute(f'build{width}',['zig','build-exe','-O','ReleaseFast','--dep','malbolge_free','--dep','ladder_cfg',
                f'-Mroot={out/"probe.zig"}',f'-Mmalbolge_free={out/"instrumented_core.zig"}',f'-Mladder_cfg={cfg}',f'-femit-bin={binary}'],2*GIB)
            binaries[binary.name]=sha(binary.read_bytes()); save('binary_hashes.json',binaries)
            result=parse_run(execute(f'rung{width}',[str(binary)],decision['budget_bytes']),width)
            assert result['peak_rss_bytes']<=decision['budget_bytes']
            result['executable_elapsed_seconds']=commands[-1]['elapsed_seconds']
            result['gate']=decision
            runs.append(result); save('runs.json',runs)
            verdict['measured_widths'].append(width)
            last_peak=result['peak_rss_bytes']; last_width=width
            print(json.dumps(dict(width=width,peak_rss_bytes=last_peak,seconds=result['executable_elapsed_seconds'])),flush=True)
        else: raise AssertionError('Must stop at the unsupported21 gate')
        verdict['scope']='Finite linear ladder witness, single Zig implementation. No global RAM-to-language-width theorem.'
    except Exception as error:
        verdict.update(status='NOT_DEMONSTRATED',error=str(error))
        raise
    finally:
        save('verdict.json',verdict)
        manifest={p.name:sha(p.read_bytes()) for p in out.iterdir() if p.is_file() and p.suffix in ['.json','.log','.zig']}
        save('hashes.json',manifest)
        print(json.dumps(verdict),flush=True)

if __name__=='__main__': main()
