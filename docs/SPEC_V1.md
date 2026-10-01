# Malbolge Free — Especificacion V1 (Borrador M0)

Estado: **DRAFT / NO NORMATIVA**.

Este documento congela las decisiones que ya estan claras y enumera las que no
pueden considerarse cerradas hasta que exista un unico runtime canonico.

## 1. Modelo De Estado

La maquina mantiene:

- `a`: acumulador entero;
- `c`: contador de instrucciones;
- `d`: puntero de datos;
- `M`: memoria direccionada por enteros no negativos;
- `w`: ancho actual en trits;
- `steps`: contador monotono de pasos;
- `stdout`: secuencia de bytes emitidos.

Estado inicial:

```text
a = 0
c = 0
d = 0
w = width inicial
steps = 0
stdout = vacio
```

## 2. Entrada Y Memoria

- Se ignoran espacios, tabuladores, CR y LF del programa fuente.
- Cada caracter restante debe estar entre ASCII 33 y 126 inclusive.
- El programa debe contener al menos dos celdas.
- Las celdas del programa se cargan en `M[0..program_len)`.
- Una celda no materializada se obtiene mediante:

```text
M[i] = crazy(M[i-1], M[i-2], w inicial)
```

- Con `mem_limit != null`, las direcciones se reducen modulo `mem_limit`.
- Con `mem_limit == null`, las direcciones no se envuelven.


## 3. Operaciones Tritwise

La tabla `CRZ` normativa es:

       b=0  b=1  b=2
a=0     1    0    0
a=1     1    0    2
a=2     2    2    1
```

`crazy(a,b,w)` procesa exactamente `w` trits, de menor a mayor peso.

`rotate(v,w)` es la rotacion derecha de un trit dentro de exactamente `w`
trits:

rotate(v,w) = floor(v/3) + (v mod 3) * 3^(w-1)
```

`pow3(w)` debe ser exacto para todo ancho soportado.

Limite publico actual: `1 <= w <= 80` con `u128`. `3^80` es exacto y `3^81`
queda fuera del dominio definido. BigInt es una decision futura; no se puede
presentar crecimiento arbitrario como soportado.

**Riesgos de precision fijados por prueba (no corregidos).**
`tests/t_m0_eof_precision.zig` fija el comportamiento real, que en dos puntos no
es el ideal:

1. `pow3(n)` con `n >= 81` **devuelve `u128::max` en vez de fallar**. Un llamador
   puede recibir un modulo plausible pero incorrecto sin ningun error. Fijado con
   test; cambiarlo alteraria la firma publica, asi que queda como limitacion
   aceptada, no como garantia.
2. El guard `1 <= width <= 80` de `init()` es un `std.debug.assert`, y
   `ReleaseFast` lo compila fuera. Un ancho fuera de dominio solo se detecta en
   builds de depuracion.

La via densa (`enableDenseSource`) si rechaza explicitamente `w >= 21`, porque
`3^21` no cabe en el elemento `u32`; ese techo es real y verificable.

## 4. Decodificacion Y Ejecucion

```text
op = (M[c] + c) mod 94
```

Semantica:

| op | accion |
|---:|---|
| 4 | `c = M[d]` |
| 5 | emitir `a mod 256` |
| 23 | leer un byte; EOF usa el sentinel definido abajo |
| 39 | rotar `M[d]`; guardar resultado en `M[d]` y `a` |
| 40 | `d = M[d]` |
| 62 | `M[d] = crazy(a, M[d], w)`; `a = M[d]` |
| 68 | no-op |
| 81 | halt |
| otro | no-op |

Despues de una instruccion no-halt:

1. si hubo salto, usar el `c` destino;
2. si `M[c]` es ASCII imprimible, aplicar `TRANSLATED[M[c]-33]`;
3. avanzar `c` y `d` una celda, aplicando wrap solo si existe `mem_limit`.

## 5. Modos

### `fixed`

