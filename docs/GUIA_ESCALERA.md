# Guía: las dos escaleras de Malbolge Free

Hay **dos escaleras distintas** en este repo y no hay que confundirlas:

| | escalera epochal (M5) | escalera E10 → E19 |
|---|---|---|
| dónde | `evidence/M5_LADDER_SCALE/` | `epoch_ladder/` |
| qué cambia | `w` **dentro de una sola ejecución** | una dimensión fija **por época** |
| qué corre | la VM real completa | el programa juguete `ubO` |
| hasta dónde | 16 medido; 17–19 piden más RAM | 19 |
| qué es | semántica real de Malbolge Free | **juguete**: transporte de estado + codec |

Toda la salida de abajo es real, ejecutada el 2026-09-16 en la laptop (15 GiB).

## Requisitos

- Zig **0.16.0** (`zig version`)
- Python 3 (`py` en Windows, `python3` en Linux)

## 1. Escalera epochal en la VM real

La regla: cuando el puntero `c` llega a `3^w`, `w` sube uno. Para llegar a `w`
el testigo tiene que caminar hasta `3^(w-1)`, y **cada celda ejecutada se
guarda en memoria**. Por eso cada peldaño cuesta el triple.

### Primero, estima la memoria (no corre nada)

```powershell
cd evidence/M5_LADDER_SCALE
py run_ladder_scale.py --estimate 17 18 19
```

```
w=17: c must reach 3^16 = 43,046,721; estimated table ~2.1 GiB
w=18: c must reach 3^17 = 129,140,163; estimated table ~8.4 GiB
w=19: c must reach 3^18 = 387,420,489; estimated table ~16.9 GiB
```

Súmale ~0.6 GiB (programa + salida) y el sistema operativo. Regla práctica:
**necesitas unos 20 GiB libres para 19.** La tabla se reserva completa al
inicio para que no se duplique al crecer. En Windows, si no cabe suele fallar
al arrancar; en Linux el sistema puede aceptar la reserva y matar el proceso
(OOM) a la mitad. Si ves `Killed` o un código de salida raro, fue memoria.

### Corre los peldaños

```powershell
py run_ladder_scale.py 13 14 15 16
```

Salida real (resumida; cada línea del script es un JSON completo):

```
13 PASS 16.2s  steps=531442    padwidth=13 growth=3 cells=532454
14 PASS 19.6s  steps=1594324   padwidth=14 growth=4 cells=1595336
15 PASS 14.6s  steps=4782970   padwidth=15 growth=5 cells=4783982
16 PASS 22.2s  steps=14348908  padwidth=16 growth=6 cells=14349920
```

(Los segundos incluyen compilar con `-O ReleaseFast`.)

Cada peldaño arranca **desde `w = 10`**, así que `16 PASS` significa que
subió 10 → 11 → 12 → 13 → 14 → 15 → 16 en una sola corrida (`growth=6`).

### En una máquina con más RAM (p. ej. 32 GB)

```bash
cd evidence/M5_LADDER_SCALE
python3 run_ladder_scale.py --label xeon-32gb 17 18 19
```

- Cierra lo que puedas antes (navegador, juegos).
- **La GPU no ayuda**: el núcleo es un solo hilo de CPU sobre una tabla hash.
- Si un peldaño falla, el script se detiene ahí (el siguiente pide el triple).
- Los resultados se **agregan** a `results.json` con tu etiqueta, SO, CPU y RAM;
  súbelo para que quede como evidencia. Usa `--label` con algo genérico
  (nunca el nombre del equipo): el repo es público.
- Es una estimación: 19 **todavía no se ha corrido** en ninguna máquina.

### Qué comprobar en el resultado

`"verdict": "PASS"`, `padwidth` igual al peldaño y `growth` igual a
`peldaño - 10`. El programa mismo sale con error si no llega.

### El test corto (ya en `tests/run_all.py`)

```powershell
zig test --dep malbolge_free -Mroot=tests/t_m5_full_vm.zig -Mmalbolge_free=src/malbolge_free.zig
```

```
1/2 t_m5_full_vm.test.full VM run crosses 10 -> 11 -> 12...OK
2/2 t_m5_full_vm.test.full VM run stops at 11 before the second frontier...OK
All 2 tests passed.
```

## 2. Escalera E10 → E19 (juguete)

```powershell
py epoch_ladder/dimension_epoch_ladder.py
```

```
E10: memory=59049 ops=[23, 5, 81] state=5a steps=3
...
E19: memory=1162261467 ops=[23, 5, 81] state=5a steps=3
LADDER PASS: E10 -> E19
```

```powershell
py epoch_ladder/offset_epoch_ladder.py run
```

```
E11: offsets=[0, 171, 154] roundtrip=True boundary=True FORMULA_GENERALIZES_E11=DEMONSTRATED
...
E18: offsets=[0, 170, 152] roundtrip=True boundary=True FORMULA_GENERALIZES_E18=DEMONSTRATED
  "first_failure": null,
  "claim": "FORMULA_GENERALIZES_E11_TO_E18=DEMONSTRATED"
```

```powershell
py -m unittest discover -s epoch_ladder -p "test_*epoch_ladder.py"
```

```
Ran 7 tests
OK
```

**Por qué es un juguete:** no existe un Malbolge histórico de 11 a 18 trits.
Lo que cruza la escalera es el byte `Z` sellado y el codec posicional; `crazy`,
rotación, cifrado y saltos **no** están demostrados en los anchos intermedios.
Solo E10 (Classic) y E19 (estilo Unshackled) son anclas reales.

`dimension_epoch_ladder.py` reescribe `epoch_ladder/fixtures/dimension_epoch_ladder.json`
cada vez que corre; si `git diff` muestra cambios ahí, algo cambió de verdad.
