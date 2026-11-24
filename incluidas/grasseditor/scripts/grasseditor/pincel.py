"""Pincel de zona: pintar en el visor dónde crece la hierba de una capa.

Se pinta sobre el suelo de la capa. Cada trazo (desde que pulsas hasta que
sueltas) es un solo paso de Ctrl+Z. Mientras pintas, la capa se ve con el
visor ligero para que el pincel vaya fluido.

Modos: «poner», «quitar» y «suavizar». Con Ctrl pulsado, «poner» quita.
"""

import maya.api.OpenMaya as om
from maya import cmds

from grasseditor import escena
from grasseditor.i18n import t
from grasseditor.mascara import Mascara

CONTEXTO = "grassEditorPincel"

_estado = {"capa": None, "modo": "poner", "radio": 100.0, "fuerza": 0.6, "mascara": None, "original": "",
           "al_pintar": None, "forma": None, "contador": 0}


def rayo_del_visor(x, y):
    """((origen), (dirección)) en mundo del píxel (x, y) del visor activo (API 1, como Árboles)."""
    import maya.OpenMaya as om1
    import maya.OpenMayaUI as omui1
    origen, direccion = om1.MPoint(), om1.MVector()
    omui1.M3dView.active3dView().viewToWorld(int(x), int(y), origen, direccion)
    return (origen.x, origen.y, origen.z), (direccion.x, direccion.y, direccion.z)


def tocar_suelo(forma, origen, direccion):
    """Punto del suelo (en su espacio local) bajo el rayo, o None."""
    sel = om.MSelectionList()
    sel.add(forma)
    camino = sel.getDagPath(0)
    fn = om.MFnMesh(camino)
    corte = fn.closestIntersection(om.MFloatPoint(*origen), om.MFloatVector(*direccion), om.MSpace.kWorld,
                                   1e8, False)
    if not corte or corte[2] < 0:
        return None
    p = om.MPoint(corte[0].x, corte[0].y, corte[0].z) * camino.inclusiveMatrixInverse()
    return p.x, p.y, p.z


def _mascara_de(capa):
    forma = escena.forma_suelo(capa)
    caja = escena.leer_suelo(forma, None).caja_local()
    texto = cmds.getAttr(capa + ".mascara") or ""
    mascara = Mascara.desde_texto(texto) if texto else None
    if mascara is None:
        return Mascara(caja, 255)
    if any(abs(a - b) > 1e-3 for a, b in zip(mascara.caja, caja)):
        return mascara.ajustada_a(caja)
    return mascara


def _escala(forma):
    matriz = cmds.getAttr(forma + ".worldMatrix[0]")
    import math
    return (math.sqrt(sum(v * v for v in matriz[0:3])) + math.sqrt(sum(v * v for v in matriz[8:11]))) / 2 or 1.0


def _aplicar(x, y, modo_contexto):
    e = _estado
    origen, direccion = rayo_del_visor(x, y)
    punto = tocar_suelo(e["forma"], origen, direccion)
    if punto is None:
        return False
    modo = e["modo"]
    modificadores = cmds.draggerContext(CONTEXTO, query=True, modifier=True) or ""
    if modo == "poner" and "ctrl" in modificadores:
        modo = "quitar"
    radio = e["radio"] / _escala(e["forma"])
    return e["mascara"].pintar(punto[0], punto[2], radio, e["fuerza"], modo) > 0


def _escribir(texto):
    cmds.setAttr(_estado["capa"] + ".mascara", texto, type="string")


def _pulsar():
    e = _estado
    capa = e["capa"]
    if not capa or not cmds.objExists(capa):
        cmds.warning(t("pincel_sin_capa"))
        return
    e["forma"] = escena.forma_suelo(capa)
    if not e["forma"]:
        cmds.warning(t("pincel_sin_suelo"))
        return
    e["original"] = cmds.getAttr(capa + ".mascara") or ""
    e["mascara"] = _mascara_de(capa)
    e["contador"] = 0
    x, y, _ = cmds.draggerContext(CONTEXTO, query=True, anchorPoint=True)
    if _aplicar(x, y, "pulsar"):
        escena._sin_deshacer(lambda: _escribir(e["mascara"].a_texto()))


def _arrastrar():
    e = _estado
    if e["mascara"] is None:
        return
    x, y, _ = cmds.draggerContext(CONTEXTO, query=True, dragPoint=True)
    if _aplicar(x, y, "arrastrar"):
        e["contador"] += 1
        escena._sin_deshacer(lambda: _escribir(e["mascara"].a_texto()))
        cmds.refresh(currentView=True)


def _soltar():
    e = _estado
    if e["mascara"] is None:
        return
    final = e["mascara"].a_texto()
    escena._sin_deshacer(lambda: _escribir(e["original"]))
    cmds.undoInfo(openChunk=True, chunkName="GrassEditor_pincel")
    try:
        _escribir(final)
    finally:
        cmds.undoInfo(closeChunk=True)
    e["mascara"] = None
    if e["al_pintar"]:
        e["al_pintar"]()


def activar(capa, modo="poner", radio=100.0, fuerza=0.6, al_pintar=None):
    """Activa el pincel sobre ``capa``. Esc o la herramienta de selección lo sueltan."""
    _estado.update(capa=capa, modo=modo, radio=float(radio), fuerza=float(fuerza), al_pintar=al_pintar)
    if cmds.draggerContext(CONTEXTO, exists=True):
        cmds.deleteUI(CONTEXTO)
    cmds.draggerContext(CONTEXTO, pressCommand=_pulsar, dragCommand=_arrastrar, releaseCommand=_soltar,
                        space="screen", cursor="crossHair", name=CONTEXTO, undoMode="sequence")
    cmds.setToolTo(CONTEXTO)


def ajustar(**cambios):
    """Cambia modo, radio o fuerza sin soltar la herramienta."""
    for clave in ("modo", "radio", "fuerza", "capa"):
        if clave in cambios:
            _estado[clave] = cambios[clave]


def soltar():
    if not cmds.about(batch=True) and cmds.draggerContext(CONTEXTO, exists=True):
        cmds.setToolTo("selectSuperContext")


def llenar(capa, valor=255):
    """Rellena (255) o vacía (0) toda la zona de la capa (un paso de Ctrl+Z)."""
    if valor >= 255:
        cmds.setAttr(capa + ".mascara", "", type="string")   # sin máscara = todo el suelo
        return
    mascara = _mascara_de(capa)
    mascara.llenar(valor)
    cmds.setAttr(capa + ".mascara", mascara.a_texto(), type="string")


def pintar_en(capa, puntos, radio, modo="poner", fuerza=1.0):
    """Pinta por programa en puntos del mundo [(x, y, z)] (para ejemplos y pruebas)."""
    forma = escena.forma_suelo(capa)
    mascara = _mascara_de(capa)
    sel = om.MSelectionList()
    sel.add(forma)
    inversa = sel.getDagPath(0).inclusiveMatrixInverse()
    escala = _escala(forma)
    for p in puntos:
        local = om.MPoint(*p) * inversa
        mascara.pintar(local.x, local.z, radio / escala, fuerza, modo)
    cmds.setAttr(capa + ".mascara", mascara.a_texto(), type="string")
    return mascara
