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

## Anexo 2026-10-18 — S1: el sello como gate (anexo; no reescribe los anteriores)

M2 pedía un harness reproducible; le faltaba comprobar su propia afirmación de bytes.
Desde hoy `tests/run_all.py` incluye `S1 seal manifest (SHA256SUMS.txt)`
(`evidence/verify_seal_manifest.py`), que re-hashía las 35 rutas selladas en Python y
sale con código 4 ante deriva, ruta ausente, línea mal formada, duplicado o ruta que
escapa del repo. Local: `50 PASS / 0 FAIL / 0 SKIP`, `manifest_sha256=9140d359…`.
Las seis ramas de fallo se midieron en una copia aparte, incluido el caso CRLF que la
entrada 26 documentó para el oráculo vendorizado. Las cifras de 49 de la tabla y del
anexo anterior quedan como medición histórica de la lista de gates hasta `be39798`.
M2 no sube de estado por esto: sigue PASS, ahora con una comprobación más. Detalle en
`docs/HONESTY_LEDGER.md` entrada 30.

## Anexo 2026-10-18 (2) — capturas crudas de F10 anexadas (anexo; no añade afirmaciones)

Las mediciones negativas de F10 vivían solo como prosa dentro del bloque `trial` del
artefacto sellado. Desde hoy están como bytes: `evidence/F10_QUINE_EPOCHAL_20261018/`
guarda la stdout de consola del run sellado, su informe `/usr/bin/time` y los dos
informes acotados previos (presupuesto de stdout 15 000 con 5 expectativas FALSIFIED de
9; 1 000 000 con 2 de 10), más `PROVENANCE.md`, que separa qué falsaciones son artefacto
del presupuesto y cuál era un defecto propio del checker. Copias literales: el
medido sigue siendo `evidence/f10_quine_epochal_20261018.json`, intacto.

Efecto sobre S1: el manifiesto pasa de 35 a 40 rutas y su identidad impresa por el
gate cambia `9140d359…` → `d45319d1…`. Medido tras anexar: `entries=40 checked=40
ok=40`, `SEAL VERDICT: PASS`, `sha256sum -c --quiet` rc 0 por separado, harness
`50 PASS / 0 FAIL / 0 SKIP` y rc 0. Ninguna de las 5 rutas nuevas es un gate, así que
la lista sigue en 50. El número `9140d359…` citado arriba y en la entrada 30 es el
manifiesto tal como estaba en `8b97437`. Ledger entrada 31.

**CI, el mismo día:** empujado `8b97437..2b57e9d`; run `39118092762` `success`; leído del
log de cada runner (ubuntu `117647889202`, windows `117647889354`), los dos imprimen
`SEAL manifest_sha256=d45319d1… entries=40 checked=40 ok=40 drift=0 missing=0 escaping=0
duplicate=0 malformed=0` con `50 PASS / 0 FAIL / 0 SKIP` y el mismo conjunto de 50 gates.
Un clon limpio comprueba por tanto las 5 capturas anexadas. F10 sigue sin re-ejecutarse en
CI: no está en `GATES` y sin MalDOOM sale con 3. Ledger entrada 32.

## Anexo 2026-10-18 (3) — el experimento de frontera se vendoriza y se re-ejecuta en CI (anexo; no reescribe los anteriores)

El anexo de F10 terminaba con una limitación incómoda: CI no re-ejecutaba F10 porque
el programa de entrada vive en otro repo. Danny eligió exactamente ese cierre
(«F10: que se re-ejecute en CI»), y la forma honesta de hacerlo no era relajar el gate
sino traer un programa propio. `corpus/classic/quine_m281.mal` (`96b670b8…`, 53 562 B)
es copia literal — `cmp` sin diferencias — del registro publicado en
`DannyBaanks/Malbolge-MB-Database:quine/quine_53562_m281.mb`, y el mismo blob
(`e5b6a1a9…`) que `DannyBaanks/BolgeForge@5a55b9b:artifacts/candidate_m281_53562b.mal`.
`corpus/classic/PROVENANCE.md` documenta además que la autoría es reproducible con la
herramienta **publicada**: `python3 synthesize.py 281` (`e401dec1…`, commit `5a55b9b`)
escribió aquí mismo bytes con ese mismo hash.

Dos gates nuevos, ninguno con entrada externa (su rama de salida 3 es inalcanzable por
construcción):

- **F11** `evidence/compare_f11_frontier_eof.py` + `evidence/run_f11_observations.zig`:
  frontera y EOF relativo al ancho en ambos cores. 15 expectativas preregistradas,
  `MATCH=15 FALSIFIED=0`, pared 1,26 s.
- **F12** `evidence/compare_f12_selfreproduction.py`: el halt real de 62 239 852 pasos,
  autorreproducción byte-exacta en ambos cores, contra la respuesta conocida que
  publicaron tres motores externos. `MATCH=7 FALSIFIED=0`, pared 1:52.97
  (Zig 63,1 s + Python 49,8 s), RSS pico 84 044 kB.

