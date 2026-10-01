# M6.1 — Malbolge Backend ABI

Estado: **SPECIFIED / NOT_IMPLEMENTED**.

Este contrato define la frontera entre la imagen `BFIR1` y el programa
Malbolge que la ejecutará. No declara que ninguna primitiva ya funcione en
Malbolge.

## Referencia Externa

`MALBOLGE-MB-DATABASE/mbir/` y `vm_malbolge/` contienen una VM MBIR, una ABI
de bytecode y artefactos Malbolge de transporte que sirven como material de
comparación. MBIR no es una dependencia, no es el formato oficial de este
proyecto y no sustituye el backend directo `BFIR1 -> Malbolge Free`.

La comparación permitida es:

```text
BFIR1 VM propia       = referencia primaria
MBIR reference VM     = control externo de diseño
Malbolge Free backend = implementación objetivo
```

No se debe convertir un PASS de MBIR en un PASS de `malbolge-free`.

## Input Stream

El programa Malbolge recibe la imagen completa por stdin, byte a byte:

```text
BFIR1
u32 instruction_count, little-endian
instruction records, 12 bytes each
```

El backend debe consumir exactamente los bytes de la imagen antes de ejecutar
la primera instrucción BF. EOF durante la imagen es un error de imagen, no una
célula BF con valor cero.

## BF State

La máquina BF lógica tiene estos registros observables:

```text
pc             índice de instrucción BFIR1
data_pointer   índice de cinta, inicialmente 0
tape[i]        byte u8, inicialmente 0
input_pos      bytes consumidos después de la imagen
output         bytes emitidos
steps          instrucciones BF ejecutadas
```

La cinta es finita para hacer los límites reproducibles. **El tamaño es una
decisión de contrato, no una ley de la máquina**: vive en
`MalbolgeCore.DEFAULT_TAPE_SIZE` (256) y se cambia por instancia con
`setTapeSize(n)` antes de `run`. `TAPE_BASE` (1000) es fijo, así que la cinta
conserva su ventana de direcciones documentada.

El wrapping de celda es de byte `u8` en los opcodes de assisted. Fuera de
`[0, tape_size - 1]` el intérprete de referencia devuelve
`POINTER_OUT_OF_BOUNDS`; en el core Free el puntero puede avanzar y las celdas
fuera de la cinta devuelven relleno perezoso, no ceros. Esa asimetría es
deliberada y es la razón por la que el tamaño es un parámetro contractual: si se
agranda la cinta, ambos lados deben seguir comparando el mismo rango.

Ampliar la cinta es capacidad, NO semántica: `tests/t_m7_tape_width.zig` exige
que el comportamiento dentro de las primeras 256 celdas sea idéntico con cinta
default y cinta amplia. El límite de pasos será parte del harness y nunca se
interpretará como terminación normal.

## Malbolge Process Contract

- stdin contiene sólo `BFIR1` y el input BF concatenado, con una frontera de
  longitud conocida por el loader;
- stdout contiene sólo el output BF;
- ningún diagnóstico se mezcla con stdout;
- terminación normal requiere `pc == instruction_count`;
- errores deben clasificarse como `INVALID_IMAGE`, `POINTER_OUT_OF_BOUNDS`,
  `INPUT_EOF` o `MAX_STEPS`;
- el primer vertical slice debe ejecutar `> < + - .` sin saltos.

## Milestones

### M6.1 ABI

Este documento y el formato `BFIR1` existente. Gate: revisión y fixtures
deterministas. **PASS para especificación; implementación pendiente.**

### M6.2 Primitivas lineales

Load/store de cinta, movimiento, aritmética byte y output en un programa
Malbolge real. Gate: tres imágenes sin loops comparan stdout, cinta, puntero,
steps y terminación contra `BFIR1 VM`.

Estado actual: **DEMONSTRATED**. `tests/t_m62_differential.zig` compara tres
imágenes lineales (`+++.-.`, `>+++<+>.>.`, `,+.`) contra la referencia BFIR1
en stdout, cinta completa (256 celdas), puntero final y terminación. La cinta
vive en las celdas Free `TAPE_BASE .. TAPE_BASE + tape_size - 1`
(`TAPE_BASE`/`D_REWIND`/`D_LEFT`); el puntero BF final se expone como
`RunResult.final_d - TAPE_BASE`. El conteo de pasos
se compara a nivel BF (el lowering expande cada op en varios pasos Malbolge).

