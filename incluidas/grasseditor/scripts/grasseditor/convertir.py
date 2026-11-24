"""Acabado: convertir la hierba de una capa y exportarla.

* ``instancias_sueltas``: cada mata pasa a ser una instancia de Maya normal
  (para retocar a mano unas pocas). Con muchas matas la escena se vuelve
  lenta: se avisa a partir de ``AVISO_SUELTAS``.
* ``unir_en_malla``: toda la capa en una sola malla (para exportar a otro
  programa). Se avisa a partir de ``AVISO_TRIANGULOS``.
* ``exportar_puntos``: CSV o JSON con tipo, variante, nivel, posición, giro y
  escala de cada mata, para repartir la hierba en un motor de juego.
* ``exportar_fbx``: los prototipos de la capa en un FBX.

Todas usan las matas del render (con recorte y detalle por distancia).
"""

import csv
import json
import math

import maya.api.OpenMaya as om
from maya import cmds

from grasseditor import escena, matas
from grasseditor.tipos import NIVELES, PROTOTIPOS_POR_TIPO

AVISO_SUELTAS = 5000
AVISO_TRIANGULOS = 2000000


def salida_render(capa):
    """La salida de render de la capa (camara.Salida) y las claves de su mezcla."""
    from grasseditor import camara as cam
    from grasseditor import capa as cp
    motor = cp.Motor()
    forma = escena.forma_suelo(capa)
    matriz = cmds.getAttr(forma + ".worldMatrix[0]")
    suelo = escena.leer_suelo(forma, matriz)
    motor.preparar(suelo, escena.ajustes(capa), escena.catalogo(), cmds.getAttr(capa + ".mascara") or "",
                   cmds.getAttr(capa + ".horneado") or "")
    camara = None
    tr = escena.camara_de(capa)
    if tr:
        forma_cam = cmds.listRelatives(tr, shapes=True, fullPath=True, type="camera") or [tr]
        aspecto = cmds.getAttr("defaultResolution.deviceAspectRatio") if cmds.objExists("defaultResolution") else 1.78
        camara = cam.Camara(cmds.getAttr(forma_cam[0] + ".worldMatrix[0]"),
                            cmds.getAttr(forma_cam[0] + ".focalLength"),
                            cmds.getAttr(forma_cam[0] + ".horizontalFilmAperture"), aspecto)
    return motor.salida(camara, True), motor.candidatas.claves


def _descomponer(indice):
    hueco, resto = divmod(int(indice), PROTOTIPOS_POR_TIPO)
    variante, nivel = divmod(resto, NIVELES)
    return hueco, variante, nivel


def _matriz(posicion, giro, escala):
    t = om.MTransformationMatrix()
    t.setTranslation(om.MVector(*posicion), om.MSpace.kWorld)
    t.setRotation(om.MEulerRotation(*[math.radians(g) for g in giro]))
    t.setScale(escala, om.MSpace.kWorld)
    return t.asMatrix()


def instancias_sueltas(capa):
    """Crea un grupo con una instancia de Maya por mata. Devuelve el grupo."""
    s, claves = salida_render(capa)
    grupo = cmds.group(empty=True, world=True, name=capa + "_sueltas")
    cat = escena.catalogo()
    cmds.undoInfo(openChunk=True, chunkName="GrassEditor_sueltas")
    try:
        rutas = {c: escena.prototipos(c, cat) for c in claves}
        for i in range(len(s)):
            hueco, variante, nivel = _descomponer(s.indices[i])
            origen = rutas[claves[hueco]][variante * NIVELES + nivel]
            copia = cmds.instance(origen, name="{}_{}".format(claves[hueco], i))[0]
            copia = cmds.parent(copia, grupo)[0]
            m = _matriz(s.posiciones[i], s.giros[i], s.escalas[i])
            cmds.xform(copia, worldSpace=True, matrix=[m.getElement(f, c) for f in range(4) for c in range(4)])
            cmds.setAttr(copia + ".visibility", 1)
        instancias = escena.instanciador(capa)
        if instancias:
            cmds.setAttr(instancias + ".visibility", 0)
    finally:
        cmds.undoInfo(closeChunk=True)
    return grupo


