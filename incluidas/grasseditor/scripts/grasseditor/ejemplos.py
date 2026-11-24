"""Escena de ejemplo: un jardín con una loma, un camino y un parterre.

Es la misma escena que la maqueta del plan: un terreno de 40 × 25 m con
una loma, un camino que lo cruza, piedras y un árbol. Lleva tres capas:

* «loma»: hierba silvestre con espigas y flores, solo donde la pendiente
  lo permite, fuera del camino y apartada de piedras y tronco;
* «cesped»: césped con trébol pintado con el pincel en la parte delantera;
* «parterre»: mata ornamental dentro de una curva cerrada.

Tiene una cámara de render con recorte y detalle por distancia activos.
"""

import math

import maya.api.OpenMaya as om
from maya import cmds

from grasseditor import escena, pincel

ANCHO, FONDO = 4000.0, 2500.0     # cm


def altura(x, z):
    """Altura del terreno (cm) en (x, z): una loma al fondo a la derecha y otra pequeña."""
    return (700 * math.exp(-((x - 1100) ** 2 + (z + 550) ** 2) / 500000.0)
            + 250 * math.exp(-((x + 1400) ** 2 + (z + 950) ** 2) / 300000.0)
            + 30 * math.sin(x * 0.0045) * math.cos(z * 0.005))


def _terreno():
    plano = cmds.polyPlane(width=ANCHO, height=FONDO, subdivisionsX=80, subdivisionsY=50,
                           name="grasseditor_ejemplo_suelo")[0]
    sel = om.MSelectionList()
    sel.add(plano)
    fn = om.MFnMesh(sel.getDagPath(0))
    puntos = fn.getPoints(om.MSpace.kObject)
    for i in range(len(puntos)):
        p = puntos[i]
        puntos[i] = om.MPoint(p.x, altura(p.x, p.z), p.z)
    fn.setPoints(puntos, om.MSpace.kObject)
    cmds.delete(plano, constructionHistory=True)
    return plano


def _camino():
    puntos = [(-2000, 0, -100), (-900, 0, 300), (300, 0, -350), (1300, 0, 150), (2000, 0, 450)]
    puntos = [(x, altura(x, z) + 2, z) for x, _, z in puntos]
    return cmds.curve(degree=3, editPoint=puntos, name="grasseditor_ejemplo_camino")


def _parterre():
    x, z = 350.0, 700.0   # a la vista de la cámara de ejemplo
    curva = cmds.circle(normal=(0, 1, 0), radius=260, center=(x, altura(x, z) + 2, z), sections=16,
                        name="grasseditor_ejemplo_parterre")[0]
    cmds.delete(curva, constructionHistory=True)
    return curva


def _piedras():
    piedras = []
    for i, (x, z, r) in enumerate(((-400, 650, 90), (-250, 760, 55), (1500, 200, 130))):
        piedra = cmds.polySphere(radius=r, subdivisionsAxis=10, subdivisionsHeight=7,
                                 name="grasseditor_ejemplo_piedra{}".format(i + 1))[0]
        cmds.setAttr(piedra + ".scaleY", 0.6)
        cmds.move(x, altura(x, z) + r * 0.25, z, piedra)
        cmds.addAttr(piedra, longName=escena.ATRIBUTO_CANTERA, attributeType="bool", defaultValue=True)
        piedras.append(piedra)
    return piedras


def _arbol():
    x, z = -700.0, -500.0
    grupo = cmds.group(empty=True, name="grasseditor_ejemplo_arbol")
    tronco = cmds.polyCylinder(radius=22, height=420, name="grasseditor_ejemplo_tronco")[0]
    cmds.move(0, 210, 0, tronco)
    copa = cmds.polySphere(radius=300, name="grasseditor_ejemplo_copa")[0]
    cmds.setAttr(copa + ".scaleY", 0.7)
    cmds.move(0, 520, 0, copa)
    cmds.parent(tronco, copa, grupo)
    cmds.move(x, altura(x, z) - 5, z, grupo)
    cmds.addAttr(grupo, longName=escena.ATRIBUTO_ARBOLES, dataType="string")
    cmds.setAttr(grupo + "." + escena.ATRIBUTO_ARBOLES, "ejemplo", type="string")
    return grupo


