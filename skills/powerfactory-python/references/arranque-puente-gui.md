# Abrir proyecto y arrancar el puente por GUI

Procedimiento comprobado el 05-11-2026 en PowerFactory 2025, Windows, con el usuario fuera del PC.
Usarlo para **abrir el proyecto solicitado y arrancar el puente en el modo autorizado**: lectura por defecto;
modificación o limpieza sólo si el usuario autorizó ese modo y alcance. El lanzador elegido determina el modo:
`pf_bridge.py`, `pf_bridge_modificar.py` o `pf_bridge_limpieza.py` (nombres verificados en `scripts/`). Arrancar no
autoriza cambios de planta fuera del alcance acordado.

## Autorización y elección de interfaz

- El usuario puede autorizar al agente a abrir PF, cambiar de proyecto y arrancar el puente en un modo concreto
  (lectura, modificación o limpieza). Esa autorización cubre el proyecto y el alcance acordados; conservarla durante la
  tarea y no volver a exigir que lo haga personalmente por una instrucción histórica de la skill/AGENTS. Si no hay
  autorización, preguntar modo y alcance antes de arrancar; no elevar a otro modo por iniciativa propia.
- Preferir Computer Use cuando funciona y seguir sus instrucciones. El error `Computer Use native pipe is unavailable
  ... (os error 2)` indica que esa interfaz no pudo conectar con su helper; no demuestra que PowerFactory haya fallado.
- La ruta PowerShell de esta referencia es independiente del helper. Usarla cuando el usuario pida expresamente ese
  método y las instrucciones vigentes lo permitan. El usuario la autorizó así en la sesión verificada: «use glms route!
  i have no access to the pc». Esta evidencia histórica no concede permiso para otras tareas.
- No cambiar permisos, seguridad del puente ni configuración del sistema para conseguir el arranque. Si aparece un
  aviso de seguridad, guardar/descartar cambios ajenos, autenticación o escritorio bloqueado, detenerse y resolverlo
  con el usuario; la autorización para abrir el proyecto no decide cómo tratar cambios pendientes de otro estudio.

## Herramientas persistentes

La fuente compartida en este PC es `C:\Users\vicen\.claude\skills\powerfactory-python`; la ruta de Codex es una junction
a esa carpeta. No depender de `AppData\Local\Temp\opencode\ps_accion.ps1`: era el helper temporal de GLM y tenía el
título de ViQSilent fijado. La versión reutilizable es `scripts/pf_ui.ps1`, que recibe el PID observado y verifica el
proceso en primer plano antes de enviar entrada. Los nombres de proyecto y las coordenadas se obtienen de nuevo.

Ejemplos PowerShell, **una captura observada antes de elegir cada acción**:

```powershell
# Identificar la instancia; si hay varias, elegir por título/proyecto, no la primera.
Get-Process -Name PowerFactory | Select-Object Id, MainWindowTitle

# Sustituir 12345 por el PID recién observado. None no manda entrada.
powershell -ExecutionPolicy Bypass -File C:\Users\vicen\.claude\skills\powerfactory-python\scripts\pf_ui.ps1 -TargetPid 12345 -Action none

powershell -ExecutionPolicy Bypass -File C:\Users\vicen\.claude\skills\powerfactory-python\scripts\captura_escritorio.ps1 -Salida C:\Users\vicen\pf_bridge\capturas\arranque.png
# Abrir la imagen con view_image. Mantener escala 1 para leer y obtener coordenadas.

# Ejemplos: X/Y deben venir de esa captura, en coordenadas absolutas de Windows.
powershell -ExecutionPolicy Bypass -File C:\Users\vicen\.claude\skills\powerfactory-python\scripts\pf_ui.ps1 -TargetPid 12345 -Action click -X 900 -Y 345
Set-Clipboard -Value 'C:\Users\vicen\.claude\skills\powerfactory-python\scripts\pf_bridge.py'
powershell -ExecutionPolicy Bypass -File C:\Users\vicen\.claude\skills\powerfactory-python\scripts\pf_ui.ps1 -TargetPid 12345 -Action key -Key '^v'
```

El helper admite `click`, `dclick`, `rclick` y `key` (sintaxis `System.Windows.Forms.SendKeys`, p. ej. `^a`, `^v`,
`{ENTER}`, `{ESC}`, `{PGDN}`). Las rutas y nombres con Ñ/tildes se pegan con `Set-Clipboard` + Ctrl+V, tras observar
el foco. Esto reemplaza el portapapeles. No usar SendKeys para texto arbitrario con caracteres especiales.
Si se recorta/reescala la captura, convertir las coordenadas a las del escritorio original; nunca copiar sin esa
conversión las coordenadas de la imagen reducida. No reutilizar las de esta sesión como receta automática.

## Secuencia de arranque

1. Consultar `python scripts/pf_send.py estado` y el título del proceso. Si ya está vivo en el proyecto correcto,
   verificar identidad por el puente y terminar. Si está vivo en otro proyecto, no arrancar una segunda sesión;
   coordinar su cierre antes del cambio. Si PF no está abierto, abrir su ejecutable instalado sólo dentro del alcance
   autorizado; la sesión comprobada empezó con PF abierto, no probó un arranque desde cero.
