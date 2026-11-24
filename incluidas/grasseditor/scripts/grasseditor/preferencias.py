"""Preferencias de GrassEditor que no van en la escena.

Se guardan en ``<preferencias de Maya>/grasseditor/ajustes.json`` y se pueden
cambiar en MantiTools › Ajustes › GrassEditor:

* ``render_automatico``: pasar la hierba a calidad de render al renderizar
  (se añaden los MEL de antes y después del render al crear una capa).
* ``tipo_inicial`` y ``densidad_inicial``: con qué empieza una capa nueva.

Lo de cada capa (mezcla, densidad, reglas…) sigue guardado en la capa.
"""

import json
import os

_ARCHIVO = "ajustes.json"
DEFECTOS = {"render_automatico": True, "tipo_inicial": "silvestre", "densidad_inicial": 100}
LIMITES = {"densidad_inicial": (10, 300)}


def carpeta():
    from maya import cmds
    return os.path.join(cmds.internalVar(userAppDir=True), "grasseditor")


def _ruta(base=None):
    return os.path.join(base or carpeta(), _ARCHIVO)


def _todas(base=None):
    try:
        with open(_ruta(base), encoding="utf-8") as f:
            datos = json.load(f)
        return datos if isinstance(datos, dict) else {}
    except (OSError, ValueError):
        return {}


def leer(clave, base=None):
    """El valor guardado de ``clave``, o el de serie si falta o no vale."""
    defecto = DEFECTOS[clave]
    valor = _todas(base).get(clave, defecto)
    if isinstance(defecto, bool):
        return valor if isinstance(valor, bool) else defecto
    if isinstance(defecto, int):
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            return defecto
        minimo, maximo = LIMITES.get(clave, (valor, valor))
        return int(max(minimo, min(maximo, valor)))
    if clave == "tipo_inicial":
        from grasseditor import tipos
        return valor if valor in tipos.SERIE else defecto
    return valor


def escribir(clave, valor, base=None):
    if clave not in DEFECTOS:
        raise KeyError(clave)
    datos = _todas(base)
    datos[clave] = valor
    ruta = _ruta(base)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    temporal = ruta + ".tmp"
    with open(temporal, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    os.replace(temporal, ruta)
