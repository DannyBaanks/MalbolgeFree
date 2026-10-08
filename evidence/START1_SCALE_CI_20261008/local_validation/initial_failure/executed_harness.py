"""Real parametric boot1 sweep; ASCII outside the initial word is explicitly labeled."""
import argparse
import hashlib
import importlib.util
import json
import re
import resource
import shutil
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SEED=ROOT/'evidence/E20_GITHUB_RUN_20261008'
GIB=2**30

def sha(data): return hashlib.sha256(data).hexdigest()

def parse(text,target,events=True):
    f=dict(x.split('=',1) for x in re.search(r'RESULT (.*)',text).group(1).split())
    h=dict(x.split('=',1) for x in re.search(r'HASH (.*)',text).group(1).split())
    label=dict(x.split('=',1) for x in re.search(r'LABEL (.*)',text).group(1).split())
    need=3**(target-1)+1
    assert f['status']=='MAX_STEPS' and f['repr']=='dense'
    for key,value in dict(target=target,steps=need,padwidth=target,growth=target-1,final_c=need,cells=need+1012,capacity=0).items():
        assert int(f[key])==value,(key,f)
    assert h['final_d']==str(need) and h['assisted']=='0'
    assert 0<int(h['encrypted'])<=need
    assert label==dict(boot_width='1',source_ascii_min='33',boot_word_max='2',source_cells_outside_boot_word=str(need+1000),classification='PARAMETRIC_ASCII_OUTSIDE_BOOT_WORD')
    ev=[dict(x.split('=',1) for x in l.split()[1:]) for l in text.splitlines() if l.startswith('WIDEN ')]
    if events:
        assert len(ev)==target-1
        for old,e in zip(range(1,target),ev):
            assert {k:int(v) for k,v in e.items()}==dict(step=3**old+1,c=3**old,d=3**old,old_w=old,new_w=old+1)
    audit=[dict(x.split('=',1) for x in l.split()[1:]) for l in text.splitlines() if l.startswith('AUDIT ')]
    rss=int(re.search(r'Maximum resident set size \(kbytes\): (\d+)',text).group(1))*1024
    return dict(target=target,fields=f,hashes=h,label=label,widen_events=ev,small_trace_audit=audit,peak_rss_bytes=rss)

def equivalent(a,b):
    return all(a[k]==b[k] for k in ['fields','hashes','label','small_trace_audit'])

