# Malbolge Free

```
Malbolge Classic    :   >:(
Malbolge Unshackled :   >:D
Malbolge Free       :   ^ω^   (Malbolgato)
```

Runtime parametrico de Malbolge en Zig. Un nucleo, cualquier ancho de trit `k`, sin
carcel hardcodeada de 3^10. *Y* la ampliacion de limites de ejecucion funciona: `c`/`d`
avanzan `+1` por paso hasta que tocan `3^k`, en cuyo punto el runtime
amplia el ancho **una vez** y conserva el trazo anterior. Sin reescritura.

## Que es esto

`MalbolgeCore(width, mem_limit, growth_policy)` — un nucleo, tres perillas.

| politica | el ancho evoluciona? | por que? |
|---|---|---|
| `fixed` | no | Semantica clasica |
| `pad_to_padwidth` | si — por desbordamiento de valor | **DESTRUIDO** por rotate (ver evidencia) |
| `epochal` | si — por frontera de direccion | **PROBADO** viable para `widen` |

## Demostrado

**PARIDAD**: corpus clasico (`hello.mal`, 3 echos, reproductor, quine) — 6/6 sha256
coinciden con la referencia Python en k=10.

**K-ARBITRARIO**: la memoria se mantiene sana en k ∈ {10, 11, 12, 19, 20, 23, 26}.

**AMPLIACION DE FRONTERA**: un programa de 70000 caracteres de puros ops `in`/`out`/`nop`
(construido en `evidence/gen_frontier_witness.py`) corre hasta que `c` cruza
`3^10 = 59049`; el trigger epochal se dispara exactamente una vez, `padwidth` sube
`10 → 11`, y el trazo hasta ese punto queda intacto. Confirmado:

```
WIDEN at step=59049, max_addr=70136, padwidth=11
```

**CRUZE DE 3^19** (testigo legal-movd): el programa `' & % $` ejecuta
movd dos veces sobre crazy-fill perezoso y termina con `d = 1743392169 > 3^19 =
1162261467`. Tanto Python como Zig concuerdan en los valores exactos de los registros.

**ROPTURA DE EXTENSION DE ANCHO** (interpretacion `fixed`): rotate ensanchado in-place
produce un resultado inconsistente entre anchos el 33% del tiempo — rotate tiene
`v % 3` aliased al HI trit unicamenteen ancho `k`, y el widen posterior
cambia el valor. Asi que `pad_to_padwidth` se fue del pool de claims.

**PERIODICIDAD DE LAZY-FILL**: la cadena crazy entra en un ciclo de periodo 6 en
`program_len + 2` sin importar el ancho (verificado numericamente en anchos
10..26 y varias parejas de semillas). Esto da O(1) en busqueda de celdas perezosas.

## No Demostrado / Destruido

| Claim | Estado |
|---|---|
| TRUE_OMEGA_SEMANTICS | **NOT_DEMONSTRATED** |
| UNSHACKLED_PARITY | **NOT_DEMONSTRABLE** por construccion (usa srand(time(NULL))) |
| VALUE-OVERFLOW WIDENING | **DESTRUIDO** (rotate rompe la injectividad) |
| FRONTIER WIDENING | **DEMOSTRADO** ^ω^ |

## El Badge "Purrfect"

El patron que hace esto lo que es: **los valores de memoria envueltos en crazy se
quedan dentro del byte**, pero las direcciones de memoria (c, d) siguen avanzando por
el espacio de direcciones incluso cuando mem_limit=null. Crazy no depende del ancho.
Rotate si. Entonces el lugar donde cambia tu ancho tiene que ser "avance de puntero", no
"valor de celda". Danny construyo este proyecto alrededor de ese hallazgo.

## Ejecutar

```bash
# paridad del corpus (referencias Python biz op)
py evidence/compare_f4.py

# evidencia de ampliacion de frontera (zig)
zig run tests/t_frontier_moment.zig

# testigo de cruce (validador)
zig run evidence/f7_witness.zig
```

Cada archivo de evidencia imprime su propio veredicto; nada esta disperso en markdown
solo-para-nerts. Todos los bytes crudos estan en evidence/.

## Licencia

MIT ^ω^

(Es el gato. Siempre es el gato.)
