# Guía: bootstrap de síntesis de bytes (lmao-lite, clean-room)

Sintetizas cualquiera de 201 bytes desde constantes imprimibles, sin guardar el byte
objetivo, y lo compruebas en dos motores Malbolge. Toda la salida es real, ejecutada el
2026-09-13.

## La idea

Malbolge no deja poner cualquier valor en una celda al cargar. El bootstrap **construye**
el byte en ejecución con dos micro-ops, combinando constantes que sí son cargables
(imprimibles 33..126):

- `ROT v` → `A := rot(v)`
- `CRAZY v` → `A := crazy(A, v)`

Ninguna constante usada es el byte objetivo: se sintetiza, no se almacena. Esto es lo que
hace `gen_init` de LMAO; aquí lo hacemos nosotros para 201/256 bytes sin leer su código.

## Ver la receta de un byte

```powershell
cd tools
py hell_materialize.py --show-moves '\n\x80'
```

```
byte 10 (.): ['rotload 118']
byte 128 (.): ['rotload 85', 'combine 33', ...]
```

El newline (10) sale de `rot(118)=19722`, y `19722 mod 256 = 10`. Se guarda 118, no 10.

## Sintetizar, ensamblar y verificar

```powershell
py hell_materialize.py 'ISyCo' > isyco.hell
py lmao_bridge.py verify isyco.hell --expect 495379436f
```

```
PASS  oracle: HALTED steps=4055 output=b'ISyCo'
PASS  zig:    HALTED steps=4055 (== oracle: True)
BRIDGE_VERIFY=PASS
```

Bytes de control y altos también:

```powershell
py hell_materialize.py '\n\t\x07' > ctrl.hell
py lmao_bridge.py verify ctrl.hell --expect 0a0907        # PASS en ambos motores
```

## Barrido completo y tests

```powershell
cd ..\evidence\M2_BOOTSTRAP_REACH_V0
py run_inline_e2e.py        # 201/201 oráculo, 23/23 Zig, 0 violaciones -> INLINE_SYNTH_E2E = PASS
cd ..\..\tools
py -m unittest test_hell_materialize -v      # 9 tests
```

## Lo que todavía no

- **55 bytes: 154..208.** No salen con el modelo inline; necesitan una celda de trabajo
  persistente (rotar tras acumular). Medido y aislado; es el siguiente slice.
- **Las 5 constantes base** (C1=29524, C2, C20, C21) aún se materializarían con gen_init;
  aquí se evitan combinando solo imprimibles cargables.
- Mientras tanto, el pipeline híbrido (`GUIA_HELL_HIBRIDO.md`) cubre 256/256 vía LMAO.