def python_case(target):
    spec=importlib.util.spec_from_file_location('mb',ROOT/'src/malbolge_core.py')
    mb=importlib.util.module_from_spec(spec); spec.loader.exec_module(mb)
    need=3**(target-1)+1
    source=bytes(next(cv for cv in range(33,127) if (cv+pos)%94 in (5,23,62,68)) for pos in range(need+1000))
    vm=mb.MalbolgeCore(width=1,mem_limit=None,growth_policy='epochal')
    vm.load(source.decode('ascii'))
    r=vm.run(need,b'')
    return dict(status=r['status'],steps=r['steps'],padwidth=r['padwidth'],growth=r['growth_events'],final_c=vm.stats['final_c'],final_d=vm.stats['final_d'],encrypted=vm.stats['encrypted_cells'],source=sha(source),stdout=sha(r['stdout'].encode('latin1')))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',type=Path,required=True); ap.add_argument('--small-only',action='store_true'); args=ap.parse_args()
    out=args.output.resolve(); out.mkdir(parents=True,exist_ok=False)
    save=lambda name,data:(out/name).write_text(json.dumps(data,indent=2)+'\n')
    runs=[]; commands=[]; validations=[]; gates=[]; binaries={}
    verdict=dict(status='NOT_DEMONSTRATED',boot_width=1,classification='PARAMETRIC_ASCII_OUTSIDE_BOOT_WORD',measured_targets=[],closed_word_machine_claim='NOT_CLAIMED',dynamic_shrinking='NOT_CLAIMED')
    def execute(name,cmd,limit):
        def limits():
            resource.setrlimit(resource.RLIMIT_AS,(limit,limit)); resource.setrlimit(resource.RLIMIT_CPU,(600,600)); resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        start=time.monotonic()
        p=subprocess.run(['/usr/bin/time','-v',*cmd],cwd=ROOT,capture_output=True,timeout=660,preexec_fn=limits)
        raw=p.stdout+p.stderr; (out/(name+'.log')).write_bytes(raw)
        commands.append(dict(name=name,command=cmd,exit_code=p.returncode,elapsed_seconds=time.monotonic()-start,log_sha256=sha(raw),address_space_limit_bytes=limit,cpu_seconds=600,wall_seconds=660))
        save('commands.json',commands)
        if p.returncode: raise RuntimeError(f'{name}: exit{p.returncode}')
        return raw.decode()
    def snapshot(target):
        m={l.split(':')[0]:int(l.split()[1])*1024 for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith(('MemTotal:','MemAvailable:','SwapTotal:','SwapFree:'))}
        state=dict(memory=m,disk_free_bytes=shutil.disk_usage(out).free,pressure=Path('/proc/pressure/memory').read_text(),limits=Path('/proc/self/limits').read_text())
        save(f'environment_{target}.json',state); return state
    try:
        manifest=json.loads((SEED/'hashes.json').read_text())
        for name in ['instrumented_core.zig','probe.zig','provenance.json']:
            assert sha((SEED/name).read_bytes())==manifest[name]
        provenance=json.loads((SEED/'provenance.json').read_text())
        assert sha((ROOT/'src/malbolge_free.zig').read_bytes())==provenance['hashes']['src/malbolge_free.zig']
        shutil.copyfile(SEED/'instrumented_core.zig',out/'observed_core.zig')
        probe=(SEED/'probe.zig').read_text().replace('target < 11 or target > 30','target < 1 or target > 20').replace('initFreePure(alloc, 10, .epochal)','initFreePure(alloc, 1, .epochal)').replace('target - 10','target - 1')
        probe=probe.replace('    var res = try vm.run(need, "");','''    std.debug.print("LABEL boot_width=1 source_ascii_min=33 boot_word_max=2 source_cells_outside_boot_word={d} classification=PARAMETRIC_ASCII_OUTSIDE_BOOT_WORD\\n", .{len});
    var trace = std.ArrayList(core.TraceEvent).empty;
    defer trace.deinit(alloc);
    var res = if (cfg.audit) try vm.runWithTrace(need, "", &trace) else try vm.run(need, "");
    if (cfg.audit) {
        var width: u8 = 1;
        var fetches = [_]u64{0} ** 21;
        var outside_fetch = [_]u64{0} ** 21;
        var encrypted = [_]u64{0} ** 21;
        var outside_encryption = [_]u64{0} ** 21;
        for (trace.items) |event| {
            if (event.c_before >= core.pow3(width) or event.d_before >= core.pow3(width)) width += 1;
            fetches[width] += 1;
            if (event.cell_before >= core.pow3(width)) outside_fetch[width] += 1;
            if (event.encrypted_value) |value| {
                encrypted[width] += 1;
                if (value >= core.pow3(width)) outside_encryption[width] += 1;
            }
        }
        for (1..21) |w| {
            if (fetches[w] != 0) std.debug.print("AUDIT width={d} fetches={d} fetched_cells_outside_word={d} encrypted_cells={d} encryption_results_outside_word={d}\\n", .{w, fetches[w], outside_fetch[w], encrypted[w], outside_encryption[w]});
        }
    }''')
        assert 'initFreePure(alloc, 1, .epochal)' in probe and 'if (cfg.audit)' in probe
        (out/'probe_start1.zig').write_text(probe)
        save('provenance.json',dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),zig=subprocess.check_output(['zig','version']).decode().strip(),harness_sha256=sha(Path(__file__).read_bytes()),original_core_sha256=sha((ROOT/'src/malbolge_free.zig').read_bytes()),python_core_sha256=sha((ROOT/'src/malbolge_core.py').read_bytes()),observed_core_sha256=sha((out/'observed_core.zig').read_bytes()),probe_sha256=sha(probe.encode()),timestamp_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
        def build(target,observed):
            cfg=out/f'cfg{target}.zig'; cfg.write_text(f'pub const target_w: u8 = {target};\npub const dense: bool = true;\npub const audit: bool = {"true" if target<=5 else "false"};\n')
            binary=out/f'vm{target}-{observed}'
            runtime=out/'observed_core.zig' if observed else ROOT/'src/malbolge_free.zig'
            execute(f'build{target}-{observed}',['zig','build-exe','-O','ReleaseFast','--dep','malbolge_free','--dep','ladder_cfg',f'-Mroot={out/"probe_start1.zig"}',f'-Mmalbolge_free={runtime}',f'-Mladder_cfg={cfg}',f'-femit-bin={binary}'],2*GIB)
            binaries[binary.name]=sha(binary.read_bytes()); save('binary_hashes.json',binaries); return binary
        built={}
        for target in range(1,6):
            a=parse(execute(f'small{target}-original',[str(build(target,False))],512*2**20),target,False)
            built[target]=build(target,True)
            b=parse(execute(f'small{target}-observed',[str(built[target])],512*2**20),target)
            c=parse(execute(f'small{target}-repeat',[str(built[target])],512*2**20),target)
            assert equivalent(a,b) and equivalent(b,c) and b['widen_events']==c['widen_events']
            py=python_case(target)
            expected=dict(status=b['fields']['status'],steps=int(b['fields']['steps']),padwidth=int(b['fields']['padwidth']),growth=int(b['fields']['growth']),final_c=int(b['fields']['final_c']),final_d=int(b['hashes']['final_d']),encrypted=int(b['hashes']['encrypted']),source=b['hashes']['source'],stdout=b['hashes']['stdout'])
            assert py==expected,(target,py,expected)
            validations.append(dict(target=target,original=a,observed=b,repeat=c,python=py)); save('small_validation.json',validations)
        if args.small_only:
            verdict.update(status='SMALL_VALIDATION_SCOPED',targets_validated=[1,2,3,4,5]); return
        seed=json.loads((SEED/'e20_result.json').read_text()); previous_peak=seed['peak_rss_bytes']; previous_target=20
        for target in range(1,21):
            s=snapshot(target); available=s['memory']['MemAvailable']; budget=available*60//100
            factor=3**(target-previous_target) if target>=previous_target else 1/3**(previous_target-target)
            predicted=max(128*2**20,int(previous_peak*factor*1.25)); source=3**(target-1)+1001; minimum=source+4*(source+12)
            reasons=[]
            if available<10*GIB: reasons.append('MEMAVAILABLE_BELOW_10_GIB')
            if s['disk_free_bytes']<8*GIB: reasons.append('TEMP_DISK_BELOW_8_GIB')
            if max(predicted,minimum)>budget: reasons.append('RAM_BUDGET')
            g=dict(target=target,available_bytes=available,budget_bytes=budget,source_bytes=source,source_array_min_bytes=minimum,predicted_peak_with_25_percent_margin=predicted,decision='GO' if not reasons else 'NO_GO',reasons=reasons)
            gates.append(g); save('gates.json',gates)
            if reasons:
                verdict.update(status='BLOCKED_RESOURCE_GATE',blocked_target=target); break
            binary=built[target] if target in built else build(target,True)
            result=parse(execute(f'rung{target}',[str(binary)],budget),target)
            result['executable_elapsed_seconds']=commands[-1]['elapsed_seconds']; result['gate']=g
            assert result['peak_rss_bytes']<=budget
            runs.append(result); save('runs.json',runs); verdict['measured_targets'].append(target)
            previous_peak=result['peak_rss_bytes']; previous_target=target
            print(json.dumps(dict(target=target,boot_width=1,peak_rss_bytes=previous_peak,seconds=result['executable_elapsed_seconds'],label=verdict['classification'])),flush=True)
        else: verdict['status']='PARAMETRIC_1_TO_20_MEASURED_SCOPED'
    except Exception as error:
        verdict.update(status='NOT_DEMONSTRATED',error=str(error)); raise
    finally:
        save('verdict.json',verdict)
        save('hashes.json',{p.name:sha(p.read_bytes()) for p in out.iterdir() if p.is_file() and p.suffix in ['.json','.log','.zig']})
        print(json.dumps(verdict),flush=True)

if __name__=='__main__': main()
