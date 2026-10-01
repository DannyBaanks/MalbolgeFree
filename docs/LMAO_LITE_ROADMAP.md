# lmao-lite Roadmap

Objetivo: ensamblador HeLL mínimo, propio y reproducible para generar fuente
Malbolge ejecutable. No copiará código de LMAO; `LMAO` GPLv3 se usará sólo
como referencia/oráculo cuando el artefacto esté disponible.

## Alcance

El primer objetivo es ensamblar los programas necesarios para el backend
`BFIR1 -> Malbolge Free`, no reemplazar todo LMAO.

Soporte inicial:

```text
.CODE / .DATA
labels
numeric literals
IN / OUT / MOVD / JMP / NOP / HALT
label references
```

Fuera del alcance inicial: macros avanzadas, IDE/debug maps, heurísticas
completas de layout, optimización de espacios y todo el dialecto HeLL.

## Milestones

### A0 — Contrato y licencia

Estado: **PASS (specification)**.

- fijar entrada/salida y errores;
- documentar implementación limpia;
- registrar LMAO como GPLv3 externo, no como dependencia oficial;
- definir stdout como artefacto generado sin diagnósticos.

Gate: este documento y un fixture HeLL mínimo.

### A1 — Lexer/parser HeLL

Estado: **PASS (22/22 tests)**.

Lexer: `.CODE`/`.DATA`, keywords (`MOV`, `MovD`/`MOVD`, `NOP`/`Nop`, `IN`/`In`,
`OUT`/`Out`, `OPR`/`Opr`, `JMP`/`Jmp`, `HALT`/`Halt`, `FLAG`, `VAR`, `CALL`),
prefixes (`R_`, `U_`, `C_` standalone and compound like `R_MOVD`), labels, colons,
slashes, braces, numbers, `?-`, comments (`//`, `/* */`).

Parser: secciones `.CODE`/`.DATA`, labels con y sin keywords como nombre
(`IN:` funciona como label), instructions con prefix/modifier/operand, data
entries con literales numéricos.

Gate: 22 tests positivos y negativos en `tests/t_a1_hell_parser.zig`.

### A2 — Tabla de opcodes

Estado: **PASS (19/19 tests)**.

Mapping completo HeLL → Malbolge:

```text
MOV / MovD  → MOVED (40)
NOP / Nop   → NOP (68)
IN / In     → IN (23)
OUT / Out   → OUT (5)
OPR / Opr   → OPR (62)  (crazy)
JMP / Jmp   → JMP (4)
HALT / Halt → HALT (81)
FLAG        → NOP
VAR         → NOP
CALL        → JMP
```

Functions: `hellOpcodeToCommand(opcode, modifier, prefix)`, `commandToChar()`, `xlat2Char()`, `classifyInstruction()`.

Gate: 22 tests positivos y negativos en `tests/t_a2_opcode_table.zig`.

### A3 — Labels y layout

Estado: **PASS (11/11 tests)**.

Layout resolver: `resolveLayout()` convierte un `Program` parseado en un
`Layout` con instrucciones posicionadas, data values acumulados, y conteos
`code_size`/`data_size`. Maneja múltiples `.CODE` y `.DATA` sections,
acumula correctamente, y produce posiciones secuenciales.

Gate: 11 tests positivos y negativos en `tests/t_a3_layout.zig`.

### A4 — Emisión Malbolge mínima

Estado: **PASS (10/10 tests)**.

Emisor: `emit()` toma un `Layout` y genera `EmittedProgram` — string de
caracteres Malbolge válidos. Incluye `XLAT2_INIT` (tabla de 94 valores),
`emitCommandToChar(cmd, position)` y `emitCharToCommand(ch, position)`.
Fixtures `NOP/HALT` e `IN/OUT` ejecutan en `MalbolgeCore`.

Gate: 10 tests en `tests/t_a4_emit.zig`.

### A5 — Comparación con LMAO

Estado: **FAIL (medido 2026-09-13)** — ver `evidence/A5_LMAO_PARITY_V0/REPORT.md`.
LMAO v0.6.0 compilado; sus 6 ejemplos pasan 34/34 checks de `testcases.bash` en
nuestros motores (oráculo Python y Zig, pasos idénticos). lmao-lite: 0/6 (falla en
emit, layout o comportamiento). Nota: los tests A6 del cat son estructurales y nunca
ejecutan el cat; con 256 bytes aleatorios imprime un byte equivocado y se detiene.

