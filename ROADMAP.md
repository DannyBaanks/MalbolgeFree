# Malbolge Free — Roadmap a Máquina Formal

Este roadmap separa el trabajo experimental de los requisitos necesarios para
publicar Malbolge Free como una máquina nueva, reproducible y operable.

## Definición De Cierre

Malbolge Free queda cerrado cuando existe:

- una especificación normativa única;
- un runtime canónico en Zig;
- un oráculo independiente que no comparta implementación;
- paridad Classic demostrada con casos positivos y negativos;
- semántica `epochal` verificada en más de una frontera;
- un programa universal o una reducción válida desde Brainfuck;
- CLI, fixtures, hashes, documentación y CI reproducibles;
- ninguna afirmación `DEMONSTRATED` contradicha por el disco.

El resultado debe llamarse **DEMONSTRATED** solamente cuando exista una corrida
reproducible. Lo demás conserva la etiqueta **NOT_DEMONSTRATED**.

## M0 — Congelar El Contrato

**Objetivo:** decidir qué máquina se está construyendo.

Especificar normativamente:

- estado inicial `a=0, c=0, d=0`;
- representación de memoria y política lazy/eager;
- tabla `crazy` y `rotate`;
- cifrado post-instrucción;
- EOF, entrada y salida byte-oriented;
- límites numéricos y comportamiento de overflow;
- políticas `fixed`, `pad_to_padwidth` y `epochal`;
- trigger de frontera: momento exacto, dirección y preservación del prefijo;
- errores, halt y `MAX_STEPS`.

**Gate:** `docs/SPEC_V1.md` contiene pseudocódigo normativo y ejemplos de
estado. Ningún comportamiento queda definido únicamente por el código.

## M1 — Un Runtime Canónico

**Objetivo:** eliminar la divergencia entre `malbolge-free` y
`Malbolge-Translator`.

- Elegir `src/malbolge_free.zig` como runtime canónico.
- Mantener el motor externo únicamente como oráculo independiente.
- Comparar estado completo, no solamente stdout: `a`, `c`, `d`, memoria tocada,
  pasos, halt y eventos de widening.
- Resolver diferencias de fill, EOF, `crazy`, `rotate` y cifrado.
- Eliminar copias stale de `malbolge_free.zig` o marcarlas como fixtures.

**Gate:** el corpus Classic y un corpus de estados intermedios pasan byte por
byte contra el oráculo independiente.

## M2 — Harness De Pruebas Reproducible

**Objetivo:** que una máquina nueva pueda verificarse con un comando.

- Crear `zig build test` o un runner equivalente.
- Incorporar tests unitarios de cada operación.
- Añadir casos de halt, EOF, input, salto, wrap, memoria vacía y caracteres
  inválidos.
- Añadir tests diferenciales con JSON estable.
- Fijar versiones de Zig y del oráculo.
- Ejecutar el harness en CI con exit code correcto.

**Gate:** una instalación limpia produce el mismo reporte y los mismos hashes.

## M3 — Compatibilidad Classic

**Objetivo:** demostrar que `fixed(width=10, mem_limit=3^10)` es Classic.

- Pasar el corpus completo y ampliar el corpus con programas de entrada,
  salida, loops, saltos y halt.
- Verificar stdout, pasos, estado final y hashes.
- Documentar explícitamente qué parte es paridad observada y qué parte es
  herencia teórica.

**Gate:** `CLASSIC_PARITY_ZIG = PASS` en el runtime canónico, con oráculo
independiente y evidencia nueva.

## M4 — Definir Malbolge Free Como Extensión Conservadora

**Objetivo:** demostrar que Free no rompe Classic.

- Probar que `epochal` sin cruzar frontera es idéntico a `fixed`.
- Probar que el prefijo anterior al widening no cambia.
- Probar que el widening no reejecuta ni reescribe historia.
- Verificar determinismo con misma fuente y mismo input.
- Publicar tabla de invariantes y contraejemplos.

