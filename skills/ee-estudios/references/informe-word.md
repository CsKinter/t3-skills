# Informe | Word, referencias y publicación

## Conservar la versión del usuario

**Verificación.** El documento más reciente guardado por el usuario es la fuente de trabajo. Antes de editar, registrar ruta, tamaño, fecha y hash; guardar una copia recuperable. Comparar el oficial nuevamente antes de reemplazarlo: la fecha por sí sola no detecta bien todas las sincronizaciones de OneDrive.

Aplicar cambios localizados. Un generador antiguo puede borrar modificaciones manuales de texto, formas, posiciones y estilos. No reconstruir capítulos completos por comodidad si el usuario los ha editado después. No sobrescribir contenido fuera del alcance autorizado.

Un archivo abierto puede permitir lectura y bloquear reemplazo. Para inspección, una copia mediante FileStream de solo lectura con FileShare.ReadWrite | FileShare.Delete puede funcionar en Windows. Verificar estabilidad de tamaño/fecha y validez ZIP de la copia; si cambia durante la lectura, reintentar. No operar, guardar ni cerrar la sesión Word de otra persona.

Solo son visibles cambios guardados y sincronizados; una copia local no demuestra autoría ni contiene necesariamente ediciones aún pendientes. No prometer seguimiento de modificaciones no guardadas.

El destino oficial depende de la instrucción del proyecto: OneDrive puede ser el destino autorizado. No convertir una preferencia antigua de trabajar localmente en una prohibición general. Preparar y verificar localmente antes de publicar. Si un bloqueo impide el reemplazo, pedir guardar/cerrar cuando sea realmente necesario.

## Referencias cruzadas reales

**Preferencia.** Referencias a figuras y tablas con solo etiqueta y número, enlazadas al destino mediante campos nativos de Word.

1. Identificar el caption real, incluidos campos STYLEREF/SEQ y separadores. No inferir toda la numeración a partir de texto plano concatenado.
2. Crear o reutilizar un marcador que cubra exclusivamente «Figura N» o «Tabla N», sin el título completo.
3. Insertar un campo REF con el nombre de marcador y el modificador de hipervínculo `\h`. Conservar estilo y espacios del texto que lo rodea.
4. En referencias plurales o rangos, conservar su gramática; pueden necesitar marcadores de solo número en los extremos.
5. Actualizar los campos pertinentes, guardar y verificar destino y resultado visible.

Preservar los REF existentes, en especial bibliografía. No anidar campos ni convertir otra vez una referencia ya vinculada. Auditar marcadores ausentes, identificadores duplicados, referencias sin destino y «Error! Reference source not found» o su equivalente local.

Word puede omitir captions dentro de grupos o cuadros de texto en GetCrossReferenceItems. Eso no impide referenciarlos mediante un marcador y REF. La actualización de referencias tampoco garantiza que la secuencia de captions se renumere correctamente entre todas las historias de Word.

Actualizar primero los captions que correspondan y después sus referencias. Ctrl+A/F9 en el cuerpo puede dejar fuera cuadros de texto y grupos. No actualizar indiscriminadamente todos los campos administrativos o de portada ni desbloquearlos sin necesidad. Verificar enlaces en el PDF además del resultado de los campos; un contador de Hyperlinks vacío no prueba por sí solo que un REF con `\h` esté roto.

## Particularidades OOXML y formas

- Al extraer texto, no sumar los párrafos de un cuadro de texto al texto de su párrafo contenedor. Evitar contar también mc:Fallback como contenido lógico nuevo.
- Reconocer separadores como w:noBreakHyphen: omitirlo puede transformar «Figura 6-19» en «Figura 619».
- Conservar relaciones, imágenes, estilos, campos, marcadores y propiedades de anclaje. Al reempaquetar un ZIP con ZipInfo, copiar sus metadatos antes de reutilizarlos para evitar efectos sobre offsets/CRC.
- En formas sin texto, un ajuste de texto `wrap="none"` en bodyPr puede hacer que Word reduzca el ancho previsto. Para cajas de resalte, revisar el ajuste, las dimensiones explícitas y el resultado tras guardar con Word; no atribuir toda deformación a las coordenadas.
- Evitar identificadores de formas y marcadores duplicados. Respetar las restricciones de tipo y rango de los identificadores.
- Un guardado de Word puede regenerar imágenes fallback aunque conserve las imágenes principales. Para comprobar que una figura no cambió, comparar relaciones e imágenes realmente usadas, geometría y render, no solo nombres de archivos internos.

## Verificación y entrega

Utilizar la skill de documentos o el flujo nativo de Word disponible para renderizar. Verificar el motor real que usará el entregable; no asumir que otro renderizador conserva igual los grupos y anclajes.

En automatización COM, crear una instancia propia si es necesario y cerrarla en finally. No matar procesos Word ni adjuntarse a la instancia del usuario para cerrarla. Exportar el PDF desde el mismo Word final que se entrega.

Comprobar estructura, referencias y páginas afectadas más las vecinas. Si una modificación puede redistribuir todo el documento, ampliar la revisión. Contrastar fuera de la sección editada para detectar pérdidas accidentales. Verificar que el Word publicado coincide con la copia aprobada y que el PDF corresponde a esa versión.
