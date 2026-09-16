# M6 — Turing Completeness

Estado: **PARTIAL / NOT_DEMONSTRATED**.

## Lo Que Ya Existe

`tests/t_turing_full.zig` ejecuta este flujo:

1. Interpreta un programa Brainfuck fijo que imprime `Hello World!`.
2. Pasa solamente esa salida finita al generador de Malbolge.
3. Ejecuta el programa generado.
4. Compara la salida.

Esto es un smoke test de generación y ejecución. No es un compilador
Brainfuck->Malbolge y no demuestra universalidad: el generador recibe la
salida ya calculada, no el programa Brainfuck ni sus estados.

La primera etapa del traductor ya está implementada en
`tests/bf_to_ir.zig`, incluyendo validación estructural de targets, y
`tests/bf_ir_vm.zig` ejecuta ese IR. Las pruebas
diferenciales cubren loops anidados, input/output, estado observable y límites
de no terminación. El backend IR->Malbolge todavía no existe.

## Gate Formal M6

Una de estas dos pruebas debe existir antes de marcar M6 como PASS:

- compilador BF->Malbolge que preserve cinta, loops, entrada, salida y
  terminación en una familia de programas; o
- intérprete BF/UTM escrito en Malbolge Free, ejecutado por el runtime
  canónico.

La alternativa conservadora es publicar sólo un claim heredado: `fixed` de
Malbolge Free coincide con Classic en el dominio probado. Esa equivalencia no
crea por sí sola una prueba nueva de completitud; sólo permite reutilizar una
prueba formal externa de Classic si se cita y reproduce adecuadamente.

## Acceptance Tests

El mínimo recomendado para un compilador real es:

- programa con loop que modifica varias celdas;
- programa con input y output dependientes del input;
- programa que no termina dentro del límite y conserva su estado observable;
- comparación de traza, no sólo de stdout final;
- dos implementaciones independientes o una prueba formal del traductor.

## Veredicto

```text
TURING_COMPLETENESS_NEW_CLAIM = NOT_DEMONSTRATED
OUTPUT_REPRODUCTION_SMOKE_TEST = PASS
CLASSIC_PARITY_SUPPORT = PASS (6/6 corpus)
BF_REFERENCE_INFRASTRUCTURE = PASS (2 tests)
BF_TO_IR = PASS (3 tests)
IR_DIFFERENTIAL_VM = PASS (3 tests)
IR_VALIDATION = PASS (1 corruption test)
IR_IMAGE_PAYLOAD = PASS (2 tests; versioned BFIR1 format)
BFIR1_VM = PASS (2 tests; image loader and differential execution)
HELLO_WORLD_ORACLE = PASS (direct BF vs own BFIR1 compiler/VM, trace-equivalent)
```
