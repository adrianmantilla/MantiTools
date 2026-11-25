"""Dibuja el estante MantiTools para la wiki y el README, a doble resolución.

Uso (fuera de Maya, con PySide6)::

    python herramientas/imagen_estante.py

Escribe ``docs/wiki/img/mantitools/estante.png`` (solo los iconos) y
``estante_grupos.png`` (con el nombre de cada grupo debajo), con los mismos iconos,
grupos y separadores que el estante de Maya, incluidos MantiTools y la Wiki.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
SALIDA = os.path.join(RAIZ, "docs", "wiki", "img", "mantitools")

NOMBRES = {"empezar": "Empezar", "construir": "Construir", "look": "Materiales, luz y render",
           "a_mano": "Siempre a mano", "pack": "Ventana y wiki"}


def dibujar(nombre, con_grupos):
    from mantitools.qt import QtCore, QtGui, QtWidgets
    from mantitools import herramientas as hr, iconos
    QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    escala, lado, hueco, sep, margen = 2, 46, 8, 22, 12
    marcas = {f.id: iconos.tono_marca(f.color) for f in hr.FICHAS}
    marcas.update(centro=hr.ACENTO, wiki=hr.ACENTO)
    grupos = [(g, list(ids)) for g, ids in hr.GRUPOS] + [("pack", ["centro", "wiki"])]
    fuente = QtGui.QFont()
    fuente.setPixelSize(13)
    metrica = QtGui.QFontMetricsF(fuente)
    anchos = []
    for g, ids in grupos:
        ancho = len(ids) * lado + (len(ids) - 1) * hueco
        if con_grupos:
            ancho = max(ancho, metrica.horizontalAdvance(NOMBRES[g]))
        anchos.append(ancho)
    ancho_total = int(2 * margen + sum(anchos) + (len(grupos) - 1) * sep)
    alto = lado + 20 + (34 if con_grupos else 0)
    imagen = QtGui.QImage(ancho_total * escala, alto * escala, QtGui.QImage.Format_ARGB32)
    imagen.fill(QtGui.QColor("#444444"))
    p = QtGui.QPainter(imagen)
    p.setRenderHint(QtGui.QPainter.Antialiasing)
    p.setRenderHint(QtGui.QPainter.TextAntialiasing)
    p.scale(escala, escala)
    p.setFont(fuente)
    x = margen
    for i, ((g, ids), ancho) in enumerate(zip(grupos, anchos)):
        iconos_ancho = len(ids) * lado + (len(ids) - 1) * hueco
        ix = x + (ancho - iconos_ancho) / 2
        for ident in ids:
            mapa = iconos.pixmap(ident, lado * escala, fondo=iconos.FONDO, grosor=iconos.GROSOR_ESTANTE,
                                 marca=marcas[ident])
            p.drawPixmap(QtCore.QRectF(ix, 10, lado, lado), mapa, QtCore.QRectF(mapa.rect()))
            ix += lado + hueco
        if con_grupos:
            p.setPen(QtGui.QColor("#c8c8c8"))
            p.drawText(QtCore.QRectF(x - 10, lado + 22, ancho + 20, 24), QtCore.Qt.AlignCenter, NOMBRES[g])
        x += ancho
        if i < len(grupos) - 1:
            p.setPen(QtGui.QPen(QtGui.QColor("#6a6a6a"), 1.2))
            p.drawLine(QtCore.QPointF(x + sep / 2, 16), QtCore.QPointF(x + sep / 2, lado + 4))
            x += sep
    p.end()
    os.makedirs(SALIDA, exist_ok=True)
    ruta = os.path.join(SALIDA, nombre)
    imagen.save(ruta)
    return ruta


if __name__ == "__main__":
    print(dibujar("estante.png", False))
    print(dibujar("estante_grupos.png", True))
