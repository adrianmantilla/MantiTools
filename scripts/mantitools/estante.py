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
# En la sesión en que se instala, los iconos van por ruta (ver ``icono``).
_sesion = {"rutas": False}


def icono(nombre, ruta_completa=False):
    """El icono por su nombre (Maya lo busca en las carpetas de iconos del .mod, con sus versiones
    _150 y _200) o, con ``ruta_completa``, por su ruta en el pack.

    Justo después de instalar Maya aún no conoce la carpeta de iconos del pack (la lee al
    arrancar), así que en esa sesión se usa la ruta; al arrancar otra vez se cambia por el nombre.
    """
    if not ruta_completa:
        return nombre
    from mantitools import carga
    return os.path.join(carga.RAIZ, "icons", nombre).replace("\\", "/")


def botones(ruta_completa=False):
    """Lo que lleva el estante, como datos: [(etiqueta, ayuda, icono, orden, [(texto, orden), ...]), ...]."""
    from mantitools import carga
    lista = []
    for ficha in hr.FICHAS:
        if not carga.activa(ficha.id):
            continue
        principal = ficha.accion(ficha.principal)
        menu = [(t(ficha.texto(a.clave)), codigo_estante(ficha.id, a.clave)) for a in ficha.secundarias]
        ayuda = "{}: {}".format(ficha.nombre, t(ficha.texto(principal.clave)))
        lista.append((ficha.nombre, ayuda, icono(ficha.icono, ruta_completa), codigo_estante(ficha.id, principal.clave), menu))
    menu_centro = [(t("menu_ajustes"), "import mantitools.centro as _c\n_c.mostrar('ajustes')"),
                   (t("menu_ayuda"), "import mantitools.centro as _c\n_c.mostrar('ayuda')"),
                   (t("menu_comprobar"), "import mantitools.comprobar as _c\n_c.mostrar()")]
    lista.append(("MantiTools", t("estante_centro"), icono("mantitools_centro.png", ruta_completa), CODIGO_CENTRO,
                  menu_centro))
    return lista


def existe():
    return bool(cmds.shelfLayout(ESTANTE, exists=True))


def _con_rutas():
    """¿Algún botón del estante usa la ruta completa del icono (estante hecho justo al instalar)?"""
    for boton in cmds.shelfLayout(ESTANTE, query=True, childArray=True) or []:
        try:
            imagen = cmds.shelfButton(boton, query=True, image=True) or ""
        except RuntimeError:
            continue
        if "/" in imagen or "\\" in imagen:
            return True
    return False


def _desfasado(ruta_completa=False):
    """¿Le faltan o le sobran botones al estante (p. ej. tras añadir una herramienta al pack)?"""
    actuales = []
    for boton in cmds.shelfLayout(ESTANTE, query=True, childArray=True) or []:
        try:
            actuales.append(cmds.shelfButton(boton, query=True, label=True))
        except RuntimeError:
            continue
    return actuales != [b[0] for b in botones(ruta_completa)]


def crear(forzar=False, seleccionar=False, ruta_completa=False):
    """Crea el estante si falta; con ``forzar`` lo rehace aunque exista.

    Si el estante se hizo al instalar (iconos por ruta), se rehace con los nombres. También se
    rehace si sus botones no son los de las herramientas activas (una herramienta nueva en el pack).
    """
    if cmds.about(batch=True):
        return None
    if ruta_completa:
        _sesion["rutas"] = True
    ruta_completa = _sesion["rutas"]
    padre = mel.eval("$tmp = $gShelfTopLevel")
    if existe():
        if not forzar and (ruta_completa or not _con_rutas()) and not _desfasado(ruta_completa):
            return ESTANTE
        for boton in cmds.shelfLayout(ESTANTE, query=True, childArray=True) or []:
            cmds.deleteUI(boton)
    else:
        mel.eval('addNewShelfTab "{}"'.format(ESTANTE))
    for etiqueta, ayuda, imagen, orden, menu in botones(ruta_completa):
        opciones = {}
        if menu:
            opciones["menuItem"] = [(texto, codigo) for texto, codigo in menu]
            opciones["menuItemPython"] = list(range(len(menu)))
        cmds.shelfButton(parent=ESTANTE, label=etiqueta, annotation=ayuda, image=imagen, image1=imagen,
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
