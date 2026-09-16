# Plan

## Estado

BLOCKED - el plan tecnico esta listo, pero coder no debe editar aun `C:/Development/ISyCo Git/malbolge-free`. Es un repositorio hermano con un working tree ampliamente modificado. La ejecucion requiere aprobacion Maintainer para la excepcion cross-repo y ownership acordado de los cambios existentes.

Condicion de desbloqueo: aprobacion registrada en Bridge, lease sobre el repo destino y baseline que permita distinguir trabajo previo de trabajo nuevo sin descartar nada.

## Objetivo

Llevar `malbolge-free` a un umbral honesto y verificable para llamarlo "Malbolge verdadero" mediante dos perfiles separados:

1. **Classic estricto**: compatible con Malbolge Classic en loader, ocho opcodes, memoria, EOF, estado y automodificacion.
2. **Free puro**: generaliza ancho y direcciones, pero ejecuta solo los ocho opcodes originales y conserva automodificacion.

La ISA BF auxiliar actual se conserva como `free-assisted`, sin usarla como prueba principal de autenticidad. M7 y self-hosting no son requisitos de cierre.

## Evidencia inspeccionada

- `C:/Development/ISyCo Git/malbolge-free/src/malbolge_free.zig:1-19`: un core parametrico; Classic usa ancho 10, memoria `3^10` y `fixed`; Free usa memoria sin wrap y widening epochal.
- `src/malbolge_free.zig:35-65`: `crazy`, `rotate` y `pow3` actuales.
- `src/malbolge_free.zig:157-168`: el loader filtra whitespace, rango imprimible y longitud minima, pero no valida `(char + source_position) % 94` contra los ocho opcodes permitidos en fuente.
- `src/malbolge_free.zig:293-359`: ciclo y ocho operaciones Classic.
- `src/malbolge_free.zig:360-431`: opcodes auxiliares 69-79 para saltos, aritmetica byte y cinta BF.
- `src/malbolge_free.zig:393-403,436-449`: `TAPE_BASE` inicializa 256 celdas y activa `lock_noencrypt`, deshabilitando automodificacion en el substrato asistido.
- `tests/t_negative.zig:1-15`: solo prueba fuente no imprimible y programa menor de dos celdas; falta fuente imprimible invalida por posicion.
- `src/bfir1_backend.zig:125-264`: BFIR1 emite instrucciones auxiliares; es backend asistido, no ocho-op puro.
- `docs/MALBOLGE_BACKEND_ABI.md:76-160`: M6.2-M6.5 demostrados; M7 sigue `NOT_DEMONSTRATED`.
- `docs/CLASSIC_SEMANTICS.md:7-57`: contrato local de memoria, instrucciones y automodificacion Classic.
- Fuente externa consultada: `https://esolangs.org/wiki/Malbolge`, seccion `Memory initialization`: en fuente solo se permiten instrucciones validas y whitespace; NOPs arbitrarios pueden aparecer durante runtime, no en fuente.
- Comando ejecutado 2026-09-12: `py evidence/compare_f4.py` -> `all_match=true`, 6/6 iguales en estado, pasos y SHA-256 de stdout.
- Comando ejecutado 2026-09-12: `py tests/run_all.py` -> `M2/M4/M5/M6-infra verdict: PASS`; 31 gates pasaron, incluidos widening `10 -> 11 -> 12` y M6.5.
- SHA-256 observado: `src/malbolge_free.zig` = `d6b314aa6a0a8adcecd68a1d0a0dc109c180686d5bab778e23fe6e1545250caa`.
- SHA-256 observado: `tests/run_all.py` = `ec299b0deded5d485b2f2743d9996ef20cac4327c30a200f39d2a2061d604f0e`.
- SHA-256 observado: `m7/compiler.bf` = `39a556d91e6809b06ae40179fd3f5a8adca7dd9b866373ae6de972e55c94a30f`.
- Working tree observado: mas de veinte archivos modificados y mas de treinta no rastreados, incluidos runtime, docs, evidencia, M6/M7 y tests.
- Drift confirmado: `README.md:127-145` y `docs/HONESTY_LEDGER.md:31` aun dicen 4/6 aunque `src/malbolge_free.zig:353-355` usa modulo y F4 da 6/6; `docs/SPEC_V1.md:123` aun dice que `11 -> 12` no esta demostrado.
- `evidence/compare_f4.py` reescribe `evidence/f4_classic_parity.json`; no debe reutilizarse esa ruta para nuevas campanas canonicas.

## Alcance

