"""Real VM E20 experiment. No fast-forward; only sparse event instrumentation."""
import argparse
import hashlib
import json
import os
import re
import resource
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def memory():
    return {l.split(':')[0]:int(l.split()[1])*1024 for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith(('MemTotal:', 'MemAvailable:', 'SwapTotal:', 'SwapFree:'))}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--small-only', action='store_true')
    args=parser.parse_args()
    out=args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    rows=[]
    binaries={}
    verdict={'EPOCHAL_19_TO_20':'NOT_DEMONSTRATED','UNBOUNDED_WIDTH_GROWTH':'NOT_DEMONSTRATED','MALBOLGE20_IDENTICAL_TO_FREE_EPOCHAL':'NOT_CLAIMED'}
    def save(name,value):
        (out/name).write_text(json.dumps(value,indent=2)+'\n')
    def command(name,cmd,limit=None):
        def bounded():
            resource.setrlimit(resource.RLIMIT_CORE,(0,0))
            resource.setrlimit(resource.RLIMIT_CPU,(600,600))
            if limit: resource.setrlimit(resource.RLIMIT_AS,(limit,limit))
        start=time.monotonic()
        proc=subprocess.run(['/usr/bin/time','-v',*cmd],cwd=ROOT,capture_output=True,timeout=660,preexec_fn=bounded)
        raw=proc.stdout+proc.stderr
        (out/(name+'.log')).write_bytes(raw)
        row=dict(name=name,command=cmd,exit_code=proc.returncode,seconds=time.monotonic()-start,log_sha256=sha(raw))
        rows.append(row)
        save('commands.json',rows)
        if proc.returncode: raise RuntimeError(f'{name}: exit {proc.returncode}')
        return raw.decode()
    try:
        core=(ROOT/'src/malbolge_free.zig').read_text()
        needle='                self.frontierTrigger(c, d);'
        assert core.count(needle)==1
        instrument=core.replace(needle,'''                const old_width = self.padwidth;
                self.frontierTrigger(c, d);
                if (old_width != self.padwidth) std.debug.print("WIDEN step={d} c={d} d={d} old_w={d} new_w={d}\\n", .{steps, c, d, old_width, self.padwidth});''')
        probe=(ROOT/'evidence/M5_LADDER_SCALE/ladder_scale.zig').read_text()
        probe=probe.replace('    if (vm.padwidth != target', '''    var source_hash: [32]u8 = undefined;
    var stdout_hash: [32]u8 = undefined;
    std.crypto.hash.sha2.Sha256.hash(src, &source_hash, .{});
    std.crypto.hash.sha2.Sha256.hash(res.stdout.items, &stdout_hash, .{});
    std.debug.print("HASH source={s} stdout={s} final_d={d} encrypted={d} assisted={d}\\n", .{std.fmt.bytesToHex(source_hash, .lower), std.fmt.bytesToHex(stdout_hash, .lower), res.final_d, res.encrypted_cells, res.assisted_opcodes});
    if (vm.padwidth != target''')
        (out/'instrumented_core.zig').write_text(instrument)
        (out/'probe.zig').write_text(probe)
        save('provenance.json',dict(timestamp_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),zig=subprocess.check_output(['zig','version']).decode().strip(),hashes={p:sha((ROOT/p).read_bytes()) for p in ['src/malbolge_free.zig','evidence/M5_LADDER_SCALE/ladder_scale.zig','evidence/E20_CI_20261008/run_ci.py']},instrumented_core_sha256=sha(instrument.encode()),probe_sha256=sha(probe.encode())))
        def build(target,observed):
            cfg=out/f'cfg{target}.zig'
            cfg.write_text(f'pub const target_w: u8 = {target};\npub const dense: bool = true;\n')
            binary=out/f'vm{target}-{observed}'
            runtime=out/'instrumented_core.zig' if observed else ROOT/'src/malbolge_free.zig'
            command(f'build{target}-{observed}',['zig','build-exe','-O','ReleaseFast','--dep','malbolge_free','--dep','ladder_cfg',f'-Mroot={out / "probe.zig"}',f'-Mmalbolge_free={runtime}',f'-Mladder_cfg={cfg}',f'-femit-bin={binary}'])
            binaries[binary.name]=sha(binary.read_bytes())
            save('binary_hashes.json',binaries)
            return binary
        def check(text,target,events):
            f=dict(x.split('=',1) for x in re.search(r'RESULT (.*)',text).group(1).split())
            need=3**(target-1)+1
            assert f['status']=='MAX_STEPS' and f['repr']=='dense'
            for key,val in dict(steps=need,padwidth=target,growth=target-10,final_c=need,cells=need+1012,capacity=0).items(): assert int(f[key])==val,(key,f)
            h=dict(x.split('=',1) for x in re.search(r'HASH (.*)',text).group(1).split())
            assert int(h['final_d'])==need and 0<int(h['encrypted'])<=need and h['assisted']=='0',h
            ev=[dict(x.split('=',1) for x in line.split()[1:]) for line in text.splitlines() if line.startswith('WIDEN ')]
            if events:
                assert len(ev)==target-10
                for old,event in zip(range(10,target),ev):
                    expected=dict(step=3**old+1,c=3**old,d=3**old,old_w=old,new_w=old+1)
                    assert {k:int(v) for k,v in event.items()}==expected
            rss=int(re.search(r'Maximum resident set size \(kbytes\): (\d+)',text).group(1))*1024
            return dict(fields=f,hashes=h,widen_events=ev,peak_rss_bytes=rss)
        for test in ['t_m5_full_vm.zig','t_dense_differential.zig']:
            for observed in [False,True]:
                runtime=out/'instrumented_core.zig' if observed else ROOT/'src/malbolge_free.zig'
                command(f'{test}-{observed}',['zig','test','--dep','malbolge_free',f'-Mroot=tests/{test}',f'-Mmalbolge_free={runtime}'])
        a=check(command('small-original',[str(build(12,False))],2*2**30),12,False)
        binary=build(12,True)
        b=check(command('small-observed',[str(binary)],2*2**30),12,True)
        c=check(command('small-repeat',[str(binary)],2*2**30),12,True)
        assert a['fields']==b['fields']==c['fields'] and a['hashes']==b['hashes']==c['hashes'] and b['widen_events']==c['widen_events']
        save('small_validation.json',dict(original=a,observed=b,repeat=c))
        if args.small_only:
            verdict['note']='Local bounded validation only; E20 not attempted.'
            return
        initial=memory()
        free=shutil.disk_usage(out).free
        if initial['MemAvailable']<10*2**30 or free<8*2**30:
            save('preflight.json',dict(memory=initial,disk_free_bytes=free,decision='NO_GO'))
            verdict['EPOCHAL_19_TO_20']='BLOCKED_RESOURCE_GATE'
            return
        calibration=check(command('calibration18',[str(build(18,True))],3*2**30),18,True)
        save('calibration18.json',calibration)
        full=build(20,True)
        available=memory()
        peak=int(calibration['peak_rss_bytes']*((3**19+1)/(3**17+1))*1.25)
        budget=int(available['MemAvailable']*.6)
        go=available['MemAvailable']>=10*2**30 and shutil.disk_usage(out).free>=8*2**30 and peak<=budget
        save('preflight.json',dict(memory=available,disk_free_bytes=shutil.disk_usage(out).free,source_bytes=3**19+1001,dense_bytes=4*(3**19+1013),calibrated_peak_with_25_percent_margin=peak,budget_bytes=budget,decision='GO' if go else 'NO_GO',note='RSS extrapolation is not a mathematical upper bound; OS address-space ceiling applied.'))
        if not go:
            verdict['EPOCHAL_19_TO_20']='BLOCKED_RESOURCE_GATE'
            return
        result=check(command('e20',[str(full)],budget),20,True)
        save('e20_result.json',result)
        verdict['EPOCHAL_19_TO_20']='DEMONSTRATED_SCOPED'
    except Exception as error:
        verdict['error']=str(error)
        verdict['EPOCHAL_19_TO_20']='NOT_DEMONSTRATED'
        raise
    finally:
        save('verdict.json',verdict)
        # Upload evidence, not temporary binaries, compiler caches or giant sources.
        files={str(p.relative_to(out)):sha(p.read_bytes()) for p in out.iterdir() if p.is_file() and p.suffix in ['.json','.log','.zig']}
        save('hashes.json',files)
        print(json.dumps(verdict),flush=True)

if __name__=='__main__': main()