def _camara():
    camara, forma = cmds.camera(name="grasseditor_ejemplo_camara", focalLength=30)
    camara = cmds.rename(camara, "grasseditor_ejemplo_camara")
    forma = cmds.listRelatives(camara, shapes=True, fullPath=True)[0]
    cmds.xform(camara, worldSpace=True, translation=(-150, 210, 1550), rotation=(-7, -8, 0))
    for otra in cmds.ls(type="camera"):
        cmds.setAttr(otra + ".renderable", 0)
    cmds.setAttr(forma + ".renderable", 1)
    return camara


def _luces():
    sol = cmds.directionalLight(name="grasseditor_ejemplo_sol", intensity=2.5)
    sol = cmds.listRelatives(sol, parent=True)[0]
    cmds.xform(sol, rotation=(-40, 35, 0))
    try:
        if escena._arnold():
            cielo = cmds.shadingNode("aiSkyDomeLight", asLight=True, name="grasseditor_ejemplo_cielo")
            forma = cmds.listRelatives(cielo, shapes=True)[0] if cmds.nodeType(cielo) == "transform" else cielo
            cmds.setAttr(forma + ".color", 0.75, 0.85, 1.0, type="double3")
            cmds.setAttr(forma + ".intensity", 0.8)
            cmds.setAttr(forma + ".aiSamples", 2)
    except RuntimeError:
        pass
    return sol


OPCIONES = {"recorte": True, "lod": True, "aclarar": True, "visor_porcentaje": 10.0, "visor_como": "tarjetas"}


def jardin_con_loma(nueva_escena=False):
    """Construye la escena de ejemplo y devuelve sus tres capas."""
    if nueva_escena:
        cmds.file(new=True, force=True)
    cmds.undoInfo(openChunk=True, chunkName="GrassEditor_ejemplo")
    try:
        suelo = _terreno()
        camino = escena.puntos_de_curva(_camino())
        camino.update(modo="fuera", ancho=160.0, nombre="grasseditor_ejemplo_camino", cerrada=False)
        parterre = escena.puntos_de_curva(_parterre())
        parterre.update(nombre="grasseditor_ejemplo_parterre")
        _piedras()
        _arbol()
        camara = _camara()
        _luces()
        alrededor = dict(parterre, modo="fuera")
        loma = escena.crear_capa(suelo, nombre="loma",
                                 mezcla=[["silvestre", 70], ["espigas", 20], ["flores", 10]],
                                 opciones=OPCIONES, densidad=100.0,
                                 reglas={"pendiente_max": 48.0, "curvas": [camino, alrededor]})
        cesped = escena.crear_capa(suelo, nombre="cesped", zona="pincel", mezcla=[["cesped", 85], ["trebol", 15]],
                                   opciones=OPCIONES, densidad=100.0, reglas={"curvas": [camino, alrededor]})
        delante = [(x, 0, z) for x in range(-1900, 300, 150) for z in range(450, 1250, 150)]
        pincel.pintar_en(cesped, delante, 220.0, "poner")
        pincel.pintar_en(loma, delante, 220.0, "quitar", 1.0)
        dentro = dict(parterre, modo="dentro")
        flores = escena.crear_capa(suelo, nombre="parterre", mezcla=[["ornamental", 70], ["flores", 30]],
                                   opciones=OPCIONES, densidad=150.0, reglas={"curvas": [dentro]})   # parterre tupido
        for capa in (loma, cesped, flores):
            escena.conectar_camara(capa, camara)
        escena.tenir_suelo(suelo)
        cmds.select(clear=True)
    finally:
        cmds.undoInfo(closeChunk=True)
    return [loma, cesped, flores]
