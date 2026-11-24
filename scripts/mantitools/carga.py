"""Arranque del pack: carga las herramientas activas, el menú y el estante.

``mantitools_plugin`` llama a ``iniciar`` al cargarse y a ``detener`` al descargarse.
Cada herramienta sigue siendo su propio plugin de Maya (unas usan la API 1 y
otras la 2, que no se pueden mezclar en un mismo archivo); MantiTools solo los
carga y descarga.
"""

import os

from maya import cmds

from mantitools import herramientas as hr
from mantitools.ajustes import Ajustes
from mantitools.clase import Clase
from mantitools.i18n import t, usar_idioma

_estado = {"ajustes": None, "clase": None, "iniciado": False, "fallos": {}}


def carpeta_preferencias():
    return os.path.join(cmds.internalVar(userAppDir=True), "mantitools")


def ajustes():
    if _estado["ajustes"] is None:
        _estado["ajustes"] = Ajustes(carpeta_preferencias())
    return _estado["ajustes"]


def clase():
    if _estado["clase"] is None:
        _estado["clase"] = Clase(ajustes()["carpeta_clase"])
    return _estado["clase"]


def releer_clase():
    _estado["clase"] = None
    return clase()


def activa(ident):
    """Activa para el alumno y no desactivada por el profesor."""
    return ajustes().activa(ident) and ident not in clase().desactivadas


def en_el_pack(ident):
    return ident in hr.ORDEN and activa(ident)


RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def carpeta_incluida(ident):
    """Dónde está la copia de ``ident`` que trae el pack (``incluidas/<id>``)."""
    return os.path.join(RAIZ, "incluidas", ident)


def ruta_plugin(ident):
    """El archivo del plugin de ``ident`` dentro del pack, o None si el pack no lo trae."""
    ruta = os.path.join(carpeta_incluida(ident), "plug-ins", hr.ficha(ident).plugin + ".py")
    return ruta if os.path.isfile(ruta) else None


def disponible(ident):
    """El pack trae la herramienta."""
    return ruta_plugin(ident) is not None


def cargada(ident):
    try:
        return bool(cmds.pluginInfo(hr.ficha(ident).plugin, query=True, loaded=True))
    except RuntimeError:
        return False


def fallo(ident):
    return _estado["fallos"].get(ident, "")


def cargar(ident):
    """Carga el plugin de ``ident``. Devuelve True si queda cargado."""
    ficha = hr.ficha(ident)
    if cargada(ident):
        return True
    try:
        # Por ruta: así se carga la copia del pack aunque quede otra instalada aparte.
        cmds.loadPlugin(ruta_plugin(ident) or ficha.plugin, quiet=True)
        # Las herramientas se cargan con su plugin, no por su cuenta: así no se cargan dos veces.
        cmds.pluginInfo(ficha.plugin, edit=True, autoload=False)
        _estado["fallos"].pop(ident, None)
        return True
    except RuntimeError as error:
        _estado["fallos"][ident] = str(error).strip() or t("sin_detalle")
        cmds.warning(t("aviso_carga", herramienta=ficha.nombre, error=_estado["fallos"][ident]))
        return False


def descargar(ident):
    ficha = hr.ficha(ident)
    if not cargada(ident):
        return True
    try:
        cmds.unloadPlugin(ficha.plugin, force=True)
        return True
    except RuntimeError as error:
        cmds.warning(t("aviso_descarga", herramienta=ficha.nombre, error=error))
        return False


def aplicar_idioma(codigo=None):
    """Pone el idioma del pack en todas las herramientas cargadas."""
    import importlib
    codigo = codigo or ajustes().idioma
    usar_idioma(codigo)
    for ficha in hr.FICHAS:
        try:
            i18n = importlib.import_module(ficha.paquete + ".i18n")
            i18n.usar_idioma(codigo)
        except Exception:
            continue
    if cmds.optionVar(exists="trepadoraIdioma") or cargada("trepadora"):
        cmds.optionVar(stringValue=("trepadoraIdioma", codigo))
    if cargada("radial"):
        try:
            from radial import interfaz_maya as radial_maya
            radial_maya.ajustes().idioma = codigo
            radial_maya.ajustes().guardar()
        except Exception:
            pass


def iniciar():
    """Carga las herramientas activas, crea el menú y, si falta, el estante."""
    usar_idioma(ajustes().idioma)
    from mantitools import adaptadores
    adaptadores.aplicar_clase()
    for ficha in hr.FICHAS:
        if activa(ficha.id):
            cargar(ficha.id)
    if cmds.about(batch=True):
        _estado["iniciado"] = True
        return
    aplicar_idioma()
    # Los plugins crean sus menús con evalDeferred: el de MantiTools se rehace después,
    # y al rehacerse les pide a todas que pongan su submenú dentro.
    cmds.evalDeferred(_terminar_arranque, lowestPriority=True)
    _estado["iniciado"] = True


def _terminar_arranque():
    from mantitools import estante, menu
    menu.construir()
    estante.crear(forzar=False)


def detener():
    from mantitools import centro, menu
    centro.cerrar()
    for ficha in reversed(hr.FICHAS):
        descargar(ficha.id)
    if not cmds.about(batch=True):
        menu.quitar()
    _estado.update(iniciado=False, ajustes=None, clase=None)


def cambiar_activa(ident, valor):
    """Activa o desactiva una herramienta al momento (menú y estante incluidos)."""
    from mantitools import centro, estante, menu
    ajustes().fijar_activa(ident, valor)
    if valor and activa(ident):
        cargar(ident)
    elif not valor:
        descargar(ident)
    cmds.evalDeferred(lambda: (menu.construir(), estante.crear(forzar=True), centro.actualizar()),
                      lowestPriority=True)