Control disponible: `tests/t_m6_malbolge_primitives.zig` ejecuta el artefacto
Classic `ubO` y confirma input/output dentro de `MalbolgeCore`. Esto sólo
valida la interfaz de I/O; no satisface el gate de cinta ni de `BFIR1`.

M6.2a añade `tests/t_m6_2a_payload_relay.zig`: el mismo artefacto recibe el
payload `A` y reenvía `A` sin cambios. Es un relay de un byte, no un loader
general ni un intérprete de `BFIR1`.

### M6.3 Input

Implementar `,`, consumo de input y EOF definido. Gate: echo y EOF.

Estado actual: **PASS para echo lineal y EOF**. `STORE` (opcode 74),
`TAPE_BASE` (75) y `D_REWIND` (76) mantienen la celda de cinta estable entre
accesos sucesivos. `tests/t_m63_input.zig` verifica echo de un byte y EOF como
byte cero. Esto no cierra todavía movimiento completo ni branches.

### M6.4 Branches

Implementar `[` y `]`, primero loops simples y luego anidados.

Estado actual: **DEMONSTRATED**. Opcodes Free `JZ` (78) / `JNZ` (79) realizan el
salto condicional con destino inmediato base-94 de 3 dígitos inline. `TAPE_BASE`
arma el substrato estable (`lock_noencrypt`): los programas Free no se
auto-cifran (los programas Classic nunca ejecutan `TAPE_BASE`, así que la
paridad Classic queda intacta). `tests/t_m64_branch.zig` compara tres programas
con loops (`+++[-].`, `++[>++<-]>.`, `,[.,]`) contra la referencia BFIR1.

### M6.5 Full Differential

Comparar al menos cinco programas BF con output, input, cinta final, puntero,
terminación, steps y checkpoints de traza.

Estado actual: **DEMONSTRATED (estado final; checkpoints por-paso NO)**.
`tests/t_m65_differential.zig` compara cinco programas — clear-loop,
move-loop, reader-loop con EOF, copy-loop y un **`Hello World`** (12 emisiones,
esquema de celda fresca `>N[>M<-]>R.` = N*M+R, verificado previamente en dos
intérpretes independientes: raw y BFIR1, ambos byte-idénticos) — contra la
referencia BFIR1 en stdout, cinta completa (256 celdas), puntero final y
terminación, todos `HALTED` idénticos. El conteo de pasos se compara a nivel BF
(el código Malbolge expande cada op). Los checkpoints de traza por-paso no son
comparables: el backend es compilador, no trazador.

### M7 Quinepiler

Sólo después de M6.5: ejecutar un `compiler.bf` dentro del backend Malbolge y
verificar regeneración byte a byte de `BFIR1`.

Estado actual: **NOT_DEMONSTRATED (seed only)**. `tests/t_m7_uroboros_seed.zig`
demuestra la semilla de quinepiler (compilación BF→BFIR1 canónica y
reproducible, `source_bytes=55 image_bytes=669 deterministic=PASS`). Ejecutar un
`compiler.bf` completo *dentro* del backend Malbolge y regenerar `BFIR1`
byte-por-byte requiere un compilador BF en BF autocontenido — trabajo aparte,
no cubierto por M6.x.

## Current Verdict

```text
BFIR1 format          = PASS
Host BFIR1 VM         = PASS
M6.1 ABI              = SPECIFIED
M6.2 Malbolge backend  = DEMONSTRATED (linear slice + 3-image differential vs BFIR1 reference)
M6.3 input             = DEMONSTRATED (echo + EOF)
M6.4 branches          = DEMONSTRATED (3 loop programs vs reference)
M6.5 full differential = DEMONSTRATED (5 programs incl. Hello World)
lmao-lite A1 parser    = PASS (22/22 tests)
lmao-lite A2 opcodes   = PASS (22/22 tests)
lmao-lite A3 layout    = PASS (11/11 tests)
lmao-lite A4 emission  = PASS (10/10 tests)
lmao-lite A6 cat       = PASS (7/7 tests)
lmao-lite A7 backend   = PASS (10/10 tests)
M7 Quinepiler          = NOT_DEMONSTRATED (seed only + capacity measured,
                          see docs/M7_TAPE_CAPACITY.md)
```
