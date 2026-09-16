# Guía: emisor propio de Malbolge Classic crudo

Genera Malbolge Classic real **sin LMAO, sin HeLL y sin `gen_init`**, y lo comprueba en
nuestros dos motores. Toda la salida es real, ejecutada el 2026-09-16.

## La idea en una línea

La celda 0 lleva `(` (valor 40), que decodifica a `MovD` en la posición 0 **y** vale 40:
la primera instrucción deja `d = 40`, así que **`d = c + 40`** el resto del tiempo. Una
operación en la posición `p` opera sobre la celda `40 + p`, y el acumulador A se arrastra.
Encadenar `Rot`/`Opr` es, directamente, sintetizar el byte.

## Emitir un byte

```powershell
cd tools
py raw_malbolge.py 10 -o nl.mb      # newline
py raw_malbolge.py 0xff -o ff.mb
```

Salida real del programa del newline (42 celdas):

```
(&aN…
```

## Comprobarlo

```powershell
py -c "import importlib.util,sys;sys.path.insert(0,'.');import raw_malbolge as rm; \
import pathlib; s=importlib.util.spec_from_file_location('m', r'../../MALBOLGE/malbolge.py'); \
m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(m.run(rm.emit_byte(10),b'',300000))"
```

```
('HALTED', 4, b'\n')
```

## Tests

```powershell
py -m unittest test_raw_malbolge -v
```

```
Ran 5 tests in 3.659s

OK
```

Cubren: muestra de bytes en el oráculo, los bytes del hueco (154..208) por la vía del
acumulador, que el objetivo **nunca se almacena**, el tamaño, y la **paridad con Zig**.

## Resultados medidos

| métrica | valor |
|---|---|
| cobertura | **256/256** bytes |
| oráculo Python | 256/256 |
| runner Zig | 256/256, pasos idénticos |
| tamaño | 42–118 celdas (media 60) |
| LMAO para un newline | 2,069 celdas, 1,803 pasos |

Somos ~34× más compactos porque no sintetizamos el data module genérico: colocamos
operandos ya válidos en carga y solo encadenamos rot/crazy.

## Los dos modelos

1. **Inline** (201/256): `Rot v` → `A := rot(v)`; `Opr v` → `A := crazy(A, v)`, cada
   operando en su celda fresca. Relleno de nops mueve cada operación hasta que su operando
   caiga en una celda donde sea válido en carga.
2. **Acumulador persistente** (los 55 restantes, 154..208): mantiene una celda ACC y la
   revisita **retrocediendo `d`** con un `MovD` cuyo puntero vale `ACC − 1`.

## Ojo con estas tres trampas

1. Una etiqueta como operando almacena su **dirección**, no su valor.
2. El puntero de retroceso debe ser válido en la celda donde `d` está **en ese momento**;
   por eso hay relleno de nops antes del `MovD`.
3. **`MovD` puede saltar hacia atrás** — sin eso, los bytes 164, 165, 193 y 194 no salen.


## Primer microprograma (M4)

Ya no sólo sintetizamos un byte: componemos una secuencia pequeña de comportamiento en
**un solo** programa. La API está en `tools/microprogram.py`:

```powershell
cd tools
py -c "import microprogram as mp; print(mp.emit_program([('out',0x48),('out',0x49),('out',0x0a),('halt',)]))"
```

### El microprograma compuesto

Descripción:

```python
[("out", 0x3e),        # '>'
 ("in",),              # lee un byte
 ("out_acc",),         # lo emite
 ("jmp", "done"),
 ("out", 0x58),        # 'X' inalcanzable (trampa)
 ("label", "done"),
 ("out", 0x0a),        # '
'
 ("halt",)]
```

Malbolge generado: 120 celdas, sha256 `6a9f04ff3f3b5dc5…`
(`evidence/M4_MICROPROGRAM_V0/examples/m4e_micro.mb`).

| entrada | salida | pasos | oráculo | Zig |
|---|---|---:|---|---|
| `A` | `>A
` | 14 | HALTED | idéntico |
| `` | `>
` | 14 | HALTED | idéntico |
| `ÿ` | `>ÿ
` | 14 | HALTED | idéntico |

El byte trampa `X` nunca aparece: el salto se ejecuta de verdad.

### Piezas demostradas

| pieza | ejemplo | celdas |
|---|---|---:|
| salida secuencial | `HI
` | 51 |
| entrada real | `IN;OUT;HALT` = `(taN` | 4 |
| estado y transformación | `IN` → `crazy(A,39)` → `OUT` | 43 |
| salto incondicional | `A`, salto, `X` inalcanzable, `B` → `AB` | 122 |
| compuesto | el de arriba | 120 |

Crecimiento: **+3 celdas y +3 pasos por byte** (lineal, sin explosión).

### Ojo: el invariante `d = c + 40` es LOCAL

Vale en el tramo lineal. Tras un `Jmp` la VM hace `c = mem[d]`, cifra la celda de
aterrizaje y sigue en `mem[d]+1`, así que el desplazamiento pasa a
`(d_del_jmp + 1) − destino` (medido: de `+40` a `−16`). Además el puntero del salto debe
ser imprimible, así que **los destinos viven entre 34 y 127**.

### Lo que sigue sin existir

Ramificación condicional, bucles, saltos hacia atrás, funciones, memoria general y
compilación de HeLL arbitrario. Nada de eso está demostrado.

## Qué falta

Esto emite **salida de bytes**, no el lenguaje HeLL completo (sin bucles, condicionales ni
entrada). Para programas HeLL arbitrarios sigue estando el pipeline híbrido
(`GUIA_HELL_HIBRIDO.md`).
