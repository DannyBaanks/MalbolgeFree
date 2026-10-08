"""Verify downloaded scale artifact without re-running large workloads."""
import argparse
import hashlib
import json
from pathlib import Path
from scale_ram import gate, parse_run

parser=argparse.ArgumentParser()
parser.add_argument('artifact',type=Path)
args=parser.parse_args()
p=args.artifact
load=lambda f:json.loads((p/f).read_text())
for file,digest in load('hashes.json').items():
    assert hashlib.sha256((p/file).read_bytes()).hexdigest()==digest,file
runs=load('runs.json') if (p/'runs.json').exists() else []
commands=load('commands.json') if (p/'commands.json').exists() else []
assert all(c['exit_code']==0 for c in commands)
for row in runs:
    w=row['width']
    parsed=parse_run((p/f'rung{w}.log').read_text(),w)
    for key in parsed: assert parsed[key]==row[key],(w,key)
    assert row['peak_rss_bytes']<=row['gate']['budget_bytes']
    assert row['gate']['decision']=='GO'
for g in load('gates.json'):
    assert g==gate(g['width'],g['available_bytes'],g['disk_free_bytes'],g['predicted_peak_with_25_percent_margin'])
v=load('verdict.json')
assert [r['width'] for r in runs]==v['measured_widths']
if v['status']=='STOPPED_BEFORE_NEXT_ALLOCATION':
    next_width=v['next_width']
    assert load('gates.json')[-1]['decision']=='NO_GO'
    assert not (p/f'rung{next_width}.log').exists()
    assert not (p/f'cfg{next_width}.zig').exists()
print(json.dumps(v))
