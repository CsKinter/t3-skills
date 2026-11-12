# Puente full para adecuación y organización de PowerFactory

Fuente incorporada el 10-11-2026 desde `C:\Users\vicen\pf_full\pf_bridge_full.py` y `pf_full_send.py`, a petición de Vicente.
El transporte y la lógica se conservaron. Ambos scripts viven ahora en `scripts/` de esta skill; los enlaces de Codex,
Claude y Claude Work apuntan a la misma fuente `~/t3-skills/skills/powerfactory-python`.

## Cuándo usarlo

Usar este modo cuando el usuario autoriza acceso total para una tarea concreta: revisar/podar una copia, organizar
casos, escenarios y scripts, adecuar demanda, capacidades y obras, o calcular dentro de ese alcance. Registrar la
autorización en el proyecto. No vuelve a pedirse para cada cambio ya incluido; criterios técnicos nuevos se acuerdan aparte.
Para una consulta ordinaria sin esa autorización se conserva el puente de lectura.

`CONFIRMO_ACCESO_TOTAL` se conserva en `True`, como en la copia de Windows suministrada por el usuario. Ejecutar este
ComPython es el arranque del modo full autorizado. No arrancarlo por importar el módulo desde una herramienta externa.

## Arranque y comprobación

En el ComPython de PF, seleccionar el archivo de la skill:

```text
C:\Users\vicen\.codex\skills\powerfactory-python\scripts\pf_bridge_full.py
```

Los enlaces `.claude/skills` y la ruta canónica `t3-skills/skills` resuelven al mismo archivo. Mantener activo el
proyecto/caso de trabajo correcto y ejecutar el comando desde el Data Manager. Si el usuario indicó que lo arrancará,
darle la ruta y dejar preparado el primer inventario. Para conducir la GUI cuando corresponda, consultar
`arranque-puente-gui.md` usando este archivo como destino.

Cliente desde PowerShell:

```powershell
python C:\Users\vicen\.codex\skills\powerfactory-python\scripts\pf_full_send.py estado
python C:\Users\vicen\.codex\skills\powerfactory-python\scripts\pf_full_send.py ejecutar inventario.py --timeout 60 --json respuesta.json
python C:\Users\vicen\.codex\skills\powerfactory-python\scripts\pf_full_send.py auditoria -n 10
```

Exigir `modo=acceso_total`, `full_access=true`, latido reciente y una consulta real que confirme PID, proyecto, caso,
escenario y modificaciones sin guardar. El estado antiguo de otra sesión no acredita la actual. No enviar comandos de
Sidon a una base de Cumbres u otro proyecto: comparar identidad antes de actuar y en el propio script.

## Transporte y ejecución

- Directorio local: `%USERPROFILE%\pf_bridge_full`, configurable con `PF_BRIDGE_FULL_DIR` y `--dir` en el cliente.
- La API `app` es la de PF, sin envoltorio de lectura. Los comandos se ejecutan en el hilo del ComPython.
- El arranque lee contexto; no activa casos/escenarios, no crea variations, no guarda ni calcula por iniciativa propia.
- Cada comando aporta `resultado`; `guardar` permite exportar un resultado a `files/`. La respuesta está en `outbox/`;
  un resultado grande puede quedar en `files/`, indicado mediante `resultado_archivo`.
- `inbox/`, `en_curso/`, `ejecutados/`, `fallos/`, `duplicados/` y `descartados/` registran el ciclo. `auditoria.jsonl`
  registra fuente/hash y respuesta; no es una función de deshacer del modelo.
- Mantener un solo escritor en PF. Tiempo de inactividad: 60 min; duración máxima: 4 h en la versión incorporada.
- **`estado` muestra dos relojes distintos (confusión común, 11-11-2026).** `se_detiene_en_min` es la inactividad: se
  reinicia con cada comando procesado (`estado` no cuenta). `expira_en_min` es el tope de horas desde `inicio`
  (`max_hours`): **no se reinicia con actividad**; al llegar a 0 el puente termina con motivo «tope de horas» aunque se
  esté usando. Ambos se revisan **entre** comandos (`motivo_fin` antes de tomar el siguiente): un comando en curso no se
  corta, pero el siguiente ya no se procesa. Mientras un comando corre, `status.json` no se refresca (los minutos
  quedan congelados). Antes de un comando largo, comparar su duración con ambos relojes; si `expira_en_min` no alcanza,
  relanzar el puente antes (sesión nueva) en vez de esperar a que lo corte.
- El cliente devuelve códigos 0 (éxito), 1 (error del comando), 2 (no disponible/timeout) y 3 (uso inválido).

Un timeout del cliente **no cancela** la llamada de PF. Consultar estado y respuesta por el mismo ID antes de reintentar;
no reenviar la escritura con un ID distinto. Para recuperar un resultado existente:

```powershell
python C:\Users\vicen\.codex\skills\powerfactory-python\scripts\pf_full_send.py ejecutar comando.py --id ID_YA_ENVIADO
```

`detener` crea `inbox/STOP` y actúa entre comandos. No detiene con seguridad una llamada de la API que esté bloqueada.

## Poda y adecuación

1. Confirmar proyecto y copia de trabajo; respaldar/exportar antes de editar y registrar su procedencia/hash.
2. Inventariar carpetas, casos, escenarios, variations/stages, hora activa y estado de despacho.
3. Preparar movimientos con rutas y destinos concretos; lo histórico va a `99_Respaldo`, sin borrar ni duplicar inyecciones.
4. Respetar qué cambios viven en red y cuáles en biblioteca. El acceso full no vuelve reversibles los cambios de Library.
5. Releer cambios y comparar antes/después: contexto, escenarios activos, despacho y resultados pertinentes.

La operación full admite organización directa autorizada; no forzar una variation para registrar un movimiento que no
se registra allí. Conservar un plan/mapeo de rutas y el respaldo que permitan restaurar. Un movimiento de la carpeta activa
puede afectar referencias o contexto: comprobarlo en la API real antes de encadenar operaciones.

## Validación de la incorporación

Se prueba el transporte en un directorio temporal, con aplicación simulada: arranque sin mutación, ejecución y respuesta,
recuperación por ID, error y STOP. Esto no valida clases, atributos, movimientos ni cálculo de la API real de PF.
La validación real empieza con identidad/inventario en la copia abierta del estudio.

Validación real adicional en PF 2025 (10-11-2026): identidad/inventario, `IntPrj.CreateVersion`, copia de semillas,
movimientos de contenedores y `WriteChangesToDb`. PF rechazó con retorno 1 el movimiento de una carpeta que contenía
el caso activo. Se crearon y activaron copias de preparación antes de archivar el origen; `destino.Move(origen)` es
la dirección documentada de la API. Conservar el ComPython que ejecuta el puente mientras la sesión está abierta.
Se compararon parámetros seleccionados entre origen y semilla al volver a activarlos, sin flujo. Los avisos de
referencias inválidas/eliminadas al activar casos deben registrarse y revisarse; un comando exitoso no valida convergencia.
