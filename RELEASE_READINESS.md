# Malbolge Free — Release Readiness Checklist

**Status**: RELEASE CANDIDATE 2026-10-02 — harness 47+/47 local, CI verde en
ubuntu+windows; C8 ladder medido hasta `w=19`; paridad Python↔Zig en epochal;
CLI de producto con `run`/`inspect`/`trace`. Limitaciones explicitas abajo.
M6 (TC) y Uroboros siguen NOT_DEMONSTRATED y NO se presentan como capacidades.

**Corrección 2026-10-17 (anexa)**: la fila "Classic Parity (6/6 corpus)" de abajo
es HISTÓRICA. El 2026-10-17 una auditoría externa midió que nuestro EOF no era
canónico; ese oráculo (`engine.zig`) compartía la convención errónea y por eso dio
6/6. Estado actual: **22 veredictos / 44 comparaciones de hash** contra los
intérpretes canónicos (`evidence/f4c_canonical_parity_20261017.json`; re-medido con
el oráculo vendorizado en `evidence/f4c_canonical_parity_vendored_20261017.json`),
4/6 con el oráculo viejo (`evidence/f4_engine_zig_divergence_20261017.json`),
harness 49/49. El oráculo canónico de Python está vendorizado y fijado por SHA-256
(`vendor/canonical_malbolge_py/`), así que CI mide la paridad en vez de saltarla — y
tardó dos runs en conseguirla: el primero falló porque el runner re-end-lineaba el
oráculo (el pin lo detectó, exit 4; `.gitattributes`), y en el segundo F4c dio MISMATCH
por un `\r` que el manifest del gate metía como byte de entrada en el núcleo Zig —
defecto del arnés, no de Classic. Ver entradas 26 y 27,
`evidence/F4C_WINDOWS_EOL_DRIFT_20261018.json` y
`evidence/F4C_WINDOWS_MANIFEST_CRLF_20261018.json`. Con ambos arreglos, el run
`39108877995` (`cc6d26d`) quedó **verde en ubuntu y en windows** con F4c midiendo 20
comparaciones y 49 PASS / 0 SKIP en cada runner (entrada 28). Ver
`docs/HONESTY_LEDGER.md` entrada 24.

---

## ✅ COMPLETE (as of 2026-09-09)

| Item | Evidence |
|---|---|
| **Classic Parity (6/6 corpus)** | `evidence/f4_classic_parity.json` — all match |
| **Frontier Widening 10→11** | `tests/t_frontier_moment.zig` — WIDEN at step 59050 |
| **3^19 Crossing (k=20)** | `evidence/f7_witness.zig` — d = 1,743,392,210 > 3^19 |
| **Epochal Invariants** | `tests/t_epochal.zig` — 2/2 tests pass |
| **Lazy == Eager Fill** | `tests/t_phase23.py` — bit-for-bit at k=10 (59049 cells) |
| **Width-Extension Brokenness** | `evidence/f8_check.py` — rotate 33.3%, crazy 100% |
| **Zero Python in Zig Toolchain** | `Malbolge-Translator/zig/parity_check.exe` is Zig reference |

---

## ✅ COMPLETED SINCE V1.0

### C8: REPEATED_WIDTH_WIDENING (11→12)
- **PASS**: `evidence/f9_repeated_frontier.json`
- Witness: 190,000 bytes, SHA-256 `3370003cfa18b02e21f095173328d1fa758722dae6e280e78413e3903013a57`
- Events: step 59,050 (`10→11`) and step 177,148 (`11→12`)

---

## 📋 OPTIONAL POLISH (not blocking)

| Item | Notes |
|---|---|
| Version tag / CHANGELOG | v1.0.0 |
| GitHub release with binaries | `malbolge-free.exe` (Zig core), `parity_check.exe` (ref) |
| docs/HONESTY_LEDGER.md sync | Already current |
| CI badge | Optional |

---

## QUICK VERIFY ALL GATES

