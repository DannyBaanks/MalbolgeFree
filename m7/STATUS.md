# M7 — Quinepiler / Uroboros: estado implementación

## Artefacto actual

- `compiler.bf` (1519 chars, BF puro, sin comentarios): lee BF por `,`, clasifica
  cada byte a opcode (8 casos), cuenta `n` y emite la imagen BFIR1
  (`BFIR1` + count u32-le + 12-byte records).
- `gen.py`: generador (mini-ensamblador BF) + oráculo Python espejo de
  `bf_to_ir.zig` + `bf_ir_image.zig`.
- `check_read.py`: volcado de cinta para verificar el layout.

## Lo verificado (byte-exacto vs oráculo)

| caso | bracket-free | resultado |
|---|---|---|
| `""` | sí | match |
| `++` | sí | match |
| `+++.-.` | sí | match |
| `>+++<+>.>.` | sí | match |
| `,+ .`  | sí | match |
| `>>+<++.` | sí | match |
| `++++++[>++++++<-]>.` | no (brackets) | mismatch esperado |

El pipeline de lectura + clasificación + conteo + emisión del registro es
**byte-exacto** para cualquier programa sin brackets (todas las posiciones
`source_pos` y la codificación u32-le correctas).

## Hallazgo determinante (fuente: `src/malbolge_free.zig`)

- `TAPE_BASE` (op 75) pone a cero SOLO las celdas 1000..1255 (256).
- Fuera de ese rango, `cell()` devuelve el relleno perezoso `crazy` (no-cero).
- Por tanto la cinta BF usable y con cero-garantizado del backend es
  **exactamente 256 celdas**.

Consecuencia: un `compiler.bf` autocontenido real (~1500+ operadores) **no puede
auto-compilar su propio fuente** dentro del backend de 256 celdas. El gate
literal de Uroboros `VM(I1, compiler.bf) = I2` (self-hosting) es
**NOT_DEMONSTRATED por límite del contrato del VM**, no por el compilador.

## Pendiente

1. **Resolución de brackets** (nested) — el paso restante de `BF → BFIR1`
   completo. Necesita layout con huecos (stride-N) para disponer de scratch al
   escanear (en layout contiguo no hay celda libre adyacente a la cinta).
2. Verificación en 3 runtimes (intérprete directo, BFIR1 reference VM, backend
   Malbolge Free).
3. Decisión de alcance sobre self-hosting: requiere ampliar `TAPE_BASE`
   (cambio de contrato del VM) — decisión del usuario, marcada como tal.