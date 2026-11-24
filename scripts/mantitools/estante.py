"""El estante «MantiTools»: un icono por herramienta activa y otro para la ventana central.

Clic: la orden principal de la herramienta. Clic derecho: sus órdenes secundarias.
Se guarda al momento (Maya solo guarda los estantes al salir bien).
"""

import os

from maya import cmds, mel

from mantitools import herramientas as hr
from mantitools.acciones import codigo_estante
from mantitools.i18n import t

ESTANTE = "MantiTools"
CODIGO_CENTRO = "import mantitools.centro as _c\n_c.mostrar()"


def botones():
    """Lo que lleva el estante, como datos: [(etiqueta, ayuda, icono, orden, [(texto, orden), ...]), ...]."""
    from mantitools import carga
    lista = []
    for ficha in hr.FICHAS:
        if not carga.activa(ficha.id):
            continue
        principal = ficha.accion(ficha.principal)
        menu = [(t(ficha.texto(a.clave)), codigo_estante(ficha.id, a.clave)) for a in ficha.secundarias]
        ayuda = "{}: {}".format(ficha.nombre, t(ficha.texto(principal.clave)))
        lista.append((ficha.nombre, ayuda, ficha.icono, codigo_estante(ficha.id, principal.clave), menu))
    menu_centro = [(t("menu_ajustes"), "import mantitools.centro as _c\n_c.mostrar('ajustes')"),
                   (t("menu_ayuda"), "import mantitools.centro as _c\n_c.mostrar('ayuda')"),
                   (t("menu_comprobar"), "import mantitools.comprobar as _c\n_c.mostrar()")]
    lista.append(("MantiTools", t("estante_centro"), "mantitools_centro.png", CODIGO_CENTRO, menu_centro))
    return lista


def existe():
    return bool(cmds.shelfLayout(ESTANTE, exists=True))


def crear(forzar=False, seleccionar=False):
    """Crea el estante si falta; con ``forzar`` lo rehace aunque exista."""
    if cmds.about(batch=True):
        return None
    padre = mel.eval("$tmp = $gShelfTopLevel")
    if existe():
        if not forzar:
            return ESTANTE
        for boton in cmds.shelfLayout(ESTANTE, query=True, childArray=True) or []:
            cmds.deleteUI(boton)
    else:
        mel.eval('addNewShelfTab "{}"'.format(ESTANTE))
    for etiqueta, ayuda, icono, orden, menu in botones():
        opciones = {}
        if menu:
            opciones["menuItem"] = [(texto, codigo) for texto, codigo in menu]
            opciones["menuItemPython"] = list(range(len(menu)))
        cmds.shelfButton(parent=ESTANTE, label=etiqueta, annotation=ayuda, image=icono, image1=icono,
                         imageOverlayLabel="", command=orden, sourceType="python", **opciones)
    if seleccionar:
        cmds.tabLayout(padre, edit=True, selectTab=ESTANTE)
    guardar()
    return ESTANTE


def guardar():
    try:
        mel.eval("saveAllShelves $gShelfTopLevel")
        cmds.savePrefs(general=True)
    except RuntimeError:
        pass


def quitar():
    """Quita el estante y su archivo (lo usa desinstalar)."""
    if not cmds.about(batch=True) and existe():
        cmds.deleteUI(ESTANTE, layout=True)
    archivo = os.path.join(cmds.internalVar(userShelfDir=True), "shelf_{}.mel".format(ESTANTE))
    if os.path.exists(archivo):
        os.remove(archivo)