```bash
# 1. Classic parity (Zig vs Zig)
cd malbolge-free && py evidence/compare_f4.py
# => PASS

# 2. Frontier 10→11
zig run tests/t_frontier_moment.zig
# => WIDEN step=59050 ... final padwidth=11

# 3. 3^19 crossing
zig run evidence/f7_witness.zig
# => max_addr=1743392210 >3^19=true

# 4. Epochal invariants
zig test tests/t_epochal.zig
# => All 2 tests passed

# 5. Lazy/eager parity
py tests/t_phase23.py
# => k=10: lazy == Classic eager loader (59049 cells bit-for-bit)  OK

# 6. Width-extension evidence
py evidence/f8_check.py
# => crazy same=729/729 (100.0%)   rotate same=9/27 (33.3%)
```

---

## ARCHITECTURE SNAPSHOT

```
malbolge-free/
├── src/
│   ├── malbolge_core.py          # Python reference core (parametric, lazy fill)
│   └── malbolge_free.zig         # Zig core (u128, epochal/fixed/pad_to_padwidth)
├── evidence/
│   ├── f4_classic_parity.json    # 6/6 corpus SHA256 matches
│   ├── compare_f4.py             # Runner: Zig ref vs Zig core
│   ├── f7_witness.zig            # 3^19 crossing
│   └── f8_check.py               # Width-extension consistency
├── tests/
│   ├── t_frontier_moment.zig     # 10→11 widening demo
│   ├── t_epochal.zig             # Invariants
│   ├── t_phase23.py              # Lazy/eager + Classic loader parity
│   └── frontier_witness.txt      # 190k program (crosses 10→11→12)
└── Malbolge-Translator/zig/      # External Zig reference (generator, PCA, epoch, etc.)
    └── parity_check.exe          # 6/6 corpus JSON oracle
```

---

## DECISION POINT

**If C8 is not a release requirement**: Tag v1.0 now. The machine is:
- Classic-compatible (6/6)
- Frontier-widening demonstrated (10→11)
- Unbounded memory with epochal policy working
- All evidence hashed and reproducible

**If C8 is required**: Generate 180k+ witness, verify 11→12, then tag.

---

*Generated 2026-09-09 — ^w^*

---

## Anexo 2026-10-18 — F10 (evidence, not a gate; nothing above is rewritten)

`evidence/f10_quine_epochal_20261018.json` runs Lutter's Classic quine (third-party,
hash-pinned, **not** vendored) through `classic`, `pure_fixed` and `epochal` on this
machine. Readiness effect, stated narrowly:

- **Strengthens M6 step 1 / "Classic-compatible"**: under `classic` our Zig core
  reproduces the quine byte-for-byte — `HALTED`, 69 547 437 steps, stdout sha256 equal
  to the input program's. The DECISION POINT above said "Classic-compatible (6/6)";
  that row is HISTÓRICA, and the current evidence is F4c (22 verdicts / 44 hash
  comparisons locally, 20 comparisons per CI runner) **plus** this 69M-step program.
  Ledger entries 24–28 and 29.
- **Constrains how "unbounded" may be advertised**: `pure_fixed` — no growth policy at
  all, only the address wrap removed — halts at 6 521 steps emitting 1 byte, and
  `epochal` halts at 8 761 emitting nothing. So no release text may claim that a
  `mem_limit = null` profile runs Classic programs unchanged; the wrap is part of the
  definition, measured. `epochal` widening is not the cause, which is exactly what the
  `pure_fixed` control proves.
- **No effect on the gate count**: `compare_quine_epochal.py` is deliberately outside
  `tests/run_all.py`'s `GATES`, so `49 PASS / 0 SKIP` stays as published. The quine is
  not vendored, so on a fresh clone the script exits 3 (`NOT_DEMONSTRATED`) rather than
  substituting an input. Details: `docs/HONESTY_LEDGER.md` entry 29,
  `evidence/F10_QUINE_EPOCHAL_20261018.hashes.json`.

---

## Anexo 2026-10-18 (segundo) — S1: el sello pasa a ser gate; el recuento pasa de 49 a 50