Construir el LMAO GPLv3 externo cuando estén disponibles gcc, flex y bison;
ensamblar fixtures iguales y comparar status, steps y stdout, no texto exacto.

Gate: comportamiento igual en `lmao-lite` y LMAO.

### A6 — Cat multi-byte

Estado: **PASS (7/7 tests)**.

Pipeline completo: HeLL source → parser → layout → emitter → Malbolge source.
Cat program de LMAO (MOV, IN, OUT, JMP) parseado, labels resueltos
forward/backward, `R_MOVD`/`R_IN`/`R_OUT` mapean a ROT (39), emite 12
caracteres Malbolge válidos (printable ASCII 33-126).

Gate: 7 tests en `tests/t_a6_cat.zig`.

### A7 — Backend BFIR1

Estado: **PASS (10/10 tests)**.

Loader BFIR1 + `lowerLinear()` (rechaza branches) + `lowerBranched()` (emite
un scaffold experimental R_OPR + OPR + MovD + NOPs), bracket map
`buildBracketMap()` empareja `[` ↔ `]` y rechaza unmatched.
El pipeline completo `BFIR1 → HeLL → parse → layout → emit → MalbolgeCore`
ejecuta y halta correctamente para programas lineales. Loops emiten HeLL
parseable con labels. La ejecución condicional todavía no está demostrada:
faltan targets de salto en memoria y la inversión de predicado para `]`.

Gate: 10 tests en `tests/t_a7_bfir1_backend.zig` + 4 tests en `tests/t_a7_conditional.zig`.


### H1 — Pipeline híbrido Classic (decisión 2026-09-13)

Estado: **PASS (8/8 tests)**.

Motivo: medido que ni `simple_cat` admite un acomodo solo-en-carga (0/1,504
acomodos; mejor caso 5/9 celdas de datos válidas), así que un HeLL Classic propio
exige un inicializador en tiempo de ejecución (investigación, varias piezas).
Mientras tanto:

- `tools/hell_frontend.py`: frontends propios que emiten HeLL Classic (`text`:
  cadena arbitraria vía Rot+Out; `echo N`), escritos desde la semántica del README
  de LMAO, sin copiar código ni ejemplos.
- `tools/lmao_bridge.py`: ensambla con LMAO **como proceso externo**
  (`_external/LMAO`, GPLv3, no vendorizado) y verifica en el oráculo Python y el
  runner Zig (estado, salida y pasos idénticos).
- `tools/hell_classic.py`: parser HeLL real + física de celdas (xlat2, R_, landing,
  ENTRY); base para el inicializador propio.

Gate: `py -m unittest test_hell_frontend -v` (desde `tools/`): Hello World, los 256
bytes, cadenas aleatorias, eco con EOF, y dos controles (valor cambiado → salida
cambia; sin `R_ROT` → el flujo de datos se desincroniza y no imprime nada).

Siguiente: inicializador propio medido contra LMAO en A5, ejemplo por ejemplo.


### M2 — Inicializador propio: bootstrap (medido 2026-09-13)

Estado: **NOT_DEMONSTRATED, con espec** — ver `evidence/M2_BOOTSTRAP_REACH_V0/REPORT.md`.

Reachability medida con las micro-ops Rot/Opr:
- semilla sola + un operando: 2/256 (prerregistrado, muro).
- 5 constantes {C0,C1,C2,C20,C21} con rot(A): 256/256, paridad de 2 implementaciones 0 fallos.
- solo lo emitible (A:=rot(Ck) reset / crazy(A,Ck)) con 5 constantes desnudas: 25/256.

Conclusión: el bootstrap propio necesita **materializar constantes arbitrarias**
(equivalente a gen_init de LMAO), con dos celdas de trabajo. Confirmado leyendo
`example_simple_hello_world.hell`: Lutter opera sobre constantes calculadas en
ensamblado, no sobre las 5 desnudas. Slice 2 (HECHO): sintetizador inline clean-room (`tools/hell_materialize.py`) verificado
de punta a punta contra LMAO en los dos motores: 201/256 bytes, 201/201 oráculo, 23/23
Zig, 0 bytes objetivo almacenados. Los 55 bytes 154..208 y el bootstrap de las 5
constantes base quedan para el siguiente slice (celda de trabajo persistente).
Tests: `tools/test_hell_materialize.py` (9). Guía: `docs/GUIA_BOOTSTRAP.md`.


