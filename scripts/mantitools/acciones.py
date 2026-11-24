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
    return espacio.get("_r")


def convertir_a_openpbr():
    """Convierte a OpenPBR los materiales de escenas viejas de cada herramienta que sabe hacerlo.

    Devuelve {nombre de la herramienta: materiales convertidos}. Las
    herramientas desactivadas no se tocan.
    """
    from mantitools import carga
    hechos = {}
    for ficha in hr.FICHAS:
        if "openpbr" not in [a.clave for a in ficha.acciones] or not carga.activa(ficha.id):
            continue
        try:
            hechos[ficha.nombre] = list(ejecutar(ficha.id, "openpbr") or [])
        except Exception:   # ya avisó ejecutar; las demás siguen
            continue
    return hechos


def resumen_openpbr(hechos):
    """Texto para el usuario con lo que ha hecho ``convertir_a_openpbr``."""
    if not any(hechos.values()):
        return t("openpbr_nada")
    lineas = ["{}: {}".format(nombre, len(materiales)) for nombre, materiales in hechos.items()]
    return t("openpbr_hecho", n=sum(len(m) for m in hechos.values())) + "\n" + "\n".join(lineas)