Hasta hoy `SHA256SUMS.txt` solo lo comprobaba a mano quien sellaba. CI podía publicar
bytes que ya no coincidían con sus hashes y seguir dando verde. Nuevo gate
`S1 seal manifest (SHA256SUMS.txt)` → `evidence/verify_seal_manifest.py`: re-hashing de
cada ruta listada con `hashlib` (Python puro: los runners de Windows no tienen
`sha256sum`), exit **4** si algo deriva, falta, está mal formado, está duplicado o escapa
del repositorio. No hay rama de exit 3 a propósito: no hay entrada externa que pueda
faltar, así que un clon **o tiene su sello o falla**.

- Medido localmente: `50 PASS / 0 FAIL / 0 SKIP`, `entries=35 checked=35 ok=35`,
  `manifest_sha256=9140d359…`, harness rc=0.
- Ramas de fallo medidas en una copia aparte del repo (no en el árbol sellado): byte
  añadido a un fichero sellado → `SEAL_DRIFT` rc 4; fichero sellado borrado →
  `SEAL_MISSING` rc 4; línea truncada → `SEAL_MALFORMED_LINE` rc 4; ruta `../` →
  `SEAL_PATH_ESCAPE` rc 4; ruta listada dos veces → `SEAL_DUPLICATE` rc 4; manifiesto
  ausente → `SEAL_MANIFEST_ABSENT` rc 4. Convertir un fichero sellado a CRLF — la clase
  exacta de defecto que la entrada 26 cazó en el oráculo vendorizado — también da
  `SEAL_DRIFT` rc 4.
- **Primera ejecución real del gate cazó un sello obsoleto de verdad**: `tests/run_all.py`,
  por editarlo para añadir el propio gate. Eso es el working, no un falso positivo.
- Consecuencia para el release: las cifras de 49 arriba (`harness 49/49`,
  `49 PASS / 0 SKIP`) son HISTÓRICAS hasta `be39798`. La lista de gates actual son 50, y
  la afirmación de paridad canónica (entrada 28) no cambia: sigue siendo 10 casos × 2
  cores × 1 oráculo vendorizado = 20 comparaciones por runner.
- No se tocó `src/`; ningún artefacto ya publicado se reescribió. El manifiesto actualiza
  la línea de `tests/run_all.py` in situ y anexa la del verifier, con el hash sustituido
  declarado en el bloque fechado (entrada 30 del ledger).

## Anexo 2026-10-18 (2) — las capturas crudas de F10 entran en el sellado

El gate S1 pasó de 35 a **40 rutas** y el harness sigue `50 PASS / 0 FAIL / 0 SKIP` con
rc 0, medido tras anexar: `SEAL manifest_sha256=d45319d1fed042d39fa660c7137d03c6166975a2c6570c7ce1659ecd8c437e4e entries=40 checked=40 ok=40 drift=0 missing=0 escaping=0 duplicate=0 malformed=0`.
`sha256sum -c --quiet SHA256SUMS.txt` da rc 0 con la implementación de GNU, aparte del
verifier propio. La identidad citada en el anexo anterior (`9140d359…`) corresponde al
manifiesto tal como estaba en `8b97437`; desde este anexo S1 imprime la nueva. Lo anexado
son cuatro capturas literales del run de F10 más `PROVENANCE.md`, todas bajo
`evidence/F10_QUINE_EPOCHAL_20261018/`. Ledger entrada 31.

Esto **no** cambia el release readiness: sigue sin haber gate nuevo (50), no se añade
ninguna afirmación sobre el lenguaje, y el medido de F10 sigue siendo
`evidence/f10_quine_epochal_20261018.json`, intacto. Tampoco cambia el alcance de F10: su
entrada sigue siendo un quine de terceros que no se vendoriza, así que un clon limpio sin
MalDOOM sigue saliendo con 3 (`NOT_DEMONSTRATED, missing external input`). Lo que gana el
repo es que las mediciones negativas —los dos trials acotados con sus expectativas
FALSIFIED— dejan de vivir solo como prosa del bloque `trial`.