- Separar explicitamente ISA Classic/pura e ISA asistida 69-79.
- Endurecer el loader Classic con validacion de opcode por posicion.
- Ampliar controles negativos y diferenciales de Classic.
- Conservar M6/BFIR1 bajo un perfil `free-assisted` explicito.
- Crear `free-pure`: widening/memoria Free, ocho opcodes originales y automodificacion activa.
- Demostrar un vertical slice Free puro con input, mutacion ternaria, control dependiente de estado y output.
- Reconciliar especificacion, README, honesty ledger, release readiness y guia humana.
- Guardar evidencia en rutas unicas con SHA-256.

## No objetivos

- No completar M7, ampliar la cinta BF ni exigir quine/self-hosting.
- No eliminar 69-79 ni romper M6; se reclasifican como `free-assisted`.
- No afirmar una nueva prueba de Turing completeness.
- No prometer ancho infinito; el dominio sigue limitado por `u128` y `w <= 80`.
- No importar, enlazar ni depender fisicamente de otro repo. Una referencia copiada exige procedencia/licencia y se vuelve codigo propio.
- No reescribir evidencia historica.
- No commit, tag, release o push sin una solicitud posterior explicita.

## Milestones

### M0 - Autorizar repo hermano y congelar baseline

**Objetivo:** evitar pisar trabajo concurrente o violar limites entre repos.

**Rutas previstas:**
- `C:/Development/ISyCo Git/malbolge-free/` (inspeccion, sin editar antes de aprobacion).
- `C:/Development/ISyCo Git/malbolge-free/AGENTS.md` (confirmar si sigue ausente).
- Bridge: topic de implementacion y PR Maintainer cross-repo.

**Pasos:**
1. Obtener aprobacion Maintainer explicita para coder y este alcance.
2. Hacer handshake y claim con la ruta destino.
3. Capturar `git status --short`, `git diff --stat`, `git diff` y `git log --oneline -10`.
4. Identificar ownership de cambios previos; prohibido reset, clean, stash o checkout destructivo.
5. Registrar hashes baseline de los archivos que tocaran M1-M5.

**Criterio de aceptacion:** aprobacion y ownership registrados; baseline reproducible; ningun cambio previo descartado.

**Comando de prueba:** `git status --short; git diff --stat; git log --oneline -10`

**Rollback:** liberar lease y detenerse. M0 no modifica producto; sin aprobacion, el plan sigue `BLOCKED`.

### M1 - Congelar Classic estricto

**Objetivo:** aceptar y ejecutar exactamente fuente Classic sin habilitar la ISA auxiliar.

**Rutas previstas:**
- `src/malbolge_free.zig`
- `tests/t_negative.zig`
- nuevo test Classic bajo `tests/`
- `tests/run_all.py`

**Pasos:**
1. Introducir una politica de instruction set/perfil; Classic reconoce solo `{4,5,23,39,40,62,68,81}`.
2. En `load()`, validar cada caracter no-whitespace con `(char + source_position) % 94`.
3. Contar posiciones despues de quitar whitespace, igual que el layout cargado.
4. Probar fuente imprimible invalida por posicion, whitespace intercalado, opcode desplazado y opcodes validos en varias posiciones.
5. En Classic, tratar 69-79 como NOP runtime y nunca activar comportamiento asistido.
6. Verificar que la celda ejecutada se cifra tras cada paso no-halt.

**Criterio de aceptacion:** invalidos posicionales rechazados; corpus Classic aceptado; solo ocho opcodes; automodificacion activa; F4 permanece 6/6.

**Comando de prueba:** `zig test --dep malbolge_free=malbolge_free -Mroot=tests/t_negative.zig -Mmalbolge_free=src/malbolge_free.zig; py evidence/compare_f4.py`

**Rollback:** revertir solo politica, loader y tests de M1; conservar ISA asistida y evidencia historica. Un fallo queda documentado, no maquillado.

### M2 - Conformidad diferencial Classic por trazas

**Objetivo:** comparar estado interno, errores y automodificacion, no solo stdout/hash/pasos de seis fixtures.

**Rutas previstas:**
- `evidence/compare_f4.py`
- `evidence/run_f4.zig`
- `corpus/classic/`
- `tests/f4_classic.zig`
- `tests/f4_corpus.zig`
- nuevos runner/fixtures bajo `tests/` o `evidence/`
- nueva campana fechada bajo `evidence/`

**Pasos:**
1. Hacer el checker read-only por defecto; escribir solo con ruta de salida nueva explicita.
2. Cubrir cada opcode, input/EOF, jumps, automodificacion, programas largos y max steps.
3. Cubrir invalidos posicionales y error antes de ejecucion.
4. Comparar checkpoints de `a`, `c`, `d`, celda antes/despues de cifrado, writes, stdout, pasos y terminacion.
5. Crear un oraculo independiente dentro del repo desde la especificacion. Antes de copiar referencia externa, pedir procedencia/licencia a librarian.
6. Guardar ambiente, comando, output crudo, exit code y hashes en una ruta unica.