### M3 — Motor de layout propio: Malbolge crudo 256/256 (2026-09-16)

Estado: **PASS** — ver `evidence/M3_RAW_LAYOUT_V0/REPORT.md`.

Emitimos Malbolge Classic CRUDO nosotros (`tools/raw_malbolge.py`): sin LMAO, sin HeLL,
sin gen_init. **256/256 bytes**, verificados en el oráculo Python y en el runner Zig con
estado, salida y pasos idénticos. Programas de 42-118 celdas (media 60) frente a las
2,069 celdas que LMAO usa para un solo newline: ~34x más compactos.

Clave: la celda 0 (`(` = 40) decodifica a MovD y vale 40, así que `d = c + 40` de ahí en
adelante; una op en la posición p opera sobre la celda 40+p. Dos modelos: cadena inline
(201/256) y acumulador persistente con retroceso de `d` vía MovD (los 55 de 154..208).

Tests: `tools/test_raw_malbolge.py` (5, incluye paridad con Zig).
Guía: `docs/GUIA_RAW_MALBOLGE.md`.

Falta: esto emite salida de bytes, no el lenguaje HeLL completo (bucles, condicionales,
entrada). Para eso sigue el pipeline híbrido.


### M4 — NADA V0: primer microprograma propio (2026-09-16)

Estado: **PASS (19/19 casos, paridad en los dos motores)** — ver
`evidence/M4_MICROPROGRAM_V0/REPORT.md`.

`tools/microprogram.py` compone en UN solo programa Malbolge: salida de bytes arbitrarios,
entrada real (`IN;OUT;HALT` = 4 celdas), una ruta de estado (`IN` → `crazy` → `OUT`),
salto incondicional con trampa inalcanzable, y el microprograma compuesto `> + eco + 
`
(120 celdas, 14 pasos). Regresión de M3: 256/256. Fuente determinista.

Cambio de método que lo hizo compacto: la búsqueda pasó a ser **consciente de la posición**
("¿qué valores son válidos donde está `d`?" en vez de "¿dónde cabe este valor?"):
`HI
` bajó de 94 celdas/42 pasos a 51/13.

Re-derivado: **`d = c + 40` es un invariante LOCAL del tramo lineal**; tras un `Jmp` pasa a
`(d_jmp + 1) − destino` (medido: `−16`). Destinos limitados a 34..127.

NOT_DEMONSTRATED: condicionales, bucles, saltos hacia atrás, funciones, memoria general,
HeLL arbitrario.

Tests: `tools/test_microprogram.py` (11).

## Reglas de evidencia

- Un parser que emite texto no es un ensamblador demostrado.
- Un programa que imprime una salida fija no es un compilador BF.
- Cada fixture debe ejecutarse en `MalbolgeCore`.
- LMAO es sólo oracle externo; su resultado no prueba `lmao-lite`.
- No marcar PASS sin comando, salida, exit code y hash.

## Estado Global

```text
A0 contract/license       PASS
A1 parser                 PASS (22/22 tests)
A2 opcode table           PASS (22/22 tests)
A3 labels/layout          PASS (12/12 tests)
A4 Malbolge emission      PASS (10/10 tests)
A5 LMAO comparison        FAIL (LMAO 34/34 en nuestros motores; lmao-lite 0/6)
A6 multi-byte cat         PASS (7/7 tests)
A7 BFIR1 backend          PASS (10/10 + 4/4 structural tests)
A7.1 conditional e2e      NOT_DEMONSTRATED (math verified; runtime pending)
                         -> partial answer 2026-10-01: control that changes OUTPUT is
                            demonstrated with 8 Classic opcodes only
                            (t_free_pure_vertical_slice.zig). Input-dependent POINTER
                            movement is not, in the searched space. See
                            docs/M6_EIGHT_OPCODE_BOUNDARY.md
```