**Cerrado en CI el mismo día:** empujado `8b97437..2b57e9d`, run `39118092762` `success`;
en el log de cada runner (ubuntu `117647889202`, windows `117647889354`) aparecen
`SEAL manifest_sha256=d45319d1… entries=40 checked=40 ok=40 drift=0 missing=0 escaping=0
duplicate=0 malformed=0`, `SEAL VERDICT: PASS` y `50 PASS / 0 FAIL / 0 SKIP`, con el mismo
conjunto de 50 gates en ambos. La identidad `d45319d1…` deja de ser una cifra local: un
clone limpio integrity-checka ya las 5 capturas anexadas. Esto no re-ejecuta F10 en CI
(no está en `GATES`; sin MalDOOM, exit 3) ni añade gates: la lista sigue en 50. Ledger
entrada 32.

## Anexo 2026-10-18 (3) — dos gates nuevos sobre un quine vendorizado: la lista pasa de 50 a 52

Cierre de la limitación que los anexos de F10 dejaron abierta en su mitad prospectiva:
CI no podía re-ejecutar el experimento de frontera porque la entrada vivía en otro repo.
Se resuelve trayendo un programa **propio y publicado**, no relajando el gate.

- `corpus/classic/quine_m281.mal` (`96b670b8…`, 53 562 B): copia literal (`cmp` sin
  diferencias) del registro de `DannyBaanks/Malbolge-MB-Database`, mismo blob que el
  artefacto de `DannyBaanks/BolgeForge@5a55b9b`. Licencia MIT idéntica a la de este repo;
  `* -text` en `.gitattributes` ya evita el re-endline que la entrada 26 documentó.
  Procedencia completa, incluida la reproducción con el sintetizador público
  (`python3 synthesize.py 281` → los mismos bytes), en `corpus/classic/PROVENANCE.md`.
- **F11** `evidence/compare_f11_frontier_eof.py`: frontera + EOF relativo al ancho, ambos
  cores, 15 expectativas preregistradas. Local: `MATCH=15 FALSIFIED=0`, 1,26 s.
- **F12** `evidence/compare_f12_selfreproduction.py`: halt completo de 62 239 852 pasos y
  autorreproducción byte-exacta en ambos cores, más el paso conocido de tres motores
  externos. Local: `MATCH=7 FALSIFIED=0`, 1:52.97.

Medido en este árbol tras sellar: harness **`52 PASS / 0 FAIL / 0 SKIP`**, rc 0, 2:08.21,
y en ese mismo run `SEAL manifest_sha256=298fe8008fbdd9e596c337f56f2e144be39cf0d37736e7777394bc76d31b4217
entries=53 checked=53 ok=53 drift=0 missing=0 escaping=0 duplicate=0 malformed=0`.
GNU `sha256sum -c --quiet` coincide. El manifiesto creció de 40 a 53 rutas (13 de
evidencia nueva) y `tests/run_all.py` se re-selló in situ (`e49210fa…`; sustituido
`246e9041…` declarado en el bloque fechado).

**Coste assumptiondo explícitamente:** F12 lleva timeout propio de 900 s porque el halt
real en dos cores no cabe en los 180 s del default; el harness acepta ahora un tercer
elemento opcional por gate y los otros 50 mantienen 180 s. Con 2:08 locales y los
runners de CI en ~3', el margen contra `timeout-minutes: 30` es amplio, pero la
cifra de CI se afirma solo tras leer el log de cada runner, no del verde global.

**Lo que esto sí cambia para el release:** la afirmación de frontera y de
autorreproducción byte-exacta pasa de «medido en una máquina» a «re-ejecutable por
cualquiera desde un clon limpio, con el programa dentro del repo y sellado». Los gates
nuevos no tienen rama de exit 3 por construcción.

**Lo que no cambia:** F10 sigue fuera de `GATES` y sigue saliendo con 3 sin el quine de
Lutter; sus bytes sellados están intactos y las entradas 29 y 32 se leen como se
midieron. No se publica release, no se empuja nada sin pedido expreso, `src/` no se tocó
(ambos cores conservan los sellos de la entrada 24) y docs/ledger siguen sin estar
sellados, por lo que redactar este anexo no puede mover la identidad del manifiesto.
Nada de esto asciende una etiqueta de claim: `epochal` no reproduce el quine aquí ni en
F10 (3 bytes / 0 bytes), y la afirmación de compatibilidad con Classic queda acotada por
dos incompatibilidades medidas, no por una. Ledger entradas 33 y 34.

