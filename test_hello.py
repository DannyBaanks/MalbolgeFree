import sys
sys.path.insert(0, 'evidence')
import malbolge as m

src = '(=<`#9]~6ZY32Vx/4Rs+0No-&Jk)"Fh}|Bcy?`=*z]Kw%oG4UUS0/@-ejc(:\'8dc'
text, steps, status = m.run(src, max_steps=2000000)
print('status:', status)
print('steps:', steps)
print('output bytes:', [hex(ord(c) & 0xFF) for c in text])
print('output:', repr(text))