"""Rutas comunes de las pruebas: el pack, las herramientas incluidas y un HOME temporal."""

import os
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCLUIDAS = os.path.join(RAIZ, "incluidas")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# Nada de lo que escriban las pruebas debe llegar a la carpeta de usuario real.
os.environ["HOME"] = os.environ["USERPROFILE"] = tempfile.mkdtemp(prefix="mantitools_home_")

for ruta in [os.path.join(INCLUIDAS, i, "scripts") for i in sorted(os.listdir(INCLUIDAS))] + \
        [os.path.join(RAIZ, "scripts"), RAIZ, os.path.dirname(os.path.abspath(__file__))]:
    if ruta not in sys.path:
        sys.path.insert(0, ruta)


def aplicacion():
    from PySide6 import QtWidgets
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
