"""Genera los PNG del estante «MantiTools» en ``icons/`` a partir de ``mantitools.iconos``.

Uso (fuera de Maya, con PySide6)::

    python herramientas/generar_iconos.py

Para cada herramienta y para la ventana central se escribe ``mantitools_<id>.png``
(32 px) y las versiones ``_150`` (48 px) y ``_200`` (64 px), que Maya usa en
pantallas de alta densidad.
"""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

TAMANOS = (("", 32), ("_150", 48), ("_200", 64))


def marcas():
    """{icono: color de su marca}: el de cada herramienta, apagado; el azul del pack para la central y la wiki."""
    from mantitools import herramientas as hr, iconos
    datos = {f.id: iconos.tono_marca(f.color) for f in hr.FICHAS}
    datos["centro"] = hr.ACENTO
    datos["wiki"] = hr.ACENTO
    return datos


def generar(carpeta=None):
    from mantitools.qt import QtWidgets
    from mantitools import iconos
    QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    carpeta = carpeta or os.path.join(RAIZ, "icons")
    if not os.path.isdir(carpeta):
        os.makedirs(carpeta)
    escritos = []
    for ident, marca in marcas().items():
        for sufijo, lado in TAMANOS:
            mapa = iconos.pixmap(ident, lado, fondo=iconos.FONDO, grosor=iconos.GROSOR_ESTANTE, marca=marca)
            ruta = os.path.join(carpeta, "mantitools_{}{}.png".format(ident, sufijo))
            if mapa is None or not mapa.save(ruta):
                raise SystemExit("No se pudo escribir {}".format(ruta))
            escritos.append(ruta)
    return escritos


if __name__ == "__main__":
    for ruta in generar():
        print(ruta)