**Gate:** invariantes P1, P2, P3, P4 y P6 pasan automáticamente.

## M5 — Primera Y Segunda Frontera

**Objetivo:** demostrar crecimiento real de la máquina.

- Reproducir `10 -> 11` en `3^10 = 59049`.
- Crear witness reproducible que cruce `11 -> 12` en `3^11 = 177147`.
- Registrar eventos `WIDEN` con paso, `c`, `d`, ancho anterior y nuevo.
- Comparar prefijos y memoria alrededor de ambos eventos.
- C8 ya tiene evidencia M5 en `evidence/f9_repeated_frontier.json`.

**Gate:** dos eventos de widening en una corrida reproducible, con hashes del
witness y del reporte.

## M6 — Turing Completeness Válida

**Objetivo:** evitar la falsa equivalencia “imprime Hello World, por tanto TC”.

Elegir una de estas rutas:

- implementar un compilador BF→Malbolge que preserve la ejecución, incluyendo
  cinta, loops, input y output;
- ejecutar un intérprete Brainfuck o una UTM escrito en Malbolge;
- demostrar formalmente que Free contiene Classic sin cambios y citar la
  reducción Classic→Brainfuck/UTM como claim heredado.

El generador de strings no cuenta como prueba de universalidad: reproduce una
salida finita y no preserva la semántica de un programa arbitrario.

**Gate:** al menos tres programas BF con loops, input y estados distintos
producen la misma traza observable al ejecutarse en BF y en Malbolge, o existe
una prueba formal documentada.

**Progreso:** infraestructura de referencia implementada en
`tests/bf_interpreter.zig`: cinta configurable, límites explícitos, EOF,
errores de puntero y traza por instrucción. Ver
`tests/t_m6_bf_reference.zig`. El lowering BF->IR y su VM diferencial están en
`tests/bf_to_ir.zig`, `tests/bf_ir_vm.zig` y sus tests. Esto no satisface
todavía el gate Malbolge.

Milestones del backend: `docs/MALBOLGE_BACKEND_ABI.md` define M6.1 ABI,
M6.2 primitivas lineales, M6.3 input, M6.4 branches y M6.5 differential full.

## M7 — Producto Operable

**Objetivo:** que otra persona pueda usar la máquina sin conocer el repo.

- CLI estable: `run`, `inspect`, `trace` y `verify`.
- Formato de programa y formato de evidencia documentados.
- Mensajes de error y exit codes estables.
- `GUIA.md` en español con comandos ejecutados y salidas reales.
- Binaries Zig reproducibles o instrucciones de build exactas.
- Licencia, changelog y versión semántica.

**Gate:** una máquina limpia ejecuta un ejemplo desde cero siguiendo sólo la
guía.

## M8 — Release 1.0 Formal

**Objetivo:** publicar sin claims inflados.

- Actualizar `README.md`, `RELEASE_READINESS.md` y `docs/HONESTY_LEDGER.md`.
- Generar hashes de fuentes, binaries, corpus, witnesses y reportes.
- Ejecutar CI final.
- Revisar que todas las filas `CURRENT` coincidan con el disco.
- Crear release con limitaciones explícitas.

**Gate final:** checklist M0–M7 verde, o cada excepción está etiquetada
`NOT_DEMONSTRATED` y no se presenta como capacidad de la máquina.

## Orden Recomendado

1. M0, porque evita construir contra una semántica ambigua.
2. M1, porque la divergencia de runtimes invalida evidencia posterior.
3. M2 y M3, para tener una base de regresión confiable.
4. M4 y M5, para cerrar la semántica Free.
5. M6, para cerrar el claim de universalidad correctamente.
6. M7 y M8, para convertir el experimento en producto publicable.

## Estado Actual