**CI, el mismo día (mismo push):** run `39129462270` `success`; ubuntu `117681459124`
3 m 56 s, windows `117681459098` 7 m 05 s. Cada log imprime la identidad sellada
`298fe800…` con `entries=53 checked=53 ok=53 drift=0 missing=0 escaping=0 duplicate=0
malformed=0`, `SEAL VERDICT: PASS`, `52 PASS / 0 FAIL / 0 SKIP` y el mismo conjunto de 52
nombres de gate en ambas plataformas. Los gates nuevos no dependen de nada externo y no
faltaron: `F11 EXPECTATIONS=15 MATCH=15 FALSIFIED=0`, `F12 EXPECTATIONS=7 MATCH=7
FALSIFIED=0`, con los mismos pasos, sha y bytes de stdout que el run local sellado. El
tipo de defecto de la entrada 26 (re-endline en Windows) se prueba ahora contra el corpus
nuevo: si `quine_m281.mal` hubiera llegado con CRLF, F11 y F12 habrían salido con 4 en vez
de medir. Timings: F12 ~3 min en CI contra sus 900 s de timeout — con el default de 180 s
no habría pasado. Queda igual: F10 sigue sin re-ejecutarse en CI (fuera de `GATES`, exit 3
sin el quine de Lutter). No hay release, tag ni PR; `src/` intacto. Ledger entrada 35.

**Anexo 2026-10-18 (4) — un cambio de documentación que sí movió el sello.** El contrato
operativo en español (`GUIA.md`) se auditó contra lo que medimos en F11 y le faltaba el
aviso: bajo `--growth epochal` el valor que `in` asigna al acabarse la entrada es
`3^padwidth - 1` y cambia en el ensanche, así que un test de EOF de Classic (`59048`) deja
de significar «fin de entrada». Se añadió la sección con dos comandos medidos localmente
(epochal `--width 3`: 80 / 242 / 728 en los pasos 68 / 82 / 256, termina `padwidth=6`;
control `--growth fixed`: 72 eventos en `26`, termina `padwidth=3`; ambos exit 2) y una
viñeta en *Trampas*. Como `GUIA.md` está sellado —a diferencia de README/ROADMAP/CHANGELOG/ledger—,
la corrección es evento de integridad: identidad `298fe800…` -> `a39adde9…`, rutas 53 -> 54
por sellar además `tests/frontier_witness.txt` (`3370003c…`, bytes intactos), que hasta ahora
solo estaba fijado transitivamente por cinco `@embedFile`. S1: `entries=54 ok=54 drift=0
missing=0 escaping=0 duplicate=0 malformed=0`, `SEAL VERDICT: PASS`, rc 0; `sha256sum -c
--quiet` coincide. Harness: `52 PASS / 0 FAIL / 0 SKIP`, rc 0. Ningún gate nuevo, ningún
claim ascendido, `src/` intacto (los dos cores conservan los sellos de la entrada 24), sin
release ni tag ni PR. Ledger entrada 36.

**CI de la entrada 36, leído por runner (2026-10-18):** push `aa702f0..69b69f5`, run
`39144966132` `success`; ubuntu `117726841165` (3 m 54 s) y windows `117726841354` (4 m 19 s)
imprimen cada uno `SEAL manifest_sha256=a39adde9… entries=54 checked=54 ok=54 drift=0
missing=0 escaping=0 duplicate=0 malformed=0`, `SEAL VERDICT: PASS`, 52 líneas `PASS:` y
ninguna `FAIL`/`SKIP`, con el mismo conjunto de 52 gates y los mismos números sellados
(EOF 59 048 / 177 146; halt de 62 239 852 pasos emitiendo 53 562 bytes con el sha del
programa). Lo nuevo aquí es la ruta 54: `tests/frontier_witness.txt` entra por primera vez
en la comprobación de integridad de un clon limpio en ambas plataformas, que es lo que hace
reproducible la salida que la guía imprime. Corrección honesta sobre los tiempos: en windows
F12 bajó de `zig=65.1 python=94.8` a `zig=31.3 python=49.6` con imagen de runner
byte-idéntica (`20261007.264.1`), así que la coincidencia de los dos `python=94.8` que anotó
la entrada 35 era ruido; lo que sí se sostiene es el coste contra el timeout (los dos cores
suman 174,9 s en ubuntu frente a los 900 s de presupuesto del gate). No hay release, tag ni
PR. Ledger entrada 37.

