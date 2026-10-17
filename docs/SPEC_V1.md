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
| 23 | leer un byte; en EOF asigna `3^w - 1` (seccion 6) |
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

`in` en EOF asigna el valor canonico `3^w - 1`; con `w = 10` es `59048`. Ese es el
valor del interprete original de 1998 (`malbolge.c`: `if ( x == EOF ) a = 59048;`)
y el de `fast20.c` de Iizawa (`INS_23:;int CR=getchar();a=CR==EOF?END-1:CR;`, con
`#define END 1162261467ULL` = `3^19`). No es un centinela negativo ni `u128::max`.

Estado: **CERRADO** (2026-10-01; corregido 2026-10-17). Antes de la correccion el
runtime guardaba `u128::max` y lo normalizaba solo dentro de `crazy`, asi que `out`
tras EOF emitia `0xff`. Una auditoria externa de 2026-10-17 midio la divergencia
frente a tres oraculos canonicos; `docs/HONESTY_LEDGER.md` entrada 24 registra el
cambio y `docs/CLASSIC_SEMANTICS.md` explica el origen del error (la copia
`MALDOOM/vendor/malbolge/malbolge.py`, que aun lleva `a = -1`). La tabla es la
observada despues de la correccion, fijada con trazas ejecutadas en
`tests/t_m0_eof_precision.zig`, no con prosa:

| caso | resultado observado |
|---|---|
| `in` en EOF -> `out` | emite exactamente `0xa8` (= `59048 % 256`), termina `HALTED` |
| `in` en EOF repetido | el valor es pegajoso: N lectures dan N `0xa8` |
| byte real vs EOF | el mismo programa distingue: `A` -> `0x41`, EOF -> `0xa8` |
| `in` en EOF -> `crazy` | `3^w - 1` entra como operando ordinario: `crazy(3^w-1, mem[d], w)`, valor calculado en el test |
| EOF en la traza | `a_before = 0`, `a_after = 59048` justo tras `in` |
| `in` en EOF -> `rot` | `rot` lee `mem[d]`, no el acumulador: EOF no se filtra ahi |
| `in` en EOF con `w = 19` | emite `0xda` (= `(3^19 - 1) % 256`): EOF sigue el ancho de la maquina, no una constante Classic. Control medido: `fast20.c` compilado localmente sobre `ubO` con stdin vacio imprime exactamente `da` |

Nota de calculo: como `c` y `d` avanzan juntos desde 0, en el paso `crazy`
`c == d == 2` y la celda leida sigue siendo el caracter fuente intacto. Eso hace
el valor esperado **computable**, no una constante magica.

Consecuencia en la capa BF: el backend baja `,` como `IN; STORE`, de modo que `,`
en EOF ya no guarda 0 sino `168`. El idiomita `,[.,]` ("leer hasta EOF") deja de
terminar. Los casos diferenciales BF llevan ahora un terminador `0x00` explicito
en la entrada (`tests/t_m64_branch.zig`, `tests/t_m65_differential.zig`) y
`tests/t_m63_input.zig` fija el byte canonico. La convencion `,` -> 0 de los VMs
BF de referencia no se toca: es otra maquina.

## 7. Resolucion M1 De La Contradiccion

Durante M0 se detecto que la copia canonica `src/malbolge_free.zig` y la copia
usada por el checker F4 no eran iguales. M1 corrigio el runtime canonico y
elimino la dependencia ejecutable de la copia de `evidence/`.

La semantica correcta para el acumulador es:

```zig
const modulus: u128 = pow3(w);
const opA = a % modulus;
```

No hay rama especial para EOF: despues de la correccion de la seccion 6 el
acumulador ya llega dentro de rango y `crazy` lo consume como cualquier otro valor.
El checker `evidence/compare_f4_canonical.py` (gate F4c) compara los dos cores
contra los oraculos canonicos. Desde 2026-10-17 el interprete canonico de Python
esta vendorizado en `vendor/canonical_malbolge_py/malbolge.py` (copia verbatim de
`github.com/DannyBaanks/MALBOLGE@bf4d6fa`, fijada por SHA-256 y documentada en su
`PROVENANCE.md`), asi que el gate se mide tambien en una clonacion limpia o en CI;
si el fichero vendorizado no coincide con el hash fijado el gate falla con codigo
4, y si no hay ningun oraculo utilizable sale con codigo 3 (`NOT_DEMONSTRATED`).
`evidence/compare_f4.py` queda como la medicion de la divergencia con el oraculo
antiguo de Malbolge-Translator.

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

**Veredicto M1:** `PASS para F4 Classic` (2026-10-01). Re-medido 2026-10-17 contra
oraculos canonicos: `PASS para F4c` — 22 veredictos byte-a-byte (11 casos x 2 cores)
y 44 comparaciones de SHA-256 con los dos oraculos de esta maquina; en CI, con el
oraculo vendorizado como unico canonico disponible, son 10 casos x 2 cores x 1
oraculo = 20 comparaciones. El centinela
de EOF fue retirado y `in` en EOF asigna `3^w - 1`. Precision numerica y los modos
no-`fixed` siguen abiertos para los milestones siguientes.
