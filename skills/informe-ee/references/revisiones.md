# Revisiones numeradas y oficialización

Cómo se llevó el informe de Cumbres del Ñuble de la revisión 16 a la 35 y a su oficialización (26-10 a 05-11-2026).
Sustituye la regla antigua de «un solo archivo, sin versiones», que valía cuando el informe vivía sólo en Documentos.

## Dos archivos, dos reglas

- **Oficial**: el que ve el cliente o el supervisor (normalmente en OneDrive). No se edita. Se reemplaza sólo con
  aprobación explícita del usuario, respaldo previo y sin `~$…docx` abierto. El AGENTS.md del proyecto dice en qué
  carpeta se puede escribir.
- **Copia de trabajo**: local, numerada por revisión. Aquí se edita siempre.

## Una revisión

Cada iteración parte del **último guardado del usuario**, no de la revisión anterior del agente: él pudo editar a mano.
Lo que el revisor eliminó no se repone.

Carpeta `iteracion_NN\` con:

- `Informe - revisión NN.docx` y su `.pdf`.
- `LEEME - revisión NN.md`, de 5 a 10 líneas: de qué archivo parte y su hash, páginas, cómo se renderizó, qué cambió,
  hash del docx y del PDF.
- Si el cambio es masivo: `CAMBIOS - RNN.md` con antes, después y criterio de cada cambio, y un registro en JSON.

No se leen las iteraciones anteriores por rutina. Hacia atrás se sigue la cadena de LEEME.

## Verificación antes de dar por buena una revisión

1. Render con una instancia **propia** de Word (PID verificado como nuevo; nunca cerrar el Word del usuario): campos,
   índice, tablas de figuras y PDF.
2. Referencias cruzadas sin destinos rotos. Contarlas y comparar con la revisión anterior.
3. Validación OOXML del .docx.
4. Render de todas las páginas. En un cambio acotado, las páginas no tocadas deben quedar idénticas a la revisión
   anterior: comparar imagen a imagen detecta corrimientos que el diff de texto no ve.
5. Cifras, unidades y códigos protegidos: comprobar párrafo a párrafo que un reemplazo de texto no los alteró.
6. Tras un reemplazo masivo, revisar negritas y cursivas: un cambio de texto puede dejarlas cortadas a media palabra.
7. Lista de chequeo de contenido de `estudio-restricciones/references/informe.md` §6.

## Oficializar

1. Aprobación explícita del usuario para **esa** revisión. La aprobación de una no vale para la siguiente.
2. Respaldo del oficial vigente en una carpeta `respaldo\oficial_antes_RNN\`.
3. Copiar docx y PDF con el nombre oficial. Comprobar que los hashes del oficial son los de la revisión.
4. Comprobante en JSON y actualización del AGENTS.md del proyecto con la revisión vigente.
5. La revisión oficial anterior del cliente (RA, RB…) se conserva intacta.

## Revisión editorial con varios modelos

Para una pasada de prosa de todo el informe se usó la skill `council`: tres modelos, hasta cinco rondas, nota mínima
por cambio y por capítulo y ninguna objeción sustantiva. El texto aprobado no se edita después, para conservar
exactamente lo evaluado. Es caro: reservarlo para la revisión previa a una entrega.
