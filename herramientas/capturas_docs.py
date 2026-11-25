"""Capturas de MantiTools para el README y la wiki, a doble resolución (``docs/capturas``).

Uso (fuera de Maya, con PySide6)::

    python herramientas/capturas_docs.py

Dibuja la ventana central con un Maya falso (el de las pruebas) y guarda:

- ``centro_herramientas.png``, ``centro_ajustes.png`` (General) y ``centro_ayuda.png``;
- ``ajustes_<id>.png``: la página de Ajustes de cada herramienta;
- ``estante.png``: el estante MantiTools, con sus separadores;
- ``centro.gif``: un recorrido por las pestañas.
"""

import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["QT_SCALE_FACTOR"] = "2"

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "docs", "capturas")
sys.path.insert(0, os.path.join(RAIZ, "tests"))
import comun  # noqa: E402
import maya_falso  # noqa: E402

ANCHO, ALTO = 900, 790


def _esperar(app, veces=4):
    for _ in range(veces):
        app.processEvents()


def ventana(app):
    from mantitools import centro
    v = centro.VentanaCentro()
    v.resize(ANCHO, ALTO)
    v.show()
    _esperar(app)
    return v


def foto(app, widget, nombre):
    _esperar(app)
    imagen = widget.grab().toImage()
    imagen.save(os.path.join(SALIDA, nombre))
    return imagen


def estante(nombre="estante.png"):
    """El estante dibujado como en Maya: botones grises sobre la barra, separadores entre grupos."""
    from mantitools.qt import QtCore, QtGui
    from mantitools import herramientas as hr, iconos
    escala, lado, hueco, sep = 2, 46, 8, 18
    marcas = {f.id: iconos.tono_marca(f.color) for f in hr.FICHAS}
    marcas.update(centro=hr.ACENTO, wiki=hr.ACENTO)
    grupos = [list(ids) for _g, ids in hr.GRUPOS] + [["centro", "wiki"]]
    ancho = 12 * 2 + sum(len(g) * lado + (len(g) - 1) * hueco for g in grupos) + (len(grupos) - 1) * sep
    alto = lado + 20
    imagen = QtGui.QImage(ancho * escala, alto * escala, QtGui.QImage.Format_ARGB32)
    imagen.fill(QtGui.QColor("#444444"))
    p = QtGui.QPainter(imagen)
    p.setRenderHint(QtGui.QPainter.Antialiasing)
    p.scale(escala, escala)
    x = 12
    for i, grupo in enumerate(grupos):
        for j, ident in enumerate(grupo):
            mapa = iconos.pixmap(ident, lado * escala, fondo=iconos.FONDO, grosor=iconos.GROSOR_ESTANTE,
                                 marca=marcas[ident])
            p.drawPixmap(QtCore.QRectF(x, 10, lado, lado), mapa, QtCore.QRectF(mapa.rect()))
            x += lado + (hueco if j < len(grupo) - 1 else 0)
        if i < len(grupos) - 1:
            p.setPen(QtGui.QPen(QtGui.QColor("#6a6a6a"), 1.2))
            p.drawLine(QtCore.QPointF(x + sep / 2, 16), QtCore.QPointF(x + sep / 2, alto - 16))
            x += sep
    p.end()
    imagen.save(os.path.join(SALIDA, nombre))


def gif(fotos, nombre="centro.gif", duracion=1600):
    """Junta las capturas en un GIF (a resolución normal, para que pese poco)."""
    from PIL import Image
    marcos = []
    for ruta in fotos:
        im = Image.open(ruta).convert("RGB")
        im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
        marcos.append(im.quantize(colors=128, method=Image.MEDIANCUT, dither=Image.NONE))
    marcos[0].save(os.path.join(SALIDA, nombre), save_all=True, append_images=marcos[1:], duration=duracion,
                   loop=0, optimize=True)


def generar():
    os.makedirs(SALIDA, exist_ok=True)
    app = comun.aplicacion()
    maya_falso.instalar()
    from mantitools import carga, herramientas as hr
    carga.iniciar()
    v = ventana(app)
    hechas = []

    def guardar(nombre):
        foto(app, v, nombre)
        hechas.append(os.path.join(SALIDA, nombre))

    v.ir_a("herramientas")
    guardar("centro_herramientas.png")
    v.ir_a_ajustes("general")
    guardar("centro_ajustes.png")
    for f in hr.FICHAS:
        v.ir_a_ajustes(f.id)
        guardar("ajustes_{}.png".format(f.id))
    v.ir_a("ayuda")
    guardar("centro_ayuda.png")
    estante()
    recorrido = ["centro_herramientas.png", "centro_ajustes.png", "ajustes_muro.png", "ajustes_materials.png",
                 "ajustes_lightmanager.png", "ajustes_renderdesk.png", "ajustes_simplesave.png", "centro_ayuda.png"]
    gif([os.path.join(SALIDA, n) for n in recorrido])
    v.close()
    return hechas + [os.path.join(SALIDA, "estante.png"), os.path.join(SALIDA, "centro.gif")]


if __name__ == "__main__":
    for ruta in generar():
        print(os.path.relpath(ruta, RAIZ))
