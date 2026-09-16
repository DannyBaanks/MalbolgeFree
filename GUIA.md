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