| Milestone | Estado |
|---|---|
| M0 Contrato congelado | PASS: EOF y precision fijados con pruebas (`t_m0_eof_precision.zig`, 10/10); 2 riesgos de precision documentados como limitacion aceptada |
| M1 Runtime canónico | PASS: `src/` canonico; copias stale `tests/`+`evidence/` eliminadas (2026-10-02, sin referencias); un solo runtime con perfiles explicitos |
| M2 Harness reproducible | PASS: `py tests/run_all.py` ejecuta todos los gates M2 |
| M3 Paridad Classic | PASS: corpus 6/6 contra oraculo independiente |
| M4 Extensión conservadora | PASS: degeneración, preservación, determinismo y no-replay observables |
| M4b Slice vertical free-pure | PASS: fixture con salida dependiente del input usando solo los 8 opcodes Classic, `assisted=0`, `lock_noencrypt=false`, cifrado activo; prefijo identico a Classic y frontera cruzada sin ISA aux (`t_free_pure_vertical_slice.zig`, 3/3) |
| M5 Segunda frontera | PASS: `10->11->12` demostrado; evidencia F9; escalera hasta `19` medida (2026-10-01, densa) |
| M6 Turing completeness válida | PASS (vía claim heredado, `docs/TURING_COMPLETENESS_INHERITED.md`): `fixed` == Classic (F4 6/6 reproducible) y Classic es TC (Scheffer 1999, citado). `TURING_COMPLETENESS_NEW_CLAIM` sigue NOT_DEMONSTRATED. Frontera medida: control por output SÍ con 8 opcodes; movimiento de puntero por dato NO en el espacio buscado (`docs/M6_EIGHT_OPCODE_BOUNDARY.md`). El backend asistido (M6.2-M6.5) es una herramienta de conveniencia, no parte del claim |
| M7 Producto operable | PASS: CLI estable `run`/`inspect`/`trace`/`verify`/`assemble`/`disassemble` con exit codes contractuales y guia `GUIA.md` con salidas reales; `trace_run` equivale a `run` (60k pasos); producto usa el core Python (sin toolchain), diferencial Zig↔Python demostrado |
| M8 Release formal 1.0 | EN CURSO: docs sincronizados, hashes generados, CI en ambos OS; release con limitaciones explicitas |

---

## Corrección 2026-10-17 (anexa, no reescribe la tabla anterior)

- **M0**: la fila dice "EOF y precision fijados con pruebas". Las pruebas fijaron
  un valor **incorrecto**: `in` en end-of-input asignaba un centinela (`u128::max` /
  `-1`) normalizado solo dentro de `crazy`, y `out` tras EOF emitía `0xff`. Canónico
  es `3^w - 1` (`0xa8` a `w=10`). Corregido en ambos núcleos y sellado de nuevo;
  `t_m0_eof_precision.zig` ahora afirma el valor canónico y el control `w=19` (`0xda`).
- **M3**: "corpus 6/6 contra oráculo independiente" sigue siendo independencia real,
  pero el oráculo (`Malbolge-Translator/zig/src/engine.zig`) compartía nuestra
  convención de EOF, así que no podía falsificar este bug. Veredicto actual: 4/6 de
  coincidencia con ese oráculo (`evidence/f4_engine_zig_divergence_20261017.json`) y
  **22 veredictos / 44 comparaciones de hash** contra los intérpretes canónicos
  (`evidence/f4c_canonical_parity_20261017.json`, y la re-medición con el oráculo ya
  vendorizado en `evidence/f4c_canonical_parity_vendored_20261017.json`).
  La paridad canónica es la que sostiene M3 hoy; `compare_f4.py` deja de ser gate.
