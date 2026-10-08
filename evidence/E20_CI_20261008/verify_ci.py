"""Verify downloaded CI artifact hashes and the scoped E20 verdict."""
import argparse
import hashlib
import json
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('artifact', type=Path)
args=parser.parse_args()
p=args.artifact
load=lambda name:json.loads((p/name).read_text())
for file,expected in load('hashes.json').items():
    assert hashlib.sha256((p/file).read_bytes()).hexdigest()==expected,file
small=load('small_validation.json')
assert small['original']['fields']==small['observed']['fields']==small['repeat']['fields']
assert small['original']['hashes']==small['observed']['hashes']==small['repeat']['hashes']
verdict=load('verdict.json')
if verdict['EPOCHAL_19_TO_20']=='DEMONSTRATED_SCOPED':
    assert load('preflight.json')['decision']=='GO'
    result=load('e20_result.json')
    assert len(result['widen_events'])==10
    for old,event in zip(range(10,20),result['widen_events']):
        assert {k:int(v) for k,v in event.items()}==dict(step=3**old+1,c=3**old,d=3**old,old_w=old,new_w=old+1)
    f=result['fields']
    assert f['steps']==f['final_c']=='1162261468'
    assert f['padwidth']=='20' and f['growth']=='10' and f['status']=='MAX_STEPS'
    assert result['hashes']['final_d']=='1162261468' and result['hashes']['assisted']=='0'
    assert result['peak_rss_bytes']<=load('preflight.json')['budget_bytes']
print(json.dumps(verdict))
