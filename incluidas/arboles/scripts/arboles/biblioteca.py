"""Biblioteca en disco: árboles guardados (receta + miniatura) y ramas favoritas.

    <carpeta>/arboles/<nombre>.json     receta del árbol
    <carpeta>/miniaturas/<nombre>.png   miniatura
    <carpeta>/ramas/<nombre>.json       rama favorita con todo lo que cuelga de ella
    <carpeta>/hojas/<nombre>.json       hoja propia del alumno (malla normalizada, ver follaje.py)

No depende de Maya.
"""

import json
import os
import re

from arboles import ajustes
from arboles.arbol import Arbol


def nombre_de_archivo(nombre):
    """Nombre seguro para archivo en Windows y macOS (sin tildes ni símbolos raros)."""
    import unicodedata
    limpio = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode("ascii")
    limpio = re.sub(r"[^A-Za-z0-9_-]+", "_", limpio).strip("_")
    return limpio or "arbol"


def _escribir(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    temporal = ruta + ".tmp"
    with open(temporal, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    os.replace(temporal, ruta)


def _listar(carpeta):
    if not os.path.isdir(carpeta):
        return []
    return sorted(os.path.splitext(n)[0] for n in os.listdir(carpeta) if n.endswith(".json"))


class Biblioteca(object):
    def __init__(self, carpeta):
        self.carpeta = ajustes.preparar_biblioteca(carpeta)

    def ruta_arbol(self, nombre):
        return os.path.join(self.carpeta, "arboles", nombre_de_archivo(nombre) + ".json")

    def ruta_miniatura(self, nombre):
        return os.path.join(self.carpeta, "miniaturas", nombre_de_archivo(nombre) + ".png")

    def ruta_rama(self, nombre):
        return os.path.join(self.carpeta, "ramas", nombre_de_archivo(nombre) + ".json")

    # árboles
    def arboles(self):
        return _listar(os.path.join(self.carpeta, "arboles"))

    def existe(self, nombre):
        return os.path.isfile(self.ruta_arbol(nombre))

    def guardar(self, arbol):
        ruta = self.ruta_arbol(arbol.nombre)
        _escribir(ruta, arbol.a_dict())
        return ruta

    def cargar(self, nombre):
        with open(self.ruta_arbol(nombre), encoding="utf-8") as f:
            return Arbol.de_dict(json.load(f))

    # hojas propias
    def ruta_hoja(self, nombre):
        return os.path.join(self.carpeta, "hojas", nombre_de_archivo(nombre) + ".json")

    def hojas(self):
        return _listar(os.path.join(self.carpeta, "hojas"))

    def guardar_hoja(self, nombre, datos):
        """Guarda la hoja y la deja disponible; devuelve el tipo de follaje («propia:<nombre>»)."""
        from arboles import follaje
        nombre = nombre_de_archivo(nombre)
        _escribir(self.ruta_hoja(nombre), datos)
        return follaje.registrar_hoja(nombre, datos)

    def cargar_hojas(self):
        """Deja disponibles todas las hojas propias de la biblioteca; devuelve sus tipos de follaje."""
        from arboles import follaje
        tipos = []
        for nombre in self.hojas():
            try:
                with open(self.ruta_hoja(nombre), encoding="utf-8") as f:
                    tipos.append(follaje.registrar_hoja(nombre, json.load(f)))
            except (OSError, ValueError):
                pass  # una hoja estropeada no impide abrir el editor
        return tipos

    # ramas favoritas
    def ramas(self):
        return _listar(os.path.join(self.carpeta, "ramas"))

    def guardar_rama(self, nombre, subarbol):
        ruta = self.ruta_rama(nombre)
        _escribir(ruta, dict(subarbol, nombre=nombre))
        return ruta

    def cargar_rama(self, nombre):
        with open(self.ruta_rama(nombre), encoding="utf-8") as f:
            return json.load(f)
