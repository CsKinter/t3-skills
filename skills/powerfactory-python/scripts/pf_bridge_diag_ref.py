"""Lanza pf_bridge.py en modo DIAGNÓSTICO REF (sin retiming).

Ejecutar este archivo desde un ComPython en PowerFactory, con la autorización acotada del usuario:
solo permite activar el Ref exacto 2608-BD-OP-COORD-DMAP (y volver al laboratorio), crear la copia
`Base SEN_SONDA_20261109` y ejecutar cálculos dentro de esa copia. NO llama PoliticaModificacion.abrir(),
NO crea variation/stage y NO llama SetStudyTime.
"""
import os

MODO_PUENTE = "diagnostico_ref"
_aqui = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else \
    r"C:\Users\vicen\.claude\skills\powerfactory-python\scripts"
_f = os.path.join(_aqui, "pf_bridge.py")
exec(compile(open(_f, encoding="utf-8").read(), _f, "exec"))
