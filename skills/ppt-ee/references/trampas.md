# Trampas conocidas de python-pptx y PowerPoint

Ya resueltas en `scripts/ee_pptx.py`. Se leen al depurar un problema raro de un deck o al escribir código que no pasa por la librería. Vienen de `SKILL.md` de ppt-ee (fase 2 del plan de uso eficiente); el contenido no cambió.

- **Nombres de lámina duplicados**: después de borrar y agregar láminas, python-pptx puede dejar dos `slideN.xml` y PowerPoint no abre el archivo. `guardar()` renumera en dos fases antes de guardar. No uses `prs.save()` directo.
- **Identidad de formas**: `slide.shapes` crea objetos nuevos cada vez; compara con `sh._element is otro._element`, nunca con `is` entre shapes (así se borró una figura del usuario).
- **Coma decimal en gráficos**: el formato numérico de las etiquetas sale con punto en esta máquina; la librería escribe cada etiqueta a mano con coma.
- **Imágenes entre presentaciones**: copiar el XML no basta, hay que llevar los archivos de imagen con nombre nuevo (`copiar_formas` lo hace). Los "Graphic" pegados son SVG; los recortes de Excel son EMF.
- **Gráficos borrados** dejan la parte colgando si no sueltas la relación; `quitar_formas` lo hace.
- **Conectores** copiados conservan referencias a ids viejos; `copiar_formas` las quita.
- **Tablas**: PowerPoint agranda la fila si el texto no cabe; después de cambiar textos largos, baja la altura de las demás filas para que la tabla no toque la franja.
- **Render con PowerPoint** a veces falla con "file not found" si otra instancia está cerrando; `render.py` reintenta.
- **La tabla de título** de la plantilla es `Tabla 15` (una celda, borde izquierdo naranjo de 3 pt, dos runs: fino + negrita). La librería la clona; no la dibujes a mano.
