```bash
python3 evidence/E20_CI_20261008/verify_ci.py /ruta/al/artifact
```

Ese comando verifica el resultado descargado de GitHub. Ejecutado realmente:

```bash
python3 evidence/E20_CI_20261008/verify_ci.py /tmp/e20-github-artifacts-37847283479/e20-37847283479-1
```

Salida real:

```json
{"EPOCHAL_19_TO_20": "DEMONSTRATED_SCOPED", "UNBOUNDED_WIDTH_GROWTH": "NOT_DEMONSTRATED", "MALBOLGE20_IDENTICAL_TO_FREE_EPOCHAL": "NOT_CLAIMED"}
```

Corrida: https://github.com/DannyBaanks/MalbolgeFree/actions/runs/37847283479
La evidencia descargada también está preservada en `evidence/E20_GITHUB_RUN_20261008/`.

Regla de oro: no iniciar E20 si el gate dice NO_GO. No confundir una
salida exitosa del job con haber demostrado E20: leer `verdict.json`.

Validación local realmente ejecutada desde la raíz:

```bash
env ZIG_GLOBAL_CACHE_DIR=/tmp/e20-zig-global ZIG_LOCAL_CACHE_DIR=/tmp/e20-zig-local python3 evidence/E20_CI_20261008/run_ci.py --small-only --output /tmp/e20-ci-small-validated-v2
```

Salida real:

```json
{"EPOCHAL_19_TO_20": "NOT_DEMONSTRATED", "UNBOUNDED_WIDTH_GROWTH": "NOT_DEMONSTRATED", "MALBOLGE20_IDENTICAL_TO_FREE_EPOCHAL": "NOT_CLAIMED", "note": "Local bounded validation only; E20 not attempted."}
```

| Estado | Significado / acción |
|---|---|
| DEMONSTRATED_SCOPED | VM real llegó de 10 a 20; conservar artifact y hashes |
| BLOCKED_RESOURCE_GATE | Recursos insuficientes; no se lanzó E20 |
| NOT_DEMONSTRATED + error | Fallo de harness, timeout o ejecución; revisar logs |
| Job verde | También puede significar bloqueo de recursos; leer veredicto |

El workflow se llama `E20 controlled research`. El push a la rama de este
experimento lo dispara cuando cambian su workflow o harness. También declara
workflow_dispatch; GitHub exige que un workflow exista en la rama por defecto
para registrarlo como manual. No se cambia master para esta primera corrida.
Artifacts contienen JSON, logs y fuentes pequeñas, no binarios ni fuente >1 GB.

Trampas: usar directorio de salida NUEVO; el runner rechaza reutilizarlo.
El stock --estimate estima HASH, no DENSE. MemTotal no es MemAvailable.
No todos los pasos cifran: el runtime solo cifra valores ASCII 33..126.
