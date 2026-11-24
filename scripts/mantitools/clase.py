"""Carpeta de clase: una sola carpeta del profesor para todas las herramientas. No depende de Maya.

Dentro, cada herramienta busca su subcarpeta (``radial/``, ``materials/``…) y,
si existe, un ``mantitools_clase.json`` con lo que el profesor fija para todo el
grupo::

    {
      "desactivar": ["radial"],
      "fijar": {
        "muro": {"abrir_con_escena": false},
        "materials": {"destino": "juego", "motor_juego": "unity"}
      }
    }

Lo fijado se aplica cada vez que arranca Maya y aparece con candado en Ajustes.
"""

import json
import os

ARCHIVO = "mantitools_clase.json"
# Herramientas que ya entienden una carpeta de clase propia: se les pasa su subcarpeta.
SUBCARPETAS = {"radial": "radial", "materials": "materials"}


def subcarpeta(raiz, ident):
    """La subcarpeta de ``ident`` dentro de la carpeta de clase (aunque aún no exista), o ""."""
    if not raiz or ident not in SUBCARPETAS:
        return ""
    return os.path.join(raiz, SUBCARPETAS[ident])


class Clase(object):
    """Lo que dice el ``mantitools_clase.json`` de una carpeta (vacío si no hay)."""

    def __init__(self, raiz=""):
        self.raiz = raiz or ""
        self.error = ""
        self.datos = self._leer()

    def _leer(self):
        if not self.raiz:
            return {}
        ruta = os.path.join(self.raiz, ARCHIVO)
        if not os.path.isfile(ruta):
            return {}
        try:
            with open(ruta, encoding="utf-8") as f:
                datos = json.load(f)
        except (OSError, ValueError) as error:
            self.error = "{}: {}".format(ARCHIVO, error)
            return {}
        if not isinstance(datos, dict):
            self.error = "{}: no es un objeto JSON".format(ARCHIVO)
            return {}
        return datos

    @property
    def existe(self):
        return bool(self.raiz) and os.path.isdir(self.raiz)

    @property
    def desactivadas(self):
        lista = self.datos.get("desactivar") or []
        return [x for x in lista if isinstance(x, str)]

    def fijadas(self, ident):
        """{clave: valor} que el profesor fija para ``ident``."""
        todas = self.datos.get("fijar") or {}
        propias = todas.get(ident) if isinstance(todas, dict) else None
        return dict(propias) if isinstance(propias, dict) else {}

    def bloqueada(self, ident, clave):
        return clave in self.fijadas(ident)
