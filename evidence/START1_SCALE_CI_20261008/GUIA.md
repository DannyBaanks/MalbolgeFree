```bash
python3 evidence/START1_SCALE_CI_20261008/verify_start1.py /ruta/al/artifact
```

Verifica el barrido sin volver a ejecutar miles de millones de pasos.
Regla de oro: todo este barrido arranca en1 con ASCII fuera del rango0..2;
no llamarlo máquina cerrada de1 trit, ni reducción de una máquina anterior.

Validación pequeña realmente ejecutada:

```bash
env ZIG_GLOBAL_CACHE_DIR=/tmp/e20-zig-global ZIG_LOCAL_CACHE_DIR=/tmp/e20-zig-local python3 evidence/START1_SCALE_CI_20261008/sweep.py --small-only --output /tmp/start1-small-validated-v2-20261008
```

Salida real:

```json
{"status": "SMALL_VALIDATION_SCOPED", "boot_width": 1, "classification": "PARAMETRIC_ASCII_OUTSIDE_BOOT_WORD", "measured_targets": [], "closed_word_machine_claim": "NOT_CLAIMED", "dynamic_shrinking": "NOT_CLAIMED", "targets_validated": [1, 2, 3, 4, 5]}
```

También se ejecutó realmente:

```bash
python3 evidence/START1_SCALE_CI_20261008/verify_start1.py /tmp/start1-small-validated-v2-20261008
```

Devolvió el mismo JSON, exit0. Verificación contra el artifact completo:
NO PROBADO todavía al crear esta guía; se actualizará tras GitHub.

| Estado | Interpretación |
|---|---|
| PARAMETRIC_1_TO_20_MEASURED_SCOPED |20 corridas frescas, cada una arranca en1; target20 cruza19 fronteras |
| SMALL_VALIDATION_SCOPED | Solo1..5 validados; no se afirma el barrido completo |
| BLOCKED_RESOURCE_GATE | El siguiente target no se lanzó por recursos |
| PARAMETRIC_ASCII_OUTSIDE_BOOT_WORD | Fuente aceptada por el loader pero sus valores exceden0..2 |
| NOT_DEMONSTRATED + error | Revisar logs; no inferir éxito del silencio |

Workflow: `Parametric boot1 scale`. Su push está limitado a la rama del
experimento; el disparador manual necesita registro en la rama por defecto.
No mezclar su CSV con el barrido anterior desde10 sin conservar boot_width.
AUDIT agrega violaciones por ancho activo en1..5. No hay traza gigante.
EOF es un sentinel deliberado; no se cuenta como celda ordinaria fuera de rango.
Salida debe ser NUEVA. RAM y tiempo pequeños incluyen coste de lanzamiento;
no son una medida precisa de la velocidad de dos instrucciones.
