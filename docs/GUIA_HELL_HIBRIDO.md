# Guía: HeLL Classic híbrido (lmao-lite + LMAO externo)

Escribes o generas HeLL, LMAO de Matthias Lutter lo ensambla como programa externo,
y nuestros dos motores Classic comprueban el resultado. Toda la salida de esta guía es
real, ejecutada el 2026-09-13.

## Por qué híbrido

Se midió que ningún programa HeLL real cabe en Classic solo con bytes de carga. Para el
cat más simple, los 1,504 acomodos posibles fallan: el mejor deja 5 de 9 celdas de datos
válidas. Hace falta código de inicialización en tiempo de ejecución, que es la parte
difícil de LMAO. Mientras hacemos el nuestro, LMAO pone esa pieza y nosotros ponemos
los frontends y la verificación.

**Licencia:** LMAO es GPLv3. Vive en `_external/LMAO`, junto a este repositorio y fuera de
los repos. Se invoca como proceso: no se importa, no se enlaza y no se copia. El commit y
la receta de compilación están en `_external\README.md`.

## 1. Generar HeLL desde texto

```powershell
cd tools
py hell_frontend.py text "Hello, World!\n" > hw.hell
```

Cada byte `b` se convierte en `ROT rotl(b) R_ROT OUT ?- R_OUT`:

- **`Rot`** gira la celda de dato para que A valga `b`;
- **`Out`** imprime A mod 256;
- **`R_ROT` y `R_OUT`** devuelven cada gadget a su comando.

Al final, `HLT`.

Para leer y repetir N bytes:

```powershell
py hell_frontend.py echo 3 > echo3.hell
```

## 2. Ensamblar y verificar

```powershell
py lmao_bridge.py verify hw.hell --expect 48656c6c6f2c20576f726c64210a
```

```
PASS  oracle: HALTED steps=6382 output=b'Hello, World!\n'
PASS  zig:    HALTED steps=6382 (== oracle: True)
BRIDGE_VERIFY=PASS
```

```powershell
py lmao_bridge.py verify echo3.hell --stdin 414243 --expect 414243
```

```
PASS  oracle: HALTED steps=2359 output=b'ABC'
PASS  zig:    HALTED steps=2359 (== oracle: True)
BRIDGE_VERIFY=PASS
```

Para obtener solo el `.mb`: `py lmao_bridge.py assemble hw.hell -o hw.mb`.
Si LMAO está en otra ruta, define `LMAO_EXE`.

## 3. Tests

```powershell
py -m unittest test_hell_frontend -v
```

```
Ran 8 tests in 3.650s

OK
```

Qué cubren:

- Hello World;
- los 256 valores de byte;
- cadenas aleatorias;
- cadena vacía;
- eco de 32 bytes aleatorios;
- EOF (`A` seguido de `0xA8 0xA8`);
- **dos controles que podrían fallar:**
  1. cambiar un valor cambia la salida (`AB` → `AC`);
  2. quitar `R_ROT` desincroniza el flujo de datos. Medido: se detiene tras 2,543 pasos
     sin imprimir nada; el programa normal imprime `AB`.

## 4. Lo que sigue

1. **Inicializador propio**, pieza por pieza. Se mide contra LMAO en
   `evidence/A5_LMAO_PARITY_V0`, empezando por `simple_cat`.
2. **`tools/hell_classic.py`** ya tiene el parser HeLL real y la física de celdas: ciclos
   xlat2, etiquetas −1, `R_` y arranque en `ENTRY`. Es la base.
3. **Port a Zig** dentro de lmao-lite cuando la pieza en Python pase.
