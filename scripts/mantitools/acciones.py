"""Ejecuta las órdenes de las herramientas (las usan el estante y la ventana central)."""

from maya import cmds

from mantitools import herramientas as hr
from mantitools.i18n import t


def codigo_estante(ident, clave):
    """El código Python que guarda un botón del estante para una orden."""
    return "import mantitools.acciones as _mt\n_mt.ejecutar({!r}, {!r})".format(ident, clave)


def ejecutar(ident, clave=None):
    """Ejecuta la orden ``clave`` de ``ident`` (la principal si no se dice), cargándola si hace falta."""
    from mantitools import carga
    ficha = hr.ficha(ident)
    clave = clave or ficha.principal
    if not carga.activa(ident):
        cmds.warning(t("aviso_desactivada", herramienta=ficha.nombre))
        return None
    if not carga.cargada(ident) and not carga.cargar(ident):
        return None
    espacio = {}
    try:
        exec(ficha.accion(clave).codigo, espacio)
    except Exception as error:
        cmds.warning(t("aviso_orden", herramienta=ficha.nombre, error=error))
        raise
    return espacio.get("_m")
