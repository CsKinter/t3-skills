"""Lanza pf_bridge.py en modo LIMPIEZA: escritura libre sobre el proyecto activo (borrar, mover, renombrar, cambiar
horas de stages, cerrar diagramas), sin variation de sesión y con diario de cada llamada que modifica
(pf_bridge\\diario_limpieza_<fecha>.jsonl). Creado el 06-11-2026 a pedido del usuario para ordenar la BD.
Guardas: nada con "_secure" en la ruta; nunca Save() de escenarios. Puede ejecutarlo el agente desde un ComPython con
autorización del usuario para limpieza y el alcance acordado."""
import os

MODO_PUENTE = "limpieza"
_aqui = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else \
    r"C:\Users\vicen\.claude\skills\powerfactory-python\scripts"
_f = os.path.join(_aqui, "pf_bridge.py")
exec(compile(open(_f, encoding="utf-8").read(), _f, "exec"))