- `w` permanece igual al `width` inicial;
- Classic es `width=10` y `mem_limit=3^10`;
- debe ser byte-compatible con Classic.

### `pad_to_padwidth`

Es un modo experimental. El crecimiento por valores no esta aceptado como
semantica de release porque `rotate` no conserva significado al cambiar de
ancho.

Estado: **NOT_RELEASED**.

### `epochal`

- inicia con `w=width`;
- requiere memoria sin limite para cruzar fronteras;
- antes de tocar la celda del paso, si `c >= 3^w` o `d >= 3^w`, aumentar `w` en
  uno;
- nunca reescribe memoria, salida o pasos historicos;
- `w` es siempre un entero finito y monotono.

Estado: `10 -> 11 -> 12` demostrado en el witness comprometido
(`evidence/f9_repeated_frontier.json`, steps 59050 and 177148). Escalera adicional hasta
`19` medida el 2026-10-01 con la representacion densa
(`evidence/M5_LADDER_SCALE/results.json`, filas `linux-14gib-dense`). Verificar
el disco antes de citar: este texto quedo detras de la evidencia.

## 6. EOF

El runtime actual usa `u128::maxInt(u128)` internamente y lo normaliza en las
operaciones. El comportamiento observable de EOF debe quedar fijado con casos
de prueba para `in`, `crazy` y `out`.

Estado: **CERRADO** (2026-10-01). `tests/t_m0_eof_precision.zig` fija con trazas
ejecutadas, no con prosa:

| caso | resultado observado |
|---|---|
| `in` en EOF -> `out` | emite exactamente `0xff`, termina `HALTED` |
| `in` en EOF repetido | el sentinel es pegajoso: N lectures dan N `0xff` |
| byte real vs EOF | el mismo programa distingue: `A` -> `0x41`, EOF -> `0xff` |
| `in` en EOF -> `crazy` | normaliza a `3^w - 1`; valor verificado contra `crazy(3^w-1, mem[d], w)` calculado en el test |
| sentinel en la traza | `a_before = 0`, `a_after = u128::max` justo tras `in` |
| `in` en EOF -> `rot` | `rot` lee `mem[d]`, no el acumulador: EOF no se filtra ahi |

Nota de calculo: como `c` y `d` avanzan juntos desde 0, en el paso `crazy`
`c == d == 2` y la celda leida sigue siendo el caracter fuente intacto. Eso hace
el valor esperado **computable**, no una constante magica.

## 7. Resolucion M1 De La Contradiccion

Durante M0 se detecto que la copia canonica `src/malbolge_free.zig` y la copia
usada por el checker F4 no eran iguales. M1 corrigio el runtime canonico y
elimino la dependencia ejecutable de la copia de `evidence/`.

La semantica correcta para el acumulador es:

```zig
const modulus: u128 = pow3(w);
const opA = if (a == EOF_SENTINEL) modulus - 1 else (a % modulus);
```

F4 ahora importa `src/malbolge_free.zig` como modulo `malbolge_free` y compara
contra el oraculo externo de Malbolge-Translator.

## 8. Gates M0

- [x] Estado inicial escrito.
- [x] Loader y rango de fuente escritos.
- [x] Tabla `crazy` y `rotate` escritas.
- [x] Instrucciones y post-instruccion escritas.
- [x] Modos y limitaciones declarados.
- [x] Contradiccion entre copias detectada.
- [x] Decisiones de precision numerica cerradas, con dos riesgos aceptados y
      fijados por prueba (saturacion silenciosa de `pow3`; guard de ancho solo en
      depuracion). La via densa fija un techo en `w = 20`.
- [x] EOF fijado con casos normativos ejecutados (`tests/t_m0_eof_precision.zig`).
- [x] Un unico runtime marcado como canonico.

**Veredicto M0:** `PARTIAL / SEMANTICS_DRAFTED`.

**Veredicto M1:** `PASS para F4 Classic`; EOF, precision numerica y los modos
no-`fixed` siguen abiertos para los milestones siguientes.