- **M6**: el claim heredado se mantiene, pero su evidencia del paso 1 es ahora F4c.
  El 2026-10-17 se vendorizó el intérprete canónico de Python
  (`vendor/canonical_malbolge_py/malbolge.py`, copia verbatim de
  `github.com/DannyBaanks/MALBOLGE@bf4d6fa`, MIT, con `PROVENANCE.md` que declara el
  repo de origen), así que CI mide la paridad canónica en lugar de omitirla: 10 casos
  × 2 cores × 1 oráculo = 20 comparaciones, medido en un clon sin checkouts hermanos
  (`all_match: true`). El primer run con el oráculo vendorizado **falló en
  windows-latest**: el runner re-end-lineaba el fichero (`core.autocrlf=true`), el pin
  no cuadraba y el gate salió con código 4 — el defecto lo cazó el sello, no la
  prosa; se corrigió con `.gitattributes` (`* -text`). En el run siguiente el oráculo
  ya cuadraba, pero F4c dio MISMATCH en 4 veredictos: el manifest de casos se escribía
  en modo texto y el `\r` sobrante llegaba al núcleo Zig como byte de entrada `0x0d`
  (era un defecto de nuestro arnés, no de Classic; el núcleo no se tocó). Ver
  `evidence/F4C_WINDOWS_EOL_DRIFT_20261018.json`,
  `evidence/F4C_WINDOWS_MANIFEST_CRLF_20261018.json` y ledger entradas 26, 27 y 28 —
  la 28 registra el run `39108877995` (`cc6d26d`) ya **verde en ambos runners**, con
  F4c midiendo 20 comparaciones y `49 PASS / 0 SKIP` en ubuntu y en windows. El pin es un
  SHA-256: si el
  fichero vendorizado deriva, el gate falla con código 4; si se quita y no queda ningún
  oráculo, sale con código 3 (`NOT_DEMONSTRATED`), que CI reporta como skip explícito,
  nunca como PASS inventado.

## Anexo 2026-10-18 — F10: la frontera con un programa real (anexo; no reescribe nada)

`evidence/f10_quine_epochal_20261018.json` responde lo que los testigos sintéticos de
M5 no pueden: si `epochal` se comporta como Classic sobre un programa real que
sobrevive más allá de `3^10`. El programa es el quine de Matthias Lutter, ajeno a este
repo y fijado por hash (`DannyBaanks/MalDOOM:vendor/quines/quine_lutter.malbolge`,
sha256 `dca8476f…`, 59 852 bytes en disco, 59 032 celdas cargadas); no se vendoriza
aquí porque re-hostear bytes de terceros es una decisión de licencia, no una medición.

- **M5/M6 paso 1 (positivo)**: bajo `classic` el núcleo Zig reproduce el quine
  byte a byte — `HALTED` en 69 547 437 pasos, stdout de 59 852 bytes cuyo SHA-256 es
  el del propio programa. Esto **supera la nota (c) de la entrada 24**, que decía que
  este run de 69M de pasos no se había repetido aquí.
- **Frontera**: se cruza en el paso **1230**, no en 59050. `d` es *asignado* a
  `3^10` (primera divergencia Zig en traza: paso 1229), así que la frase "el puntero
  debe caminar hasta `3^(w-1)`" describe el coste de los testigos, no una exigencia de
  la regla. La invariante P1 sí se cumple: la divergencia `pure_fixed` vs `epochal`
  aparece en el paso 1246, después del ensanche.
- **Límite del claim "otro Malbolge"**: `pure_fixed` (sin política de crecimiento
  alguna, solo sin wrap) halta en 6 521 pasos emitiendo 1 byte; `epochal` halta en
  8 761 sin emitir nada. La diferencia con Classic la produce **quitar el wrap de
  direcciones**, que forma parte de la definición de Classic, no el ensanche. Las
  imágenes de memoria pre-ejecución son idénticas en los tres perfiles (`c455d288…`),
  así que no es un efecto de `load`.
- **No es gate**: `compare_quine_epochal.py` no entra en la lista `GATES` de
  `tests/run_all.py`, así que el recuento publicado de 49 gates queda igual. Sin
  MalDOOM al lado, el script sale con código 3 (`NOT_DEMONSTRATED`) en lugar de
  sustituir el programa. Detalle: `docs/HONESTY_LEDGER.md` entrada 29 y
  `evidence/F10_QUINE_EPOCHAL_20261018.hashes.json`.
