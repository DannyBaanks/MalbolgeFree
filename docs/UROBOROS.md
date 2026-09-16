# M7 — Quinepiler / Uroboros

El objetivo es probar un ciclo de regeneración, no sólo repetir una llamada al
compiler host:

```text
compiler.bf
    -> BFIR1 compiler image I1
    -> BFIR1 VM ejecuta compiler.bf
    -> compiler image I2
```

## Estado Actual

`tests/t_m7_uroboros_seed.zig` cierra únicamente el primer gate de
reproducibilidad:

```text
C0(source) = I1
C0(source) = I2
SHA256(I1) = SHA256(I2) = PASS
```

Esta semilla se llama **Quinepiler**: un compilador cuyo objetivo final es
regenerar su propia representación compilada, como una quine pero pasando por
una etapa de compilación.

Esto prueba que el compilador host y el formato BFIR1 son deterministas. No es
prueba de self-hosting: todavía no existe un `compiler.bf` que lea BF y emita
BFIR1 dentro de la VM.

## Gates Restantes

- `compiler.bf` debe ser un programa BF que lea fuente BF y emita BFIR1.
- `VM(I1, compiler.bf) = I2` debe producir una imagen idéntica.
- Los vectores independientes deben comparar output, input consumido, cinta,
  puntero, terminación, pasos y checkpoints de traza.
- Sólo después se puede probar `BFIR1 -> Malbolge` y cerrar el ciclo externo.

El self-hosting no se infiere de que dos ejecuciones del compilador Zig
produzcan bytes iguales.

MBIR de `MALBOLGE-MB-DATABASE` queda únicamente como referencia externa para
comparar decisiones de ABI y transporte. El backend oficial de este proyecto
continúa siendo directo desde `BFIR1` a Malbolge Free.