2. Capturar el escritorio y cerrar sólo selectores/diálogos identificados que impidan navegar. En esta sesión quedó
   abierto `Please Select 'DPL Command/Python Script' - All scripts`: se cerró con **Cancel**, no ejecutando lo seleccionado.
3. En Data Manager, usar la barra de ruta para ir al proyecto conocido. Pegar la ruta completa y Enter evita recorrer
   miles de objetos. Si hay que cambiar de proyecto, hacerlo desde el proyecto identificado en el árbol y comprobar
   el nuevo título; el caso real ya había llegado al proyecto Cumbres cuando Codex retomó.
4. Navegar al caso activo que se conservará. El caso comprobado fue:
   `vicen\Estudios\[ER] PE Cumbres del Ñuble\EE-ES-2026-2442-RA_Anexo I – BD_EE\Study Cases\00_PE Cumbres del Ñuble\POI 2 - Buli\03_15 SS`.
   **Es evidencia, no el caso obligatorio para un nuevo trabajo.** El nombre contiene un guion largo `–` en `Anexo I – BD_EE`;
   copiar el nombre observado, no reconstruirlo con `-`.
5. Reutilizar el ComPython de lectura si existe y comprobar su archivo. Si no existe, crear **New Object → Python Script**
   dentro del caso (no en Network Data). En la sesión se creó `Puente PF lectura`:
   - `Basic Options → Name`: `Puente PF lectura`.
   - `Script → External → Script file`: `C:\Users\vicen\.claude\skills\powerfactory-python\scripts\pf_bridge.py`.
   - Conservar Interface Version 2 (valor mostrado). En un arranque de lectura, no seleccionar `pf_bridge_modificar.py`
     ni `pf_bridge_limpieza.py` ni editar el script. Si el usuario autorizó modificación o limpieza, apuntar el ComPython
     al lanzador correspondiente (`pf_bridge_modificar.py` / `pf_bridge_limpieza.py`).
6. Cerrar el editor guardando su configuración y salir de los cuadros anidados de propiedades/Contents hasta el
   **Data Manager principal**. El primer Execute desde el editor anidado no levantó el puente; el estado seguía detenido.
   No considerar ese clic como éxito. En tablas, doble clic en el **nombre** puede editarlo; usar el icono para abrir
   carpetas y cancelar ediciones accidentales con Escape.
7. Localizar el objeto guardado desde la barra de ruta, añadiendo `\Puente PF lectura` a la ruta del caso. Eso muestra
   sus contenidos vacíos y lo selecciona en el árbol izquierdo: es normal. **Clic derecho en el ComPython del árbol →
   Execute**. En la sesión ésta fue la acción que arrancó el puente. Distinguir `Execute` de `Execute Script...`.
8. Capturar/leer la salida y verificar por consola como sigue. Cuando PF entra en `NON-INTERACTIVE MODE` queda ocupado
   y puede no repintar: es esperado mientras corre el puente. No seguir enviando clics para comprobar su actividad.

## Verificación obligatoria y cierre

```powershell
python C:\Users\vicen\.claude\skills\powerfactory-python\scripts\pf_send.py estado
python C:\Users\vicen\.claude\skills\powerfactory-python\scripts\pf_send.py -c "resultado = {'proyecto': app.GetActiveProject().GetFullName(), 'caso': app.GetActiveStudyCase().GetFullName(), 'escenario': app.GetActiveScenario().GetFullName() if app.GetActiveScenario() else None}"
```

Exigir `vivo: true`, latido reciente, PID esperado, proyecto/caso correctos y una consulta real con resultado `ok`.
En el arranque de lectura, además `modo: solo lectura` y `allow_calc: false`; si el usuario autorizó modificación o
limpieza, exigir el modo esperado (`modificación`/`limpieza`), donde el cálculo lo gobierna la política de ese modo y no
`allow_calc`. En la sesión: PID 12676, inicio 05-11-2026 12:50:09, Bulí/03_15 SS,
escenario `2_Base_Restringido\E03_VES_DA_15_BESS-D`, `escenario_modificado: false`; consulta de identidad en 0,34 s.
La salida de PF mostró `Puente Claude activo ... (modo solo lectura)`.

Si sigue detenido, inspeccionar una captura nueva y la salida de PF antes de otro intento; no enviar consultas en
bucle ni declarar éxito porque cerró un diálogo. Si aparece error de script, diagnosticarlo sin debilitar sus controles.
No arrancar otra instancia de PF para intentar conectar con la abierta.

Informar proyecto, caso, escenario y modo, y registrar el ComPython creado y la comprobación en la bitácora del
proyecto. No afirmar que no se escribió nada: crear/configurar el comando sí añade un objeto al caso; en el arranque
verificado no se cambiaron parámetros de red, despacho ni informe. El puente conserva 120 min de inactividad y 8 h de
sesión en la versión comprobada; estos límites se leen del script/estado, no se cambian para este procedimiento.
