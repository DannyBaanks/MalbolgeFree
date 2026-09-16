# M4 — NADA V0: primer microprograma propio sobre Malbolge Classic

Fecha: 2026-09-16. Continúa `../M3_RAW_LAYOUT_V0` (no lo rehace: su regresión se
comprueba aquí y sigue en 256/256).

## Qué cambia respecto a M3

M3 demostró `sintetiza(byte)`. M4 demuestra **ejecutar una secuencia pequeña de
comportamiento** en **un solo** programa Malbolge, todo clean-room: sin LMAO en runtime,
sin HeLL, sin `gen_init`.

## Lo que se re-derivó (y hay que subrayar)

M3 descubrió que, tras la primera `MovD`, `d = c + 40`. **Ese invariante es local al tramo
lineal.** Al introducir `Jmp` volvimos a derivar la geometría, sin dar por hecho nada:

```
paso  c    d    op     d-c
1     0    0    movd   0
2     1    41   jmp    +40
3     58   42   out    -16      <- tras el salto
4     59   43   hlt    -16
```

La VM hace `c = mem[d]`, **cifra la celda de aterrizaje sin ejecutarla** y sigue en
`mem[d] + 1`, mientras `d` avanza 1. Por tanto:

    offset_nuevo = (d_del_jmp + 1) - destino

El emisor lleva `c` y `d` explícitos y nunca asume `+40`. Hay un test que lo fija
(`test_jump_breaks_the_linear_offset`).

Consecuencias medidas:
- El puntero del salto (`destino - 1`) debe ser imprimible, así que **los destinos viven
  entre 34 y 127**.
- Tras saltar, los datos siguen en `d_jmp + 1` mientras el código arranca en el destino:
  `d` queda `(destino - d_jmp - 1)` celdas por detrás, y **ese hueco es el presupuesto de
  instrucciones del tramo posterior**. Por eso la política determinista elige el destino
  **más lejano** válido.

## El otro cambio que lo hizo compacto

En M3 la búsqueda era "dado el valor, encuentra una celda válida", lo que obligaba a
rellenar con nops y terminaba haciendo chocar código y datos. M4 la invierte: **"dado
dónde está `d` ahora, ¿qué valores son válidos en carga en esa celda?"**. El tramo lineal
queda sin un solo `goto`:

| programa | antes (M3) | ahora (M4) |
|---|---|---|
| `HI\n` | 94 celdas / 42 pasos | **51 celdas / 13 pasos** |

## Resultados (19 casos, los dos motores)

| milestone | casos | oráculo | paridad Zig |
|---|---:|---:|---:|
| M4A salida múltiple | 5 | 5/5 | 5/5 |
| M4B entrada | 5 | 5/5 | 5/5 |
| M4C estado | 4 | 4/4 | 4/4 |
| M4D salto | 1 | 1/1 | 1/1 |
| M4E compuesto | 4 | 4/4 | 4/4 |

`M4_PASS`. La paridad compara **estado, salida y número de pasos**.

### M4A — salida secuencial

`emit_program([("out", b) for b in data] + [("halt",)])` produce **un** programa.

| datos | celdas | pasos |
|---|---:|---:|
| `A` | 44 | 6 |
| `AB` | 47 | 9 |
| `HI\n` | 51 | 13 |
| `\x00\xff\x7f` | 51 | 13 |

### M4B — entrada real

`IN; OUT; HALT` son **4 celdas**: `(taN`. Roundtrip exacto de `0x00`, `0x41`, `0x7f`, `0xff`.

**Semántica de EOF (documentada y probada aparte):** sin entrada, `IN` deja `A = 59048`
(C2) y `OUT` emite `59048 % 256 = 0xa8`.

### M4C — estado y transformación

Un byte leído **sobrevive como estado computacional** y se transforma antes de salir:
`IN` → `Opr v` (`A := crazy(A, v)`) → `OUT`, con `v = 39`.

| entrada | esperado `crazy(x,39) % 256` | salida |
|---|---|---|
| `0x41` | `0x41` | `0x41` |
| `0x00` | `0x36` | `0x36` |
| `0xff` | `0x37` | `0x37` |
| `0x7a` | `0xdb` | `0xdb` |

(El caso `0x41` coincide consigo mismo por casualidad aritmética; los otros tres muestran
la transformación real.)

**Esto no es memoria general.** Es una sola ruta de estado viva.

### M4D — salto incondicional

```
OUT 'A'
JMP done
OUT 'X'      # inalcanzable (trampa)
done:
OUT 'B'
HALT
```

Salida: **`AB`**, 122 celdas, 10 pasos. El byte trampa `X` **nunca** aparece.

### M4E — microprograma compuesto

```
OUT '>' ; IN ; OUT_ACC ; JMP done ; OUT 'X' (inalcanzable) ; done: OUT '\n' ; HALT
```

120 celdas, 14 pasos, idéntico en ambos motores:

| entrada | salida |
|---|---|
| `A` | `>A\n` |
| `\x00` | `>\x00\n` |
| `z` | `>z\n` |
| `\xff` | `>\xff\n` |

Toca constante, secuencia, entrada, eco del dato leído, control de flujo y halt.

## Tamaño y crecimiento

| bytes | celdas | pasos | celdas/byte |
|---:|---:|---:|---:|
| 1 | 44 | 6 | 44.0 |
| 2 | 47 | 9 | 23.5 |
| 3 | 50 | 12 | 16.7 |
| 5 | 56 | 18 | 11.2 |
| 8 | 65 | 27 | 8.1 |

**Crecimiento lineal: +3 celdas y +3 pasos por byte.** Sin explosión. Las ~41 celdas de
base son la región fija que impone el desplazamiento inicial. Los programas con salto
llegan a ~120 celdas porque el destino se elige lejano a propósito (para dejar hueco).

## Determinismo

Para la misma descripción, el SHA-256 de la fuente generada es estable (5 ejecuciones,
dos programas distintos). La búsqueda es un BFS con orden fijo; no hay aleatoriedad.

## Veredictos

### DEMONSTRATED
- Salida de múltiples bytes arbitrarios en un solo programa.
- Entrada real de un byte con la instrucción `In` de Malbolge.
- Un valor leído sobrevive como estado y se transforma antes de salir.
- Salto incondicional real, con trampa inalcanzable que nunca se ejecuta.
- Microprograma compuesto que combina todo lo anterior.
- Paridad Python/Zig en estado, salida y pasos, en los 19 casos.
- Fuente determinista.
- Regresión de M3: 256/256 sigue pasando.

### NOT_DEMONSTRATED
- Ramificación condicional.
- Bucles (ni acotados).
- Salto hacia atrás (no se intentó: el stretch pedía no montar infraestructura).
- Compilación de HeLL arbitrario.
- Funciones, stack, heap.
- Memoria mutable de propósito general.
- Frontend Turing-completo.

### PARTIAL
- El control de flujo existe pero **sólo hacia adelante y sin condición**.
- Los destinos de salto están limitados al rango 34..127 por la restricción del puntero.

## Reproducir

```powershell
cd evidence/M4_MICROPROGRAM_V0
py run_m4.py
cd ..\..\tools
py -m unittest test_microprogram -v
```
