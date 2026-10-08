import importlib.util
import json
from collect import HERE, ROOT, ORIGIN, run

if (HERE/'nagoya_compare.json').exists():
    raise SystemExit('Frozen output exists; set E20_OUTPUT to a fresh directory.')
HERE.mkdir(parents=True, exist_ok=True)

rows = [run('nagoya_compile', ['gcc','-O2','-std=gnu99',str(ORIGIN/'nagoya/malbolge20.c'),'-lm','-o','/tmp/e20-nagoya-oracle'])]
(HERE/'eof_echo.mb').write_bytes(b'ubO')
for name, source, data in [('hello20',ORIGIN/'nagoya/hello20.mb',b''),('eof_echo',HERE/'eof_echo.mb',b''),('byte_echo',HERE/'eof_echo.mb',b'A')]:
    rows.append(run('nagoya_'+name, ['/tmp/e20-nagoya-oracle',str(source)],data))
rows.append(run('zig_fixed20', ['zig','run','--dep','malbolge_free','-Mroot='+str(ORIGIN/'fixed20.zig'),'-Mmalbolge_free=src/malbolge_free.zig']))
spec=importlib.util.spec_from_file_location('mb',ROOT/'src/malbolge_core.py')
mb=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mb)
python=[]
for name, source, data in [('hello20',ORIGIN/'nagoya/hello20.mb',b''),('eof_echo',HERE/'eof_echo.mb',b''),('byte_echo',HERE/'eof_echo.mb',b'A')]:
    vm=mb.MalbolgeCore(width=20,mem_limit=3**20,growth_policy='fixed')
    vm.load(source.read_text())
    result=vm.run(2_000_000,data)
    result['stdout_hex']=result.pop('stdout').encode('latin1').hex()
    python.append(dict(name=name,**result))
(HERE/'nagoya_compare.json').write_text(json.dumps(dict(commands=rows,python_fixed20=python),indent=2)+'\n')