def triangulos_render(capa):
    s, claves = salida_render(capa)
    cat = escena.catalogo()
    from grasseditor.capa import triangulos_tipo
    tris = {c: triangulos_tipo(cat[c]) for c in claves}
    return sum(tris[claves[_descomponer(i)[0]]][_descomponer(i)[2]] for i in s.indices)


def unir_en_malla(capa):
    """Toda la hierba de la capa en una malla con UVs y colores. Devuelve el transform."""
    s, claves = salida_render(capa)
    cat = escena.catalogo()
    cache = {}
    puntos, conteos, indices, us, vs, colores = [], [], [], [], [], []
    lineal = escena._con_gestion_de_color()
    for i in range(len(s)):
        hueco, variante, nivel = _descomponer(s.indices[i])
        clave = claves[hueco]
        if (clave, variante, nivel) not in cache:
            cache[(clave, variante, nivel)] = matas.mata(cat[clave], variante, nivel)
        malla = cache[(clave, variante, nivel)]
        m = _matriz(s.posiciones[i], s.giros[i], s.escalas[i])
        base = len(puntos)
        for v, uv, c in zip(malla.vertices, malla.uvs, malla.colores):
            puntos.append(om.MPoint(*v) * m)
            us.append(uv[0])
            vs.append(uv[1])
            colores.append(om.MColor(escena._a_lineal(c, lineal, escena._BRILLO) + (1.0,)))
        conteos.extend(malla.conteos)
        indices.extend(base + k for k in malla.indices)
    fn = om.MFnMesh()
    forma = fn.create(om.MPointArray(puntos), conteos, indices, om.MFloatArray(us), om.MFloatArray(vs))
    fn.assignUVs(om.MIntArray(conteos), om.MIntArray(indices))
    fn.createColorSet("colorSet1", True)
    fn.setCurrentColorSetName("colorSet1")
    fn.setVertexColors(om.MColorArray(colores), list(range(len(puntos))))
    transform = cmds.rename(om.MFnDagNode(forma).fullPathName(), capa + "_malla")
    formas = cmds.listRelatives(transform, shapes=True, fullPath=True)
    cmds.setAttr(formas[0] + ".displayColors", 1)
    if cmds.attributeQuery("aiExportColors", node=formas[0], exists=True):
        cmds.setAttr(formas[0] + ".aiExportColors", 1)
    cmds.sets(formas[0], edit=True, forceElement=escena.SG)
    return transform


def filas(capa):
    """Una fila por mata: tipo, variante, nivel, x, y, z, giro x/y/z, escala."""
    s, claves = salida_render(capa)
    resultado = []
    for i in range(len(s)):
        hueco, variante, nivel = _descomponer(s.indices[i])
        p, g, e = s.posiciones[i], s.giros[i], s.escalas[i]
        resultado.append([claves[hueco], variante, nivel] + [round(v, 3) for v in p] +
                         [round(v, 2) for v in g] + [round(e[0], 4)])
    return resultado


CABECERA = ["tipo", "variante", "nivel", "x", "y", "z", "giro_x", "giro_y", "giro_z", "escala"]


def exportar_puntos(capa, ruta):
    """Escribe las matas en ``ruta`` (.csv o .json). Devuelve cuántas."""
    datos = filas(capa)
    if ruta.lower().endswith(".json"):
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump({"unidades": "cm", "giro": "grados XYZ", "columnas": CABECERA, "matas": datos}, f)
    else:
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            escritor = csv.writer(f)
            escritor.writerow(CABECERA)
            escritor.writerows(datos)
    return len(datos)


def exportar_fbx(capa, ruta):
    """Exporta los prototipos de los tipos de la capa a un FBX. Devuelve la ruta."""
    if not cmds.pluginInfo("fbxmaya", query=True, loaded=True):
        cmds.loadPlugin("fbxmaya", quiet=True)
    cat = escena.catalogo()
    rutas = []
    for clave in escena.ajustes(capa).claves():
        rutas.extend(escena.prototipos(clave, cat))
    seleccion = cmds.ls(selection=True, long=True) or []
    try:
        cmds.select(rutas, replace=True)
        cmds.file(ruta, force=True, options="v=0;", type="FBX export", exportSelected=True, preserveReferences=False)
    finally:
        cmds.select(seleccion, replace=True) if seleccion else cmds.select(clear=True)
    return ruta