Recuento: `tests/run_all.py` re-sellado en su sitio (`e49210fa…`; el `246e9041…`
sustituido queda nombrado en el bloque fechado del manifiesto). Harness local completo:
`52 PASS / 0 FAIL / 0 SKIP`, rc 0, 2:08.21. S1 en ese mismo run imprime
`manifest_sha256=298fe800… entries=53 checked=53 ok=53 drift=0 missing=0 escaping=0
duplicate=0 malformed=0`; `sha256sum -c --quiet` coincide. La identidad del manifiesto
se movió `d45319d1…` → `298fe800…` por las 13 rutas de evidencia nuevas; las citas
anteriores corresponden al manifiesto de sus commits respectivos. F12 recibe timeout
propio de 900 s porque 62 M de pasos en dos cores no caben en los 180 s del default;
los otros 50 gates conservan 180 s sin cambio.

**F10 sigue como estaba**: su checker continúa fuera de `GATES` y sigue saliendo con 3
sin el quine de Lutter al lado; sus bytes sellados no se tocaron. Lo que cambia es la
mitad prospectiva de la frase anterior: un clon limpio ya puede re-ejecutar *esta clase*
de experimento por su cuenta.

## Hallazgo medido aquí — el EOF es relativo al ancho (entra en el límite del claim)

Bajo `pure_fixed`, `in` en EOF devuelve **59 048** (`3**10-1`, paso 7 541). Bajo
`epochal`, el core ensancha `10 → 11` en el paso **1 230** y `in` devuelve **177 146**
(`3**11-1`, pasos 25 687 y 25 702). Ambos cores coinciden en los 8 observables
comparados, y los controles `reproducer.mal` y `hello.mal` son idénticos en los tres
perfiles, así que no es artefacto de la forma del programa.

Consecuencia para la compatibilidad: la identidad documentada en BolgeForge
`crazy(crazy(59048,x),29524) == 0` iff `x == 59048` deja de señalar EOF una vez
ensanchado el ancho. Es una **segunda** incompatibilidad con Classic, distinta de la
frontera/ausencia de wrap que midió F10; el límite del claim «otro Malbolge» se anota
con las dos, no con una. No se afirma nada de Turing-completitud: son dos programas
medidos, no un corpus.

Se corrige por anexo la nota (c) de la entrada 24, que razonaba «estos quines no leen
stdin, así que EOF no les afecta»: bajo `classic` se mide 0 eventos `in` dentro del
presupuesto de 60 000 pasos, pero bajo los perfiles sin wrap el programa **sí** ejecuta
op 23 y recibe un valor relativo al ancho. La fila de la entrada 24 queda intacta.

**Defecto definitorio entre cores, nombrado en vez de promediado:** `max_addr_touched`
es «mayor dirección ESCRITA» en Python (`src/malbolge_core.py:156-161`) y «mayor
dirección LEÍDA O ESCRITA» en Zig (`src/malbolge_free.zig:337-338`); deltas medidos
`classic` 0, `pure_fixed` +2, `epochal` +1. No es campo comparado y el gate lo imprime
así. Detalle en `docs/HONESTY_LEDGER.md` entradas 33 y 34.

**CI, el mismo día:** empujado `b80e28e..318aa9b`; run `39129462270` `success`; leído del
log de cada runner (ubuntu `117681459124`, 3 m 56 s; windows `117681459098`, 7 m 05 s). Los
dos imprimen `SEAL manifest_sha256=298fe800… entries=53 checked=53 ok=53 drift=0 missing=0
escaping=0 duplicate=0 malformed=0`, `SEAL VERDICT: PASS`, 52 líneas `PASS:` y ninguna
`FAIL`/`SKIP`, con el mismo conjunto de 52 gates (tras quitar el `\r` que el propio log de
Windows lleva, el `diff` de los dos conjuntos es vacío). Los números coinciden con el run
local sellado: EOF 59 048 / 177 146, halt de 62 239 852 pasos emitiendo 53 562 bytes con el
sha del propio programa. El coste real de F12 en CI (zig 65,1 s + python 94,8 s en windows;
zig 85,4 s + python 94,8 s en ubuntu; local fue 63,1 s + 49,8 s) confirma que los 180 s del
default no lo habrían contenido. Las dos cifras de Python idénticas son coincidencia a la
resolución de 0,1 s que imprime el gate: se anota como se midió, sin explicar. **Aviso de
entorno:** GitHub anuncia que `ubuntu-latest` migra a Ubuntu 26 el 2026-10-19, así que los
tiempos de CI pueden moverse sin que cambie ni un byte nuestro; lo que separa un cambio de
entorno de una deriva real son los pins y S1. Ledger entrada 35.

