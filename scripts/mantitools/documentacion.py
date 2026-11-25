"""La documentación de MantiTools: una wiki en HTML dentro del pack (``docs/wiki``).

Son páginas estáticas que se abren en el navegador, sin conexión: el menú
MantiTools, el estante y la pestaña Ayuda llevan a ellas. Cada herramienta tiene
su página, ``docs/wiki/<id>.html``. Las páginas se generan con
``herramientas/generar_wiki.py`` a partir de los ``.md`` de la misma carpeta.
"""

import os

PORTADA = "index"


def carpeta():
    from mantitools import carga
    return os.path.join(carga.RAIZ, "docs", "wiki")


def ruta(pagina=PORTADA):
    """Ruta del HTML de ``pagina`` (``index``, ``instalar``, ``muro``…), o "" si no está."""
    archivo = os.path.join(carpeta(), pagina + ".html")
    return archivo if os.path.isfile(archivo) else ""


def pagina_de(ident):
    """Página de una herramienta (o de ``mantitools``): la suya si existe, si no la portada."""
    if ident and ident != "mantitools" and ruta(ident):
        return ident
    return PORTADA


def abrir(pagina=PORTADA):
    """Abre la página en el navegador. Devuelve False si la wiki no está en el pack."""
    archivo = ruta(pagina) or ruta(PORTADA)
    if not archivo:
        return False
    from mantitools.qt import QtCore, QtGui
    if not QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(archivo)):
        import webbrowser
        webbrowser.open(QtCore.QUrl.fromLocalFile(archivo).toString())
    return True
