# Scripts con ventana e intercambio con otras apps

Se lee al escribir un script con ventana de configuración (tkinter) o que intercambia paquetes JSON/CSV con otra app. Viene de `SKILL.md` de powerfactory-python (fase 2 del plan de uso eficiente); el contenido no cambió.

## Ventana de configuración (tkinter)

Los usuarios prefieren una ventana a editar constantes. tkinter funciona dentro de PF con estos cuidados:
- `if not getattr(sys, "argv", None): sys.argv = ["powerfactory"]` antes de `tk.Tk()` — el Python
  embebido de PF a veces no define `sys.argv` y Tk falla.
- `root.attributes("-topmost", True)`, `root.lift()`, `root.focus_force()` para que no quede detrás de PF.
- Ventana modal: `mainloop()`, y en Ejecutar/Cancelar `root.destroy()`; devolver `None` si se cancela
  y terminar el script sin hacer nada.
- Campos típicos: archivo de entrada con `filedialog` (prellenar con el más reciente de Descargas),
  fecha dd-mm-aaaa + hora/minuto con `ttk.Spinbox`, nombre de variation, modo **Simular / Aplicar**
  (Simular por defecto; Aplicar pide confirmación con `messagebox.askyesno` indicando cuántos cambios).
- Validar en la ventana (fecha, archivo legible) y mostrar un resumen del archivo cargado.
- Mantener una constante `USE_DIALOG = True` con valores de respaldo para correr sin ventana.

## Intercambio con otras apps

- JSON en UTF-8 con `ensure_ascii=False`; identificar cada objeto por `GetFullName()` y guardar también
  el nombre para mostrar. Incluir fecha de generación y un `schema_version` en los paquetes.
- CSV para Excel en español: separador `;`, coma decimal, `encoding="utf-8-sig"`.
- Los paquetes que el script aplica deben traer los valores esperados (para detectar cambios) y los
  nombres finales de los objetos (para que el dry run muestre exactamente lo que se creará).