**Anexo 2026-10-18 (5) — F13 divide `UNSHACKLED_PARITY` y sube el recuento a 53 gates.**
Para la readiness importa sobre todo la separación: la afirmación (a), paridad bit a bit con
el `Unshackled` original, sigue **NOT_DEMONSTRABLE** y ya no se puede mezclar con nada — el
`Unshackled.c:585` con `srand(time(NULL))` no es un control. La afirmación (b), acuerdo con
una máquina externa **determinista** de 3^19 fijo, pasa a **DEMONSTRATED dentro de un alcance
declarado**: `docs/F13_UNSHACKLED_K19_PREGISTRATION.md` se escribió antes de ejecutar y
`evidence/f13_unshackled_k19_20261018.json` (`00c7080d…`) cierra `F13 EXPECTATIONS=20
MATCH=20 FALSIFIED=0`, exit 0, con tres máquinas por caso (referencia, core Python, core Zig).
Dos de esas 20 expectativas afirman desacuerdo y se miden como tal: `rot` (`0x9e` nuestro
contra `0x92` de la referencia, y `P2` demuestra que el conjunto de divergencia es
exactamente `{v : v % 3 != 0}`, 133 230 de 200 000) y el contador de halt, sellado como
`ours = reference + 1` en lugar de alineado. Escalado a 19 trits, `crazy` coincide con la
tabla base-9 de la referencia en 200 000 pares con 0 discrepancias.

**Qué NO entra en una release con esto:** paridad con Lutter, completitud Turing nueva
(C10 sigue `INHERITED`), direcciones `>= 3^18`, regiones 1/2 (offsets `0, 117, 140` — V1,
leídas y sin testear), la cascada de cifrado (V3) y el loader canónico. El alcance lo imprime
el propio gate en su línea `F13 DISCLOSURE`, no solo esta prosa.

**Consecuencia operativa para CI:** la referencia no está vendorizada — decisión de licencia
de Danny, no del harness — así que un clon limpio sin `../MalbolgeLispSlop` al lado obtiene
exit 3 y el harness imprime `SKIP (NOT_DEMONSTRATED, missing external input)`. Por tanto el
`53 PASS / 0 FAIL / 0 SKIP` que F13 produce en esta máquina (rc 0, 2:03.79, RSS 92 276 kB;
repetido 2:11.71 / 92 228 kB) **no** es lo que van a imprimir los runners: allí se verá
`52 PASS / 0 FAIL / 1 SKIP`. Lo primero es honesto sobre el lenguaje, lo segundo sobre el
entorno, y ninguna de las dos se presenta como la otra.

**Evento de integridad:** seis rutas selladas nuevas (`evidence/compare_unshackled_k19.py`
`7a083791…`, `evidence/run_f13_k19.zig` `e9c6cbea…`, el JSON `00c7080d…` y las tres capturas
crudas `1e9b8f98…` / `185c84bb…` / `cd1e8003…`) y dos líneas movidas por bytes propios:
`tests/run_all.py` (`e49210fa…` -> `6ba737c8…`) y `GUIA.md` (`92fc4a50…` -> `0f143886…`,
donde la trampa `NOT_DEMONSTRATED` se parte en las dos lecturas y se añade la nota operativa
de F13; ninguna advertencia se eliminó). Identidad del manifiesto `a39adde9…` -> `ad581d0a…`,
rutas verificadas 54 -> 60, S1 `SEAL VERDICT: PASS` y `sha256sum -c --quiet` devolviendo 0 por
su cuenta. `src/`, `corpus/` y `vendor/` intactos: F13 apoyan sobre los mismos cores que
sellaron F4c, F11 y F12. Sin release, sin tag, sin PR, sin push hasta que Danny lo diga.
Ledger entrada 39.
