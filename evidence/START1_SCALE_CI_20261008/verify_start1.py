"""Verify boot1 raw evidence and explicit word-range caveats."""
import argparse
import hashlib
import json
from pathlib import Path
from sweep import parse, equivalent

ap=argparse.ArgumentParser(); ap.add_argument('artifact',type=Path); args=ap.parse_args(); p=args.artifact
load=lambda n:json.loads((p/n).read_text())
for name,digest in load('hashes.json').items():
    assert hashlib.sha256((p/name).read_bytes()).hexdigest()==digest,name
assert all(r['exit_code']==0 for r in load('commands.json'))
for validation in load('small_validation.json'):
    target=validation['target']
    for tag,eventful in [('original',False),('observed',True),('repeat',True)]:
        parsed=parse((p/f'small{target}-{tag}.log').read_text(),target,eventful)
        assert parsed==validation[tag]
    assert equivalent(validation['original'],validation['observed'])
    assert equivalent(validation['observed'],validation['repeat'])
    assert validation['observed']['widen_events']==validation['repeat']['widen_events']
    r=validation['observed']; py=validation['python']
    assert py['stdout']==r['hashes']['stdout'] and py['source']==r['hashes']['source']
    assert py['padwidth']==target and py['growth']==target-1
v=load('verdict.json')
assert v['classification']=='PARAMETRIC_ASCII_OUTSIDE_BOOT_WORD'
assert v['closed_word_machine_claim']==v['dynamic_shrinking']=='NOT_CLAIMED'
if v['status']=='PARAMETRIC_1_TO_20_MEASURED_SCOPED':
    rows=load('runs.json'); assert [r['target'] for r in rows]==list(range(1,21))
    for r in rows:
        parsed=parse((p/f'rung{r["target"]}.log').read_text(),r['target'])
        for k in parsed: assert parsed[k]==r[k]
        assert r['gate']['decision']=='GO' and r['peak_rss_bytes']<=r['gate']['budget_bytes']
    assert rows[0]['fields']['growth']=='0' and rows[-1]['fields']['growth']=='19'
    assert len(rows[-1]['widen_events'])==19
print(json.dumps(v))
