# A5 — LMAO (Lutter) contra lmao-lite (nuestro)

Fecha: 2026-09-13. Gate A5 de `docs/LMAO_LITE_ROADMAP.md`: "comportamiento igual en
lmao-lite y LMAO". Antes estaba `BLOCKED UNTIL LMAO BUILD`.

## Preguntas

- **H1.** ¿Los programas que genera LMAO v0.6.0 cumplen **las pruebas del propio
  LMAO** cuando corren en **nuestros** motores Classic?
- **H2.** ¿lmao-lite ensambla los mismos 6 ejemplos HeLL en programas que cumplen lo
  mismo?

La especificación no la escribimos nosotros: sale de `testcases.bash` de LMAO.

## Método

- **Prerregistro:** `PREREGISTRATION.json`, SHA-256 `c88de44f…`, congelado antes de
  ejecutar ningún programa. Declara que ya se había leído el código de lmao-lite y que
  se esperaba FAIL en H2.
- **LMAO:** commit `3ea747e1` compilado en Windows sin instalar nada: winflexbison
  2.5.25 portable más `gcc` de mingw-winlibs.
- **Licencia:** LMAO es GPLv3. Sus fuentes y ejemplos **no se copian** a este repositorio.
  `run_parity.py` los lee de un clon externo y verifica sus hashes contra el prerregistro.
- **Motores:** `MALBOLGE/malbolge.py` (oráculo) y `MALBOLGE/intermediate_vm_runner.exe`
  (Zig, forma `@archivo`).
- **lmao-lite:** `lmaolite_driver.zig` llama a `Parser.parse → resolveLayout → emit`,
  las mismas funciones que usan los tests de malbolge-free, sin modificar lmao-lite.

```powershell
git clone https://github.com/esoteric-programmer/LMAO  # y compilar lmao.exe (ver PREREGISTRATION.json)
zig build-exe --dep hell -Mroot=lmaolite_driver.zig -Mhell=../../src/hell.zig -femit-bin=lmaolite_driver.exe
py run_parity.py --lmao-dir <clon LMAO> --driver lmaolite_driver.exe
```

## Resultados

### H1 — LMAO en nuestra maquinaria: **PASS (34/34)**

| ejemplo | celdas | casos | pasos (Zig = oráculo) |
|---|---:|---:|---|
| simple_hello_world | 4,607 | 1 | 4,475 |
| hello_world (con bucles) | 14,795 | 1 | 27,938 |
| simple_cat (infinito) | 2,050 | 1 | eco exacto de 256 bytes aleatorios |
| cat_halt_on_eof | 20,775 | 1 | 472,965 |
| digital_root | 31,754 | 7 | 42,890 a 572,131 |
| adder | 55,724 | 6 | 168,058 a 400,641 |

Cada caso pasa en los dos motores. En todos los casos que terminan, los dos motores dan
**el mismo número de pasos**. En `simple_cat`, el Zig para por tope de salida y el
oráculo por combustible; se juzga el prefijo, como en `testcases.bash`.

### H2 — lmao-lite con los mismos ejemplos: **FALSIFIED (0/6)**

| ejemplo | dónde falla | qué hace |
|---|---|---|
| simple_hello_world | emit | `InvalidDataValue`: no admite datos fuera de 33..126, como `C1` = 29524 |
| hello_world | layout | `UnknownLabel` |
| simple_cat | comportamiento | 12 celdas; imprime **un** byte equivocado (`0x61`, el 2.º de la entrada) y se detiene en 99 pasos |
| cat_halt_on_eof | comportamiento | 74 celdas; se detiene en 4 pasos sin salida |
| digital_root | comportamiento | 120 celdas; se detiene en 66 pasos sin salida, con cualquier entrada |
| adder | comportamiento | 160 celdas; se detiene en 129 pasos sin salida, con cualquier entrada |

**`A5_GATE = FAIL`.**

## Cómo leerlo

- **Nuestra maquinaria queda validada por un tercero.** Seis programas reales de
  Lutter, con bucles, condicionales, aritmética decimal y hasta 572,131 pasos, corren
  idénticos en el oráculo Python y en el runner Zig. Es la prueba independiente más
  fuerte que tienen hasta hoy nuestros motores Classic.
- **lmao-lite no es todavía un ensamblador HeLL, sino un parser con emisor.**
  Coincide con lo que se ve en el código:
  - pone las instrucciones seguidas desde la celda 0;
  - no tiene `ENTRY` ni código de inicialización;
  - toma solo el primer comando de cada ciclo xlat2;
  - no ajusta las etiquetas en −1;
  - no admite datos grandes.
- **Sus tests A6 ("cat multi-byte, 7/7") eran estructurales.** Comprueban 12 caracteres
  imprimibles y la posición de las etiquetas, pero nunca ejecutan el cat. El roadmap ya
  tenía la regla que lo habría evitado: "Un parser que emite texto no es un ensamblador
  demostrado".

## Errores y desviaciones (todos declarados)

1. **Entrada del cat mal generada en la primera corrida.** Salió como 256 copias de
   `0x30` en vez de bytes aleatorios, porque se creaba un `Random(semilla)` nuevo en cada
   byte. Se corrigió y se volvió a correr; los dos logs se conservan
   (`run_log_first_run_bug.txt`, `run_log.txt`). **El bug favorecía a lmao-lite:** con
   ceros, su `simple_cat` parecía un eco parcial (`0x30`); con bytes reales, imprime un
   byte equivocado.
2. **Tope de combustible de `simple_cat`.** Se limitó a 5,000,000 en ambos motores para
   no volcar cientos de MB de salida. Se declaró en el código antes de correr.
3. **Una predicción mía que falló.** Esperaba que las salidas de lmao-lite no pasaran la
   validación de carga Classic. **Sí la pasan**; fallan después, al ejecutarse.

## Qué nos da Lutter, concretamente

1. **Un oráculo HeLL → Classic** que corre bit a bit igual en nuestros dos motores.
   Cualquier compilador nuestro puede medirse contra él por comportamiento.
2. **La especificación de lo que falta en lmao-lite**, en su README y en `gen_init.c`:
   - colocación con restricción xlat2;
   - `U_`/`R_` y etiquetas −1;
   - `RNop`;
   - generación de código de inicialización con el *data module* de constantes.
3. **Una validación cruzada del reporte mini-Lutter.** Su "semilla 29524 = todos los
   trits en 1" es la constante `C1` de HeLL. Su "celda sin dígito 2" es la nota
   `TMP (all trits must be 0 or 1)` del `datamodule.txt` de LMAO. La "fórmula del
   compilador" que se midió descompilando la quine es el mecanismo que LMAO ya documenta.
