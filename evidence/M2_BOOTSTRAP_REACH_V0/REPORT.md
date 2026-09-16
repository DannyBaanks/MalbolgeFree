# M2 — Bootstrap del inicializador propio de lmao-lite: reachability

Fecha: 2026-09-13. Sigue a `../A5_LMAO_PARITY_V0`. Milestone M2: inicializador en
tiempo de ejecución propio (clean-room). Antes de escribir un emisor, se mide qué se
puede alcanzar. LMAO solo como oráculo de comportamiento; **no se leyó su `gen_init.c`**.

## Pregunta

Para materializar valores en tiempo de ejecución hacen falta las micro-ops Classic
`Rot` (rotar un trit) y `Opr` (crazy con A). ¿Qué bytes de salida son alcanzables, y con
qué operandos?

## Hechos del motor (congelados)

De `MALBOLGE/malbolge.py` (crazy/rot verificados):

- `crazy(0, x)` por trit: 0→1, 1→1, 2→2. Si `x` no tiene trit 2, da **29524 = C1**
  (todos-unos). Es la semilla.
- `crazy(x, x)` por trit: 0→1, 1→0, 2→1.
- `rot(v) = v//3 + (v%3)*3⁹`.

## Tres modelos, tres resultados medidos

| modelo | movimientos | bytes alcanzables | archivo |
|---|---|---:|---|
| **1. semilla sola (PRERREGISTRADO)** | `rot(A)`, `crazy(A, semilla)` | **2 / 256** | `REACH_RESULTS.json` |
| 2. banco de 5 constantes, con `rot(A)` (exploratorio) | `rot(A)`, `crazy(A, Ck)` | **256 / 256** | `CONSTBANK_RESULTS.json` |
| 3. **emitible** (exploratorio) | `A:=rot(Ck)` (resetea), `crazy(A, Ck)` | **25 / 256** | `EMITTABLE_RESULTS.json` |

### Modelo 1 — el prerregistrado: 2/256

`BOOTSTRAP_ALL_BYTES_REACHABLE = PARTIAL 2/256`. Con la semilla y un operando fijo, el
banco nunca crece (ningún valor alcanzable es válido en carga). Es el mismo muro que el
acomodo solo-en-carga de `A5`: sin más operandos no hay bootstrap.

### Modelo 2 — con las 5 constantes de LMAO: 256/256, pero no emitible tal cual

Con `{C0, C1, C2, C20, C21}` como operandos reutilizables se alcanzan **los 256 bytes**
(4,711 valores), desde `C0` y desde `rot(C1)`. Un intérprete de micro-ops **escrito
aparte** repite cada secuencia testigo: **0 discrepancias** en los 256 (paridad de dos
implementaciones sobre la búsqueda). El byte 'A' sale en 5 ops; el peor caso, 13.

**Caveat descubierto este turno:** este modelo usa `rot(A)` como movimiento, y el gadget
`ROT` real de HeLL **no rota A**: hace `A := rot(celda)`, descartando A. Así que estas
secuencias no son emitibles tal cual.

### Modelo 3 — solo lo emitible con las 5 constantes: 25/256

Con los movimientos que un gadget HeLL sí puede dar (`A := rot(Ck)` que resetea, o
`A := crazy(A, Ck)`), y el banco fijo de 5, solo se alcanzan **25 bytes**.

`OWN_EMITTER_ALL_BYTES = NOT_DEMONSTRATED (25/256)`.

## Qué significa (la parte honesta)

- **El bootstrap NO está hecho.** Con las piezas emitibles y las 5 constantes desnudas
  solo llegamos a 25 de 256 bytes.
- **La parte difícil es materializar constantes arbitrarias**, es decir el `gen_init` de
  LMAO. Al leer su `example_simple_hello_world.hell` se confirma cómo lo hace: los
  operandos no son las 5 constantes, sino expresiones calculadas **en tiempo de
  ensamblado** (`'e'<<1`, `C2!'H'`, `C2!('l'!C1!C1)`) que su `gen_init` escribe en celdas
  en ejecución. El runtime solo baraja esas constantes ya materializadas con Rot/Opr.
