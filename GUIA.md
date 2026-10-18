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

Sin `--stdin`, `in` lee EOF —que vale `3^10 - 1 = 59048`— y el programa imprime
`a % 256`, o sea `a8`:

```text
status=HALTED steps=3 padwidth=10
stdout[1 bytes]=a8
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
     1      0      0    in        0    59048  0
     2      1      1   out    59048    59048  1
     3      2      2  halt    59048    59048  -
```

Se lee así: en el paso 1 (`in` sin stdin) el acumulador pasa de `0` a `59048` —
EOF asigna el valor canónico `3^10 - 1`, no un centinela; ver
`docs/CLASSIC_SEMANTICS.md`—; en el paso 2 (`out`) emite `a % 256 = 168`
(`0xa8`); en el paso 3 (`halt`) termina. `enc@` es la celda que se auto-cifró
tras ejecutar (`-` = ninguna).

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

### El EOF bajo `--growth epochal` (aviso obligatorio)

El valor que `in` asigna al acabarse la entrada es `3^padwidth - 1`, no una
constante. Con `classic` y con `free_pure --growth fixed` el `padwidth` nunca
crece, así que ese valor fijo es `59048` en width 10 y `26` en width 3. Con
`--growth epochal` el ancho sigue a la frontera de direcciones y el EOF cambia
de valor en el paso del ensanche: un programa escrito contra `59048` deja de
reconocer el fin de entrada en cuanto la máquina ensancha.

```powershell
py malbolge_cli.py trace tests/frontier_witness.txt --file --profile free_pure --growth epochal --width 3 --max-steps 400 --limit 400
```

Salida verificada: los 72 eventos `in` de esa ejecución se agrupan en tres
valores; la columna *paso* es el primer evento de cada grupo.

| paso | `in` asigna | igual a |
|---|---|---|
| 68 | `80` | `3^4 - 1` |
| 82 | `242` | `3^5 - 1` |
| 256 | `728` | `3^6 - 1` |

Control, mismo programa y mismo límite de pasos sin política de crecimiento:

```powershell
py malbolge_cli.py trace tests/frontier_witness.txt --file --profile free_pure --growth fixed --width 3 --max-steps 400 --limit 400
```

Los 72 eventos `in` quedan en `26` (`3^3 - 1`) y la traza termina con
`padwidth=3`; el comando epochal termina con `padwidth=6`. En un programa real
ocurre lo mismo: el quine `corpus/classic/quine_m281.mal` lee `59048` bajo
`--growth fixed` y `177146` (`3^11 - 1`) bajo `--growth epochal`, tras ensanchar
en el paso 1230 (`evidence/f11_frontier_eof_20261018.json`, ledger entrada 34).

Los dos comandos salen con exit `2` (`MAX_STEPS`) porque el witness no halta;
eso no inválida la traza, que se imprime antes de salir.

Regla práctica: no reutilices un test de EOF de Classic bajo `--growth
epochal`, y no compares stdout entre perfiles sin declarar el `padwidth` final.

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
- La paridad con Unshackled son dos claims, no uno. Contra el `Unshackled.c`
  original es `NOT_DEMONSTRABLE` por construccion: ese programa llama a
  `srand(time(NULL))` y un peer no determinista no puede refutar nada. Contra
  una referencia determinista de ancho fijo `3^19` pasa a `DEMONSTRATED` en
  alcance estrecho con el gate F13: `end`, EOF, wrap, los ocho opcodes de
  dispatch y `crazy` a 19 trits coinciden con `bolge19` en tres maquinas; `rot`
  y la tabla de auto-cifrado **no** coinciden y se reportan como divergencias
  medidas o identificadas. No leas F13 como paridad con Lutter Unshackled.
- F13 necesita el checkout hermano `../MalbolgeLispSlop` (fuente + perfil +
  binario). Sin el sale con codigo 3 y el harness lo imprime como SKIP; eso es
  lo que muestra CI mientras no se decida vendear la referencia, que es una
  decision de licencia, no un paso tecnico. Su alcance es region 0
  (`c < 3^18`) y programas de cuatro instrucciones: ver
  `docs/F13_UNSHACKLED_K19_PREGISTRATION.md` antes de citar un numero.
- Con `--growth epochal` el EOF vale `3^padwidth - 1` y cambia de valor en el
  ensanche (`59048` -> `177146` en el quine medido): un test de fin de entrada
  heredado de Classic deja de funcionar en silencio. Ver el aviso en Perfiles.
- No usar `git reset`, `git clean`, `git stash` ni checkout masivo en estos
  working trees.
