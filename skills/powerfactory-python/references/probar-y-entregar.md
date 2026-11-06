# Probar fuera de PF y entregar un script

Se lee antes de probar con el PowerFactory simulado y antes de entregar un script que escribe en el modelo. Viene de `SKILL.md` de powerfactory-python (fase 2 del plan de uso eficiente); el contenido no cambió.

## Probar fuera de PowerFactory

Antes de entregar un script que escribe en el modelo, pruébalo con el PF simulado:

```python
import sys; sys.path.insert(0, r"<skill>/scripts")
from run_with_fake import run_script
import fake_powerfactory as pf
prj = pf.build_project()
typ = pf.Obj("TypLne", "Cu 250", prj.equip, sline=0.5)
line = pf.Obj("ElmLne", "A - B 66 kV", prj.grids[0], typ_id=typ)
pf.APP.calc_objects.append(line)
run_script("mi_script.py", replace={"USE_DIALOG = True": "USE_DIALOG = False"})
```

Casos a cubrir: dry run no modifica nada; aplicar produce los punteros y valores esperados y deja los
originales intactos; re-ejecutar detecta `ya aplicado`; un valor cambiado en PF se omite. Para la
ventana, se puede parchear `tk.Tk.mainloop` para rellenar campos y pulsar Ejecutar por código.

El simulado reproduce el comportamiento observado (identidad por ruta, registro en el stage, AddCopy
con hijos) pero **no valida la API real**: nombres de atributos, unidades o códigos de retorno solo se
confirman en PF. Dilo al entregar y sugiere una primera ejecución en Simular, idealmente sobre una
copia del proyecto.

## Al entregar un script

- Cabecera con qué hace, qué nunca toca y cómo usarlo (Simular → revisar reporte → Aplicar).
- Log legible por ítem (`[listo]`, `[ya aplicado]`, `[omitido] motivo`, `[aplicado]`, `[error]`) y
  resumen final con conteos.
- Lista breve para la primera ejecución real: qué mirar en el log, qué verificar en PF y qué supuestos
  de la API quedan por confirmar.
- Mantén el estilo del usuario: comentarios y mensajes en español, nombres de funciones descriptivos.