**Anexo 2026-10-18 (4) — la guía de operación avisaba de menos de lo que medimos.**
`GUIA.md` explicaba que `in` sin entrada asigna `59048` y que el perfil `epochal` ensancha,
pero no unía las dos cosas: el valor de EOF es `3^padwidth - 1`, así que cambia en el paso
del ensanche y un test de fin de entrada heredado de Classic deja de disparar en silencio.
Ahora está escrito, con dos comandos del CLI medidos en esta máquina antes de redactarlos
(`tests/frontier_witness.txt`, 400 pasos, sin stdin): epochal con `--width 3` da
`80` -> `242` -> `728` (`3^4-1`, `3^5-1`, `3^6-1`) en los pasos 68 / 82 / 256 y termina con
`padwidth=6`; el control con `--growth fixed` deja los 72 eventos `in` en `26` y termina con
`padwidth=3`. Los dos salen con exit `2` porque el witness no halta. No añade ningún claim
nuevo sobre el lenguaje: la afirmación sigue siendo la de la entrada 34, medida allí con
ambos cores; el CLI solo usa el core Python, y eso queda dicho en la propia guía.

**Por qué esto mueve el sello:** `README.md`, `ROADMAP.md`, `RELEASE_READINESS.md`,
`CHANGELOG.md` y `docs/HONESTY_LEDGER.md` no están en `SHA256SUMS.txt`, pero `GUIA.md` sí.
Corregir la guía de operación es entonces un evento de integridad, no un cambio de texto:
la identidad se movió `298fe800…` -> `a39adde94cf5da95…` y las rutas verificadas 53 -> 54.
El quinto path es `tests/frontier_witness.txt`, que hasta ahora solo estaba fijado de forma
transitiva por cinco `@embedFile` de cuatro tests Zig: si alguien lo editaba, ninguna línea
de hash se enteraba. Sus bytes no cambiaron (`3370003c…`, 190 000 B). Tras el anexo, S1
mide `entries=54 checked=54 ok=54 drift=0 missing=0 escaping=0 duplicate=0 malformed=0` y
`sha256sum -c --quiet` devuelve 0 por su cuenta; el harness completo sigue en
`52 PASS / 0 FAIL / 0 SKIP`, rc 0 (2:09.11, RSS pico 92 228 kB). Gates: 52, sin cambios —
la demo de la guía no se subió a `GATES` a propósito. Ledger entrada 36.

**Anexo 2026-10-18 (5) — F13: el primer gate que responde ante una máquina externa
determinista.** `UNSHACKLED_PARITY` estaba escrito como una sola frase sobre dos
afirmaciones distintas. La unreachable sigue siéndolo: `Unshackled.c` llama
`srand(time(NULL))`, así que el original no puede falsificar nada porque no coincide
siquiera consigo mismo. La alcanzable ya está medida: F13 compara nuestros dos cores contra
`MalbolgeLispSlop/src/bolge19.zig` (`47758a3f…`) con su perfil `fixed19.json` (`6cc0afa1…`),
y las 20 expectativas se escribieron antes de ejecutar (`docs/F13_UNSHACKLED_K19_PREGISTRATION.md`).
Resultado: `F13 EXPECTATIONS=20 MATCH=20 FALSIFIED=0`, exit 0. Lo que hace creíble el PASS es
que dos expectativas afirman **desacuerdo**: `rot` (nosotros `0x9e`, referencia `0x92`) y el
contador de halt (`ours = reference + 1`), ambos medidos, no alineados en silencio.

**Alcance declarado por el propio gate:** región 0 (`c < 3^18 = 387 420 489`), imágenes de
como máximo 4 celdas, loader `raw`, tres máquinas por caso. No es paridad con el Unshackled
de Lutter y no se vende como tal. Las divergencias V1 (offsets de región `0, 117, 140`),
V3 (alfabeto de cifrado: nuestras 94 entradas indexadas por `m-33` con guarda `33..126`,
frente a las 135 de la referencia indexadas por `m` con guarda `<135`) y V5 (representación del tail) están **leídas del
código y sin testear**; V2 es la única medida.

**Qué decide Danny, no el harness:** la referencia **no se vendoriza**. Sus avisos piden
copiar-y-revalidar en lugar de importar, así que meterla en `vendor/` es una decisión de
licencia. El gate lee el checkout hermano, se auto-pinea los dos hashes y sale con exit 3
si falta — por eso en CI F13 aparece como `SKIP (NOT_DEMONSTRATED, missing external input)`
mientras el local da `53 PASS / 0 FAIL / 0 SKIP`. Siguientes pasos reales, en orden de coste:
(1) decidir licencia y vendorizar o fijar un fixture mínimo; (2) un gate para región 1/2, que
es donde vive V1; (3) la cascada de cifrado (V3), que requiere programas más largos que 4
instrucciones. Gates: 52 -> 53. Rutas selladas 54 -> 60 (checker, sonda Zig, JSON y tres
capturas crudas), y dos líneas movidas por bytes propios: `tests/run_all.py`
(`e49210fa…` -> `6ba737c8…`) y `GUIA.md` (`92fc4a50…` -> `0f143886…`). Identidad del
manifiesto `a39adde9…` -> `ad581d0a…`; S1 `SEAL VERDICT: PASS` y suite completa rc 0
(2:03.79, RSS 92 276 kB; repetida 2:11.71 / 92 228 kB). `src/` intacto. Ledger entrada 39.
