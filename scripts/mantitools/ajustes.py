"""Ajustes propios de MantiTools: idioma, herramientas activas y carpeta de clase.

Se guardan en ``<preferencias de Maya>/mantitools/ajustes.json``. Los ajustes de
cada herramienta siguen en su propio archivo (``<preferencias>/muro/ajustes.json``…):
la ventana central los lee y los escribe allí. No depende de Maya.
"""

import json
import os

_ARCHIVO = "ajustes.json"
IDIOMAS = ("es", "en")
DEFECTOS = {
    "idioma": "es",
    "activas": {},          # {"radial": False}: las que no aparecen están activas
    "carpeta_clase": "",
    "sueltas_desactivadas": [],  # .mod de herramientas sueltas que el instalador apartó
}


class Ajustes(object):
    def __init__(self, carpeta):
        self.carpeta = carpeta
        self.ruta = os.path.join(carpeta, _ARCHIVO) if carpeta else None
        self.datos = self._leer()

    def _leer(self):
        if not self.ruta:
            return {}
        try:
            with open(self.ruta, encoding="utf-8") as f:
                datos = json.load(f)
            return datos if isinstance(datos, dict) else {}
        except (OSError, ValueError):
            return {}

    def guardar(self):
        if not self.ruta:
            return
        try:
            os.makedirs(self.carpeta, exist_ok=True)
            temporal = self.ruta + ".tmp"
            with open(temporal, "w", encoding="utf-8") as f:
                json.dump(self.datos, f, ensure_ascii=False, indent=2)
            os.replace(temporal, self.ruta)
        except OSError:
            pass

    def __getitem__(self, clave):
        valor = self.datos.get(clave, DEFECTOS.get(clave))
        defecto = DEFECTOS.get(clave)
        if defecto is not None and not isinstance(valor, type(defecto)):
            return defecto
        return valor

    def __setitem__(self, clave, valor):
        self.datos[clave] = valor
        self.guardar()

    @property
    def idioma(self):
        valor = self["idioma"]
        return valor if valor in IDIOMAS else "es"

    def activa(self, ident):
        return bool(self["activas"].get(ident, True))

    def fijar_activa(self, ident, valor):
        activas = dict(self["activas"])
        if valor:
            activas.pop(ident, None)
        else:
            activas[ident] = False
        self["activas"] = activas
