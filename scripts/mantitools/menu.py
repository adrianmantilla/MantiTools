"""El menú «MantiTools» de la barra de Maya.

Arriba va un submenú por herramienta (lo crea cada herramienta con su propio
código, a través de su ``pack.py``, que pregunta aquí dónde ponerlo); abajo,
las órdenes del pack.
"""

from maya import cmds

import mantitools
from mantitools import herramientas as hr
from mantitools.i18n import t

MENU = "MantiToolsMenu"
SEPARADOR = "MantiToolsMenuSeparador"


def existe():
    return bool(cmds.menu(MENU, exists=True))


def lugar_para(ident):
    """Dónde va el submenú de ``ident``: {parent, insertAfter} o None si no hay menú MantiTools.

    Los submenús siguen el orden de ``herramientas.ORDEN`` aunque se creen en otro orden.
    """
    if not existe():
        return None
    from mantitools import carga
    if not carga.en_el_pack(ident):
        return None
    elementos = cmds.menu(MENU, query=True, itemArray=True) or []
    anterior = ""
    for otro in hr.ORDEN:
        if otro == ident:
            break
        nombre = hr.ficha(otro).menu
        if nombre in elementos:
            anterior = nombre
    return {"parent": MENU, "insertAfter": anterior}


def construir():
    """Crea (o rehace) el menú y pide a cada herramienta cargada que ponga su submenú."""
    if cmds.about(batch=True):
        return None
    quitar()
    cmds.menu(MENU, parent="MayaWindow", label="MantiTools", tearOff=True)
    cmds.menuItem(SEPARADOR, divider=True)
    cmds.menuItem(label=t("menu_centro"), command=lambda *_: _centro("herramientas"))
    cmds.menuItem(label=t("menu_ajustes"), command=lambda *_: _centro("ajustes"))
    cmds.menuItem(label=t("menu_ayuda"), command=lambda *_: _centro("ayuda"))
    cmds.menuItem(label=t("menu_wiki"), annotation=t("menu_wiki_ayuda"), command=lambda *_: _wiki())
    cmds.menuItem(divider=True)
    cmds.menuItem(label=t("menu_comprobar"), command=lambda *_: _comprobar())
    cmds.menuItem(label=t("menu_recrear_estante"), command=lambda *_: _recrear_estante())
    cmds.menuItem(label=t("menu_openpbr"), annotation=t("menu_openpbr_ayuda"),
                  command=lambda *_: _openpbr())
    cmds.menuItem(label=t("menu_acerca", version=mantitools.__version__), enable=False)
    from mantitools import carga
    for ficha in hr.FICHAS:
        if carga.cargada(ficha.id):
            poner_submenu(ficha)
    return MENU


def poner_submenu(ficha):
    """Llama a la función de menú de la herramienta: con MantiTools cargado, va dentro de este menú."""
    import importlib
    modulo, funcion = hr.separar(ficha.crear_menu)
    try:
        getattr(importlib.import_module(modulo), funcion)()
    except Exception as error:  # una herramienta rota no deja sin menú a las demás
        cmds.warning(t("aviso_menu", herramienta=ficha.nombre, error=error))


def quitar():
    if existe():
        cmds.deleteUI(MENU)


def _centro(pestana):
    from mantitools import centro
    centro.mostrar(pestana)


def _wiki(pagina="index"):
    from mantitools import wiki
    if wiki.abrir(pagina) is None:
        cmds.warning(t("wiki_no_hay"))


def _comprobar():
    from mantitools import comprobar
    comprobar.mostrar()


def _recrear_estante():
    from mantitools import estante
    estante.crear(forzar=True)


def _openpbr():
    from mantitools import acciones
    texto = acciones.resumen_openpbr(acciones.convertir_a_openpbr())
    print(texto)
    cmds.confirmDialog(title=t("menu_openpbr"), message=texto, button=[t("boton_aceptar")])
