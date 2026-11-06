"""Lanza pf_bridge.py en modo MODIFICACIÓN (variation "Claude_revisar_<fecha>", copias "_revisar", diario y deshacer).
Ejecutar este archivo desde un ComPython en PowerFactory. Ver la cabecera de pf_bridge.py."""
import os

MODO_PUENTE = "modificacion"
_aqui = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else \
    r"C:\Users\vicen\.claude\skills\powerfactory-python\scripts"
_f = os.path.join(_aqui, "pf_bridge.py")
exec(compile(open(_f, encoding="utf-8").read(), _f, "exec"))
