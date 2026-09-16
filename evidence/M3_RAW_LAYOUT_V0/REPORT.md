# M3 — Motor de layout propio: Malbolge Classic crudo, 256/256

Fecha: 2026-09-16. Cierra la decisión de Danny (2026-09-14): cerrar el hueco con un
**motor propio**, no con la maquinaria `U_`/`FLAG`/`MOVED` de LMAO.

## Resultado

**Emitimos Malbolge Classic crudo nosotros mismos, sin LMAO, sin HeLL y sin `gen_init`.**

| métrica | resultado |
|---|---|
| bytes de salida cubiertos | **256 / 256** |
| verificados en el oráculo Python | **256 / 256** |
| verificados en el runner Zig | **256 / 256**, estado, salida y **pasos idénticos** |
| tamaño de programa | 42 a 118 celdas (media 60) |
| comparación: LMAO para un solo newline | 2,069 celdas, 1,803 pasos |

Nuestros programas son ~**34× más chicos** que los de LMAO porque no sintetizamos el data
module genérico: colocamos los operandos ya válidos en carga y solo encadenamos rot/crazy.

## El descubrimiento que lo hizo posible

La celda 0 lleva el carácter 40 (`(`), que en la posición 0 decodifica a `MovD` **y** cuyo
valor es 40. Así la primera instrucción deja `d = 40`, y a partir de ahí **`d = c + 40`**
mientras la ejecución es lineal.

Consecuencia: una operación en la posición de código `p` opera sobre la celda de datos
`40 + p`, y el acumulador A se arrastra entre operaciones. Una cadena de `Rot`/`Opr` en
posiciones crecientes **es** el modelo de síntesis, sin lista enlazada.

## Los dos modelos emitidos

1. **Cadena inline** — `Rot v` (A := rot(v)) y `Opr v` (A := crazy(A, v)) sobre celdas
   frescas. Cubre **201/256**. Relleno de nops desplaza cada operación hasta que su
   operando cae en una celda donde es válido en carga.
2. **Acumulador persistente** — mantiene una celda ACC y la revisita, lo que exige
   **retroceder `d`**: un `MovD` cuya celda-puntero (colocada donde `d` esté, tras relleno
   de nops) contiene `ACC − 1`. Cierra los 55 restantes (154..208).

## Los tres bugs que costaron el cierre

1. **`ROT WK0` rotaba la *dirección*, no el valor.** En HeLL una etiqueta como operando
   almacena su dirección; por eso el newline daba 193 en vez de 10.
2. **El puntero de retroceso debe ser válido en la celda donde `d` está *en ese momento*.**
   Faltaba insertar nops para mover `d` hasta una celda donde el puntero sea válido en carga.
3. **`MovD` sí puede saltar hacia atrás.** Mi `goto` cortaba la búsqueda cuando `d` ya había
   pasado el objetivo. Quitar esa condición desbloqueó los últimos 4 bytes (164, 165, 193, 194).

## Controles

- **El byte objetivo nunca se almacena**: cada operando es un imprimible 33..126 distinto
  del objetivo; se sintetiza con rot/crazy. Verificado en el test suite.
- **Paridad de dos motores**: oráculo Python y runner Zig coinciden en estado, salida y
  número de pasos en los 256.

## Archivos

- `tools/raw_malbolge.py` — el motor (búsqueda de recetas + layout + emisión).
- `tools/test_raw_malbolge.py` — 5 tests, incluida la paridad con Zig.
- `docs/GUIA_RAW_MALBOLGE.md` — guía en español con salida real.

## Veredictos

| Claim | Estado |
|---|---|
| Emitimos Malbolge Classic crudo propio, sin LMAO | DEMONSTRATED |
| Cobertura de los 256 bytes de salida | DEMONSTRATED 256/256, dos motores |
| El byte objetivo se sintetiza, no se almacena | DEMONSTRATED |
| Nuestro layout es más compacto que el de LMAO | DEMONSTRATED (60 vs 2,069 celdas de media/caso) |
| Esto es un ensamblador HeLL completo | NOT_CLAIMED — emitimos salida de bytes, no el lenguaje HeLL entero |