**Criterio de aceptacion:** validos coinciden en trazas; invalidos coinciden en error; checker normal no escribe; campana hasheada y no sobrescrita.

**Comando de prueba:** `zig test --dep malbolge_free=malbolge_free -Mroot=tests/f4_classic.zig -Mmalbolge_free=src/malbolge_free.zig; zig test --dep malbolge_free=malbolge_free -Mroot=tests/f4_corpus.zig -Mmalbolge_free=src/malbolge_free.zig`

**Rollback:** retirar solo fixtures/oraculo nuevos no confiables; preservar resultados negativos en una campana fechada.

### M3 - Separar `free-pure` y `free-assisted`

**Objetivo:** impedir que BF asistido se confunda con Malbolge ocho-op.

**Rutas previstas:**
- `src/malbolge_free.zig`
- `src/hell.zig`
- `src/bfir1_backend.zig`
- tests M6 existentes bajo `tests/t_m6*.zig`, `tests/t_m62*.zig`, `tests/t_m63_input.zig`, `tests/t_m64_branch.zig`, `tests/t_m65_differential.zig`
- nuevos tests de perfiles bajo `tests/`

**Pasos:**
1. Definir perfiles explicitos `classic`, `free_pure` y `free_assisted` segun estilo Zig.
2. En `classic/free_pure`, 69-79 son NOP y el cifrado siempre permanece activo.
3. En `free_assisted`, conservar exactamente 69-79 y `TAPE_BASE -> lock_noencrypt`.
4. Hacer que BFIR1 solicite `free_assisted`; nunca depender del default.
5. Instrumentar tests con contador de opcodes asistidos y transiciones de `lock_noencrypt`.
6. Ejecutar suite completa y confirmar que Classic y M6 no cambian.

**Criterio de aceptacion:** perfil explicito; `classic/free_pure` ejecutan cero 69-79 y mantienen cifrado; `free_assisted` conserva M6.2-M6.5; default no habilita ISA BF.

**Comando de prueba:** `py tests/run_all.py`

**Rollback:** restaurar dispatch previo sin eliminar tests de caracterizacion; no eliminar 69-79 ni cambiar BFIR1.

### M4 - Demostrar vertical slice Free puro

**Objetivo:** demostrar computacion no trivial mediante semantica Malbolge, no mediante ISA BF.

**Rutas previstas:**
- nuevo fixture bajo `corpus/` o `tests/fixtures/`, segun estructura confirmada en M0
- nuevo `tests/t_free_pure_vertical_slice.zig`
- `src/hell.zig` solo si necesita emitir comandos Classic ya soportados
- nueva evidencia fechada bajo `evidence/`

**Pasos:**
1. Usar `ubO` como control I/O, no como prueba suficiente.
2. Construir fixture stateful: input, mutacion con `ROT/OPR`, control dependiente de estado y output.
3. Ejecutarlo en `free_pure` con decode posicional y automodificacion.
4. Control negativo: intentar 69-79 y verificar NOP.
5. Exigir `assisted_opcode_count == 0`, `lock_noencrypt == false`, una celda cifrada, una mutacion ternaria y dos inputs con trazas distintas.
6. Comparar el prefijo `free_pure(width=10, antes de frontera)` con Classic y agregar un caso acotado que cruce una frontera sin ISA auxiliar.
7. Si sintetizar el witness requiere busqueda/hipotesis, hacer handoff a researcher; coder conserva harness y criterios, no inventa resultados.

**Criterio de aceptacion:** fixture reproducible; estado/output esperado; cero auxiliares; automodificacion observada; prefijo igual a Classic; widening no reescribe historia. Solo entonces `FREE_PURE_VERTICAL_SLICE=DEMONSTRATED`.

**Comando de prueba:** `zig test --dep malbolge_free=malbolge_free -Mroot=tests/t_free_pure_vertical_slice.zig -Mmalbolge_free=src/malbolge_free.zig`

**Rollback:** retirar el fixture del gate si no cumple todos los contadores y conservar salida como `NOT_DEMONSTRATED`; no sustituirlo por programa asistido.

### M5 - Reconciliar claims, guia y release gate

**Objetivo:** alinear toda documentacion con perfiles y evidencia actuales.

