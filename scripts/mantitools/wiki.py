"""La wiki de MantiTools: documentación completa del pack en HTML, sin conexión.

Está en ``docs/wiki`` (se genera con ``herramientas/generar_wiki.py``) y se abre en
el navegador desde «MantiTools → Documentación (wiki)», desde la pestaña Ayuda de la
ventana central y desde la página de cada herramienta. No depende de Maya.
"""

import os

from mantitools import herramientas as hr

CARPETA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                       "docs", "wiki")
INICIO = "index"


def ruta(pagina=INICIO):
    """Ruta del HTML de ``pagina`` («index», «trepadora»…), o None si no existe."""
    archivo = os.path.join(CARPETA, (pagina or INICIO) + ".html")
    return archivo if os.path.isfile(archivo) else None


def pagina_de(ident):
    """La página de la wiki de una herramienta (o la portada para «mantitools»)."""
    if ident in hr.ORDEN and ruta(ident):
        return ident
    return INICIO


def abrir(pagina=INICIO, seccion=None):
    """Abre la página en el navegador. Devuelve la ruta abierta, o None si no está la wiki."""
    archivo = ruta(pagina) or ruta(INICIO)
    if archivo is None:
        return None
    try:
        from mantitools.qt import QtCore, QtGui
        url = QtCore.QUrl.fromLocalFile(archivo)
        if seccion:
            url.setFragment(seccion)
        if QtGui.QDesktopServices.openUrl(url):
            return archivo
    except Exception:  # sin Qt (pruebas, mayapy sin interfaz): el navegador del sistema
        pass
    import webbrowser
    from urllib.parse import quote
    camino = archivo.replace(os.sep, "/")
    if not camino.startswith("/"):  # C:/… en Windows
        camino = "/" + camino
    webbrowser.open("file://" + quote(camino) + ("#" + seccion if seccion else ""))
    return archivo
