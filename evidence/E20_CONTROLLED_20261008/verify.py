"""Check recorded evidence, negative controls, deterministic fields and hashes."""
import hashlib
import json
import re
from pathlib import Path

p=Path(__file__).resolve().parent
pre=json.loads((p/'01_PREFLIGHT.json').read_text())
assert pre['source_bytes']==3**19+1001
assert pre['dense_bytes']==4*(pre['source_bytes']+12)
assert pre['memory_bytes']['MemAvailable']<10*2**30
assert pre['source_plus_dense_bytes']>pre['peak_budget_bytes']
assert not json.loads((p/'02_RUN.json').read_text())['e20_executed']
for file in ['02_RUN.json','nagoya_compare.json']:
    for row in json.loads((p/file).read_text())['commands']:
        assert row['exit_code']==0, row
        assert hashlib.sha256((p/(row['name']+'.log')).read_bytes()).hexdigest()==row['log_sha256']
a,b=[re.search(r'RESULT .*', (p/f'calibration15_{i}.log').read_text()).group() for i in [1,2]]
assert a==b and 'padwidth=15 growth=5' in a
report=json.loads((p/'epochal_python.json').read_text())
assert report['verdict']=='PASS' and report['python_guard_rejects_wrap']
ref=json.loads((p/'nagoya_compare.json').read_text())
n={row['name'].removeprefix('nagoya_'):row['stdout_hex'] for row in ref['commands'] if row['name'].startswith('nagoya_')}
py={row['name']:row['stdout_hex'] for row in ref['python_fixed20']}
z={}
for line in (p/'zig_fixed20.log').read_text().splitlines():
    if line.startswith('CASE '):
        fields=dict(item.split('=',1) for item in line[5:].split())
        assert fields['status']=='HALTED' and fields['width']=='20' and fields['growth']=='0'
        z[fields['name']]=fields['stdout_hex']
assert n['eof_echo']=='a9' and py['eof_echo']==z['eof_echo']=='ff'
assert n['hello20']==py['hello20']==z['hello20']=='48656c6c6f576f726c64'
assert n['byte_echo']==py['byte_echo']==z['byte_echo']=='41'
manifest=p/'hashes.json'
if manifest.exists():
    for name, sha in json.loads(manifest.read_text()).items():
        assert hashlib.sha256((p/name).read_bytes()).hexdigest()==sha, name
print('Recorded evidence verified: resource block, finite calibration, EOF counterexample.')