**Rutas previstas:**
- `README.md`
- `RELEASE_READINESS.md`
- `docs/SPEC_V1.md`
- `docs/FREE_SEMANTICS.md`
- `docs/CLASSIC_SEMANTICS.md`
- `docs/HONESTY_LEDGER.md`
- `docs/MALBOLGE_BACKEND_ABI.md`
- `docs/UROBOROS.md`
- `GUIA.md`

**Pasos:**
1. Corregir drift 4/6 a 6/6 y `11 -> 12 NOT_DEMONSTRATED` al estado real, preservando el bug como historico.
2. Documentar tres perfiles y que M6 usa `free-assisted`.
3. Definir autenticidad con `CLASSIC_STRICT_CONFORMANCE` y `FREE_PURE_VERTICAL_SLICE`, no con porcentaje sin gates.
4. Mantener M7 opcional y `NOT_DEMONSTRATED` mientras corresponda.
5. Crear `GUIA.md` en espanol: comando principal primero, regla de oro, comandos ejecutados con output real, tabla de estados y trampas.
6. Ejecutar suite desde baseline conocido y producir evidencia fechada con hashes.

**Criterio de aceptacion:** ningun doc llama ocho-op puro a `free-assisted`; claims CURRENT coinciden con comandos; guia solo usa comandos probados o `NO PROBADO`; suite PASS; evidencia nueva no sobrescrita.

**Comando de prueba:** `py tests/run_all.py; git diff --check; git status --short`

**Rollback:** restaurar solo docs/guia de M5 si contradicen evidencia; conservar perfiles, tests y resultados negativos.

## Dependencias

- M0 bloquea todo trabajo en el repo hermano.
- M1 depende de M0 y fija el contrato medido por M2.
- M2 depende de M1; copiar una referencia externa depende de librarian.
- M3 depende de M1 y usa M6 como control de no regresion.
- M4 depende de M3; la sintesis experimental de witness, si fuera necesaria, depende de researcher.
- M5 depende de M1-M4 y solo eleva claims despues de ejecutar gates.
- Release/tag posterior depende de M5, pero queda fuera de alcance.

## Riesgos

- **Bloqueo alto - working tree ajeno:** muchos cambios no committeados. Mitigacion: M0; prohibido reset/stash/clean/checkout destructivo.
- **Bloqueo alto - cross-repo:** la solicitud de plan no sustituye aprobacion Maintainer para editar el hermano.
- **Alto - pure nominal:** renombrar sin bloquear 69-79 seria maquillaje. Mitigacion: contadores y control negativo.
- **Alto - romper M6:** bloquear auxiliares globalmente destruye backend demostrado. Mitigacion: `free_assisted` explicito y 31 gates.
- **Alto - falso oraculo:** comparar el core consigo mismo da falso PASS. Mitigacion: implementacion separada y trazas.
- **Medio - loader vs runtime NOP:** fuente permite solo instrucciones validas; runtime puede producir otros NOP. Mitigacion: tests separados.
- **Medio - dependencia externa:** checker actual apunta a otro repo. Mitigacion: eliminar dependencia de release; copiar solo con procedencia/licencia.
- **Medio - evidencia sobrescrita:** checker reutiliza JSON. Mitigacion: read-only default y rutas unicas.
- **Medio - docs obsoletos:** README, ledger y SPEC divergen. Mitigacion: M5.
- **Bajo - M7 distrae:** self-hosting no mejora conformidad. Mitigacion: fuera del gate principal.

### Preguntas abiertas

- Nombre publico final de perfiles; recomendado: `classic`, `free-pure`, `free-assisted`.
- Alcance del vertical slice: recomendado witness stateful primero; backend BF ocho-op completo despues.
- Procedencia/licencia de referencia externa: si no es copiable, implementar oraculo desde especificacion con handoff librarian.

## Rollback global

Conservar patch/hash del baseline antes de M1. Revertir solo hunks de este plan en orden M5 a M1, sin tocar cambios previos. El minimo seguro deja runtime actual, 69-79 y M6 intactos, los 31 gates en estado basal y evidencia negativa preservada. Si no se puede distinguir trabajo previo de nuevo, detenerse y escalar; nunca usar reset, clean, checkout masivo ni borrado.

## HANDOFF TO CODER

Primer paso inequivoco: **no editar producto aun**. Ejecutar M0 en `C:/Development/ISyCo Git/malbolge-free`: obtener aprobacion Maintainer cross-repo, reclamar lease con esa ruta, capturar `git status/diff/log`, identificar ownership y publicar baseline en Bridge. Solo despues comenzar M1: agregar primero un test de fuente imprimible pero posicionalmente invalida, verlo fallar contra el loader actual y recien entonces cambiar `src/malbolge_free.zig`.