- **Nuestro reverse-engineering es correcto:** el patrón que dedujimos (cadenas Opr/Rot
  sobre constantes) es exactamente el de Lutter. Lo que falta implementar es el
  materializador, no el barajado.

## Lo que le da esto al siguiente turno

El inicializador propio, medido:

1. Necesita materializar un **valor arbitrario** en una celda, no solo las 5 constantes.
2. Con `rot(A)` disponible (dos celdas de trabajo, no una) el espacio es completo
   (modelo 2, 256/256): el materializador debe construir con **dos celdas
   independientes**, no una, para tener `crazy(A, X)` con A ≠ X.
3. Se mide contra LMAO en A5, byte por byte, y contra el intérprete de paridad.

## Veredictos

| Claim | Estado |
|---|---|
| Semilla + un operando alcanza los bytes | PARTIAL 2/256 (prerregistrado) |
| Las 5 constantes de LMAO bastan como operandos (con rot(A)) | DEMONSTRATED 256/256, paridad 0 fallos |
| `rot(A)` es un gadget HeLL emitible | DESTROYED (el ROT real hace A:=rot(celda)) |
| Un emisor con las 5 constantes desnudas alcanza los bytes | NOT_DEMONSTRATED 25/256 |
| Nuestro bootstrap propio está terminado | NO — falta el materializador de constantes (gen_init) |

## Slice 2 — síntesis inline verificada de punta a punta (2026-09-13)

Tras medir la reachability, se implementó el sintetizador clean-room y se probó de
verdad, no en abstracto. Modelo **inline** (el que ensambla y corre bien por LMAO):

- `rotload(v)`: `ROT v R_ROT` → A := rot(v)
- `combine(v)`: `CRAZY v R_CRAZY` → A := crazy(A, v)

con cada `v` un byte imprimible (33..126) puesto en línea por el cargador. Nada de
gen_init; el byte objetivo nunca se guarda como literal.

`tools/hell_materialize.py` sintetiza; `tools/lmao_bridge.py` ensambla con el LMAO
externo y verifica en los dos motores.

### Resultado (`INLINE_E2E_RESULTS.json`, `run_inline_e2e.py`)

| métrica | valor |
|---|---|
| bytes alcanzables (inline) | **201 / 256** |
| verificados en el oráculo Python | **201 / 201** |
| verificados en Zig (muestra) | **23 / 23**, pasos idénticos al oráculo |
| violaciones de no-guardado | **0** |

`INLINE_SYNTH_E2E = PASS`. Ejemplos reales corridos en ambos motores: `ISyCo`,
`\n\t\x07` (control), `\x80` (byte alto). El newline sale de `ROT 118` → rot(118)=19722,
19722 mod 256 = 10, sin almacenar el 10.

### Lo que falta (honesto)

- **55 bytes (154..208)** no salen en el modelo inline: necesitan una **celda de trabajo
  persistente** (rotar tras acumular). El intento con una celda etiquetada `WK` dio salida
  equivocada (193 en vez de 10 para newline) por la convención de llamada de HeLL con
  operando etiquetado; aislado, es el siguiente slice.
- El bootstrap propio de las **5 constantes base** (materializarlas sin cargarlas) sigue
  pendiente; aquí se evitó usándolas: solo se combinan imprimibles cargables.

### Veredictos (slice 2)

| Claim | Estado |
|---|---|
| Síntesis clean-room de bytes (inline) verificada en Malbolge real, 2 motores | DEMONSTRATED 201/256 |
| El byte objetivo nunca se almacena (síntesis genuina) | DEMONSTRATED 0 violaciones |
| Cobertura total 256/256 con lo emitible hoy | NOT_DEMONSTRATED (faltan 154..208, celda persistente) |
