```bash
python3 evidence/RAM_SCALE_CI_20261008/verify_scale.py /ruta/al/artifact
```

Verifica la evidencia descargada sin repetir la corrida. Ejecutado realmente:

```bash
python3 evidence/RAM_SCALE_CI_20261008/verify_scale.py /tmp/ram-scale-artifacts-37848647590/ram-scale-37848647590-1
```

Salida real:

```json
{"status": "STOPPED_BEFORE_NEXT_ALLOCATION", "measured_widths": [14, 15, 16, 17, 18, 19, 20], "next_rung_executed": false, "next_width": 21, "reasons": ["PREDICTED_PEAK_ABOVE_BUDGET", "CURRENT_STORAGE_MIN_ABOVE_BUDGET", "DENSE_U32_WIDTH_CEILING"], "scope": "Finite linear ladder witness, single Zig implementation. No global RAM-to-language-width theorem."}
```

Corrida: https://github.com/DannyBaanks/MalbolgeFree/actions/runs/37848647590
Evidencia y tabla: `evidence/RAM_SCALE_RUN_20261008/04_VERDICT.md`.

Regla de oro: NO_GO detiene el siguiente peldaño antes de asignar memoria;
no intentar consumir toda la RAM ni interpretar las proyecciones como PASS.

Pruebas realmente ejecutadas:

```bash
python3 -m unittest discover -s evidence/RAM_SCALE_CI_20261008 -p 'test_*.py' -v
```

Salida real final:

```text
Ran 7 tests in 0.003s

OK
```

Workflow: `Epochal RAM scale`, Ubuntu24.04. El push de cambios del harness
en la rama del experimento lo dispara. Declara también workflow_dispatch;
GitHub lo registra como manual solo cuando exista en la rama por defecto.
Se guardan artifacts durante90 días y después también en Git.

| Resultado | Cómo leerlo |
|---|---|
| STOPPED_BEFORE_NEXT_ALLOCATION | Barrido terminó con parada preventiva; ver razones y runs.json |
| DENSE_U32_WIDTH_CEILING | Implementación densa actual termina en20; no es prueba de imposibilidad del lenguaje |
| CURRENT_STORAGE_MIN_ABOVE_BUDGET | La representación actual supera el presupuesto para ese witness |
| PREDICTED_PEAK_ABOVE_BUDGET | Estimación con margen no cabe; no se ejecutó |
| NOT_DEMONSTRATED + error | Fallo/timeout; conservar logs, no declarar éxito |
| PROJECTION_ONLY_NOT_A_CAPABILITY_DEMONSTRATION | Cuenta teórica, no medición ni promesa |

Trampas: usar salida NUEVA.16 GB físicos no son16 GiB disponibles.
La fuente escala como3^(w-1), no linealmente. u64 duplica bytes por celda.
Llegar a un ancho no significa materializar sus3^w direcciones, y esta
medición corresponde al witness lineal, no a cualquier programa de ese ancho.
