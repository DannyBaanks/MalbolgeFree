"""Bounded evidence collection; deliberately never runs E20 or edits old results."""
import hashlib
import json
import os
import platform
import resource
import subprocess
import time
from pathlib import Path

ORIGIN = Path(__file__).resolve().parent
ROOT = ORIGIN.parents[1]
HERE = Path(os.environ.get('E20_OUTPUT', str(ORIGIN))).resolve()
ENV = dict(os.environ, ZIG_GLOBAL_CACHE_DIR='/tmp/e20-zig-global', ZIG_LOCAL_CACHE_DIR='/tmp/e20-zig-local', PYTHONDONTWRITEBYTECODE='1')

def bounded():
    resource.setrlimit(resource.RLIMIT_AS, (2 * 2**30, 2 * 2**30))
    resource.setrlimit(resource.RLIMIT_CPU, (180, 180))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

def run(name, cmd, stdin=b''):
    started = time.time()
    p = subprocess.run(['/usr/bin/time', '-v', *cmd], cwd=ROOT, env=ENV,
                       capture_output=True, input=stdin, timeout=240, preexec_fn=bounded)
    raw = p.stdout + p.stderr
    (HERE / (name + '.log')).write_bytes(raw)
    (HERE / (name + '.stdout')).write_bytes(p.stdout)
    row = dict(name=name, command=cmd, exit_code=p.returncode,
               elapsed_seconds=time.time()-started, log_sha256=hashlib.sha256(raw).hexdigest(), stdout_sha256=hashlib.sha256(p.stdout).hexdigest(), stdout_hex=p.stdout.hex())
    print(json.dumps(row), flush=True)
    return row

if __name__ == '__main__':
    if (HERE/'01_PREFLIGHT.json').exists():
        raise SystemExit('Frozen output exists; set E20_OUTPUT to a fresh directory.')
    HERE.mkdir(parents=True, exist_ok=True)
    mem = {line.split(':')[0]: int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemTotal:', 'MemAvailable:', 'SwapTotal:', 'SwapFree:'))}
    need = 3**19+1
    length = need+1000
    dense = (length+12)*4
    stat = os.statvfs('/tmp')
    preflight = dict(timestamp_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        platform=platform.system()+' '+platform.machine(), zig=subprocess.check_output(['zig','version'],env=ENV).decode().strip(),
        memory_bytes=mem, tmp_free_bytes=stat.f_bavail*stat.f_frsize,
        boundary=3**19, planned_steps=need, source_bytes=length, dense_bytes=dense,
        source_plus_dense_bytes=length+dense, source_plus_dense_is_not_peak=True,
        decision='BLOCKED_RESOURCE_GATE', reason='MemAvailable below 10 GiB and source+dense alone exceeds 60% budget',
        peak_budget_bytes=int(mem['MemAvailable']*.6), limits_for_small_runs=dict(address_space_bytes=2*2**30,cpu_seconds=180,wall_seconds=240))
    (HERE/'01_PREFLIGHT.json').write_text(json.dumps(preflight,indent=2)+'\n')
    (HERE/'environment.log').write_text(Path('/proc/self/limits').read_text()+Path('/proc/pressure/memory').read_text())
    rows = []
    for file in ['t_epochal.zig','t_m5_full_vm.zig','t_dense_differential.zig','t_m4_conservative.zig']:
        rows.append(run(file, ['zig','test','--dep','malbolge_free=malbolge_free',f'-Mroot=tests/{file}','-Mmalbolge_free=src/malbolge_free.zig']))
    rows.append(run('epochal_python', ['python3','evidence/compare_epochal.py','--output',str(HERE/'epochal_python.json')]))
    rows.append(run('hash_estimate20', ['python3','evidence/M5_LADDER_SCALE/run_ladder_scale.py','--estimate','20']))
    cfg=HERE/'calibration_cfg.zig'
    cfg.write_text('pub const target_w: u8 = 15;\npub const dense: bool = true;\n')
    cmd=['zig','run','-O','ReleaseFast','--dep','malbolge_free','--dep','ladder_cfg','-Mroot=evidence/M5_LADDER_SCALE/ladder_scale.zig','-Mmalbolge_free=src/malbolge_free.zig',f'-Mladder_cfg={cfg}']
    for i in range(2):
        rows.append(run(f'calibration15_{i+1}',cmd))
    (HERE/'02_RUN.json').write_text(json.dumps(dict(e20_executed=False,e20_status='BLOCKED_RESOURCE_GATE',commands=rows),indent=2)+'\n')
