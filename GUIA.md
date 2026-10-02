# Guia de uso

## Comando principal

```powershell
py malbolge_cli.py verify
```

Salida verificada:

```text
VERIFY PASS 472392 positional instruction pairs
```

## Regla de oro

`free-pure` y `free-assisted` son perfiles distintos. No presentes una
ejecucion con opcodes 69-79 como prueba de Classic o Free-pure.

## Ensamblar un plan

```powershell
py malbolge_cli.py assemble "in,out,rot,movd,opr,nop,end"
```

Salida verificada:

```text
ub%%:?K
```

## Inspeccionar una fuente

```powershell
py malbolge_cli.py disassemble "ub%%:?K"
```

Salida verificada: siete filas con opcodes `23, 5, 39, 40, 62, 68, 81`.

## Construir un witness determinista

```powershell
py tools/constructive_assembler.py "in,out,rot,movd,opr,nop,end"
```

Salida verificada:

```text
PLAN=in,out,rot,movd,opr,nop,end
SOURCE='ub%%:?K'
BYTES=7
```

## Ejecutar un programa

```powershell
py malbolge_cli.py run --file corpus/classic/hello.mal
```

Salida verificada:

```text
status=HALTED steps=40 padwidth=10
stdout[12 bytes]=48656c6c6f20576f726c6421
stdout_text='Hello World!'
final a/c/d: see trace for registers (run --trace)
max_addr_touched=63 max_value=29554 growth_events=0
```

Con entrada por stdin (el programa `ubO` lee un byte y lo imprime):

```powershell
py malbolge_cli.py run "ubO" --stdin "A"
```

Sin `--stdin`, `in` lee EOF y el programa imprime `ff`:

```text
status=HALTED steps=3 padwidth=10
stdout[1 bytes]=ff
```

## Inspeccionar el estado sin ejecutar

```powershell
py malbolge_cli.py inspect "ubO"
```

Salida verificada:

```text
profile=classic width=10 mem_limit=59049 growth=fixed padwidth=10
program_len=3 initial_registers: a=0 c=0 d=0 steps=0 stdout=empty
first 3 cells (char -> decoded op):
  [     0] 'u'  op=23
  [     1] 'b'  op= 5
  [     2] 'O'  op=81
frozen tail (lazy-fill period, 12 cells from program_len):
  29507 71 29509 77 29501 79 29507 71 29509 77 29501 79
tail repeats with period 12 from cell 15 onward
```

## Traza paso a paso

```powershell
py malbolge_cli.py trace "ubO" --limit 3
```

Salida verificada:

```text
status=HALTED steps=3 padwidth=10
showing 3 events of a 3-step run (a/c/d are accumulator/code/data registers):
  step      c      d  op  a_before  a_after  enc@
     1      0      0    in        0       -1  0
     2      1      1   out       -1       -1  1
     3      2      2  halt       -1       -1  -
```

Se lee así: en el paso 1 (`in` sin stdin) el acumulador pasa de `0` a `-1`
(EOF); en el paso 2 (`out`) emite `a % 256 = 255`; en el paso 3 (`halt`)
termina. `enc@` es la celda que se auto-cifró tras ejecutar (`-` = ninguna).

## Códigos de salida (parte del contrato)

| Exit | Significado |
|---|---|
| `0` | El programa terminó (`HALTED`) o el comando de inspección funcionó |
| `1` | Error de uso o fuente inválida (no imprimible o menos de 2 celdas) |
| `2` | No terminó dentro de `--max-steps` (`MAX_STEPS`) |

Verificado: `run "ubO" --max-steps 1` da exit `2`; `run "a"` da exit `1`
con `INVALID SOURCE: need at least 2 cells for crazy-fill seed`.

## Perfiles (regla de oro ampliada)

El CLI solo ofrece `classic` y `free_pure`. **No hay `free_assisted` a
propósito**: la ISA auxiliar (opcodes 69-79, `TAPE_BASE`, `lock_noencrypt`)
solo existe en el motor Zig, y este CLI usa el core Python, que implementa
exactamente los ocho opcodes Classic. Ofrecerlo sería mentir en silencio
comportándose como `free_pure`. `free_pure` acepta `--growth fixed|epochal`
y `--width`.

## Como leer los estados

| Estado | Significado | Accion |
|---|---|---|
| `VERIFY PASS` | Codec posicional completo para Classic | Puede continuar |
| `VERIFY FAIL` | Hay una regresion en el codec | No publicar evidencia |
| `HALTED` | El runtime termino por opcode 81 | Revisar stdout y pasos |
| `MAX_STEPS` | Se alcanzo el limite | Aumentar limite solo con control |
| `NOT_DEMONSTRATED` | Falta referencia o control suficiente | No elevar el claim |

## Trampas

- El codec demuestra inversion posicional, no sintesis arbitraria con saltos y
  auto-cifrado.
- `tape_epoch_19.json` describe un tape de 19 celdas; no es evidencia de un
  runtime Unshackled de memoria `3^19`.
- La paridad con un Unshackled externo permanece `NOT_DEMONSTRATED` hasta tener
  una implementacion de referencia localizada y una ejecucion reproducible.
- No usar `git reset`, `git clean`, `git stash` ni checkout masivo en estos
  working trees.
