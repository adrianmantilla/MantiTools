"""Materiales de Árboles: clay y, si están instaladas, texturas por especie.

Usa ``openPBRSurface`` (OpenPBR, ver openpbr.py), que viene con Maya 2026 y
2027, se ve en el visor y Arnold lo renderiza sin cargar nada más; en un Maya
sin OpenPBR, ``standardSurface``. Los atributos se escriben con los nombres de
standardSurface y openpbr.py los traduce. Corteza y hoja van en materiales separados.
Los materiales con texturas se llaman ``arboles_<juego>_corteza`` y
``arboles_<juego>_hoja`` y leen las imágenes de ``texturas/<juego>/<resolución>``.
"""

from maya import cmds

from arboles import openpbr
from arboles import texturas as tx

# nombre: (color base, rugosidad, intensidad especular, transmisión)
CLAY = {
    "arboles_clay_corteza": ((0.58, 0.55, 0.52), 0.6, 0.3, 0.0),
    "arboles_clay_hoja": ((0.66, 0.66, 0.62), 0.5, 0.35, 0.15),
}


# Tipos de material de Árboles: los nuevos (OpenPBR) y los de escenas viejas.
TIPOS = [openpbr.TIPO, "standardSurface"]


def _grupo(material):
    conexiones = cmds.listConnections(material + ".outColor", type="shadingEngine") or []
    if conexiones:
        return conexiones[0]
    grupo = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=material + "SG")
    cmds.connectAttr(material + ".outColor", grupo + ".surfaceShader", force=True)
    return grupo


def crear_material(nombre):
    """Devuelve (material, grupo de sombreado); lo crea si no existe."""
    if cmds.objExists(nombre):
        return nombre, _grupo(nombre)
    color, rugosidad, especular, transmision = CLAY[nombre]
    material = cmds.shadingNode(openpbr.tipo(), asShader=True, name=nombre)
    poner = openpbr.poner
    poner(material, "base", 1.0)
    poner(material, "baseColor", *color, type="double3")
    poner(material, "specular", especular)
    poner(material, "specularRoughness", rugosidad)
    if transmision:
        # Las hojas dejan pasar algo de luz, como en Trepadora.
        poner(material, "thinWalled", 1)
        poner(material, "subsurface", transmision)
        poner(material, "subsurfaceColor", *color, type="double3")
    return material, _grupo(material)


def crear_todos():
    return {nombre: crear_material(nombre) for nombre in CLAY}


def asignar(objetos, nombre):
    _, grupo = crear_material(nombre)
    cmds.sets(objetos, edit=True, forceElement=grupo)


# --- texturas por especie ---------------------------------------------------------

def nombre_material(juego, parte):
    """Material que usa ``parte`` (corteza u hoja) de un árbol con ese juego de texturas."""
    if not tx.existe(juego):
        return "arboles_clay_" + parte
    return "arboles_{}_{}".format(juego, parte)


def _archivo(nombre, ruta, color):
    nodo = cmds.shadingNode("file", asTexture=True, isColorManaged=True, name=nombre)
    colocacion = cmds.shadingNode("place2dTexture", asUtility=True, name=nombre + "_place")
    for a, b in (("outUV", "uvCoord"), ("outUvFilterSize", "uvFilterSize")):
        cmds.connectAttr(colocacion + "." + a, nodo + "." + b)
    cmds.setAttr(nodo + ".fileTextureName", ruta, type="string")
    if not color:
        cmds.setAttr(nodo + ".colorSpace", "Raw", type="string")
        cmds.setAttr(nodo + ".ignoreColorSpaceFileRules", 1)
        cmds.setAttr(nodo + ".alphaIsLuminance", 1)
    return nodo


# Brillo especular por estilo: el cartoon casi mate, el estilizado a medias.
ESPECULAR_ESTILO = {"cartoon": 0.33, "estilizado": 0.66}
# Emisión con el propio color: aplana el sombreado (el cartoon casi no tiene sombras propias)
EMISION_ESTILO = {"cartoon": 0.35, "estilizado": 0.12}


def _especular(parte, estilo):
    return CLAY["arboles_clay_" + parte][2] * ESPECULAR_ESTILO.get(estilo, 1.0)


def crear_material_texturas(juego, parte, resolucion=tx.RESOLUCION_POR_DEFECTO, estilo=tx.ESTILO_POR_DEFECTO):
    """(material, grupo) con las texturas de ``juego``; clay si el juego no está instalado."""
    nombre = nombre_material(juego, parte)
    if cmds.objExists(nombre):
        return nombre, _grupo(nombre)
    if not tx.existe(juego):
        return crear_material(nombre)
    clay = CLAY["arboles_clay_" + parte]
    material = cmds.shadingNode(openpbr.tipo(), asShader=True, name=nombre)
    poner, conectar = openpbr.poner, openpbr.conectar
    poner(material, "base", 1.0)
    poner(material, "baseColor", *clay[0], type="double3")  # si falta la imagen de color
    poner(material, "specular", _especular(parte, estilo))
    poner(material, "specularRoughness", clay[1])
    if parte == "hoja":
        poner(material, "thinWalled", 1)
        poner(material, "subsurface", 0.4)
        poner(material, "subsurfaceColor", *clay[0], type="double3")
    canales = tx.canales(juego, parte, resolucion, estilo=estilo)
    if "color" in canales:
        n = _archivo(nombre + "_color", canales["color"], True)
        conectar(n + ".outColor", material, "baseColor")
        conectar(n + ".outColor", material, "emissionColor")
        poner(material, "emission", EMISION_ESTILO.get(estilo, 0.0))
        if parte == "hoja" and "translucidez" not in canales:
            conectar(n + ".outColor", material, "subsurfaceColor")
    if "translucidez" in canales:
        n = _archivo(nombre + "_translucidez", canales["translucidez"], True)
        conectar(n + ".outColor", material, "subsurfaceColor")
    if "rugosidad" in canales:
        n = _archivo(nombre + "_rugosidad", canales["rugosidad"], False)
        conectar(n + ".outAlpha", material, "specularRoughness")
    if "normal" in canales:
        n = _archivo(nombre + "_normal", canales["normal"], False)
        relieve = cmds.shadingNode("bump2d", asUtility=True, name=nombre + "_relieve")
        cmds.setAttr(relieve + ".bumpInterp", 1)  # mapa de normales en espacio tangente
        cmds.connectAttr(n + ".outAlpha", relieve + ".bumpValue")
        conectar(relieve + ".outNormal", material, "normalCamera")
        cmds.setAttr(n + ".alphaIsLuminance", 0)
    return material, _grupo(material)


def cambiar_texturas(resolucion, estilo=tx.ESTILO_POR_DEFECTO):
    """Vuelve a apuntar las texturas de los materiales de la escena a ``resolucion`` y ``estilo``."""
    cambiados = 0
    for nodo in cmds.ls("arboles_*_color", "arboles_*_normal", "arboles_*_rugosidad", "arboles_*_translucidez",
                        type="file") or []:
        partes = nodo.split("_")  # arboles, <juego…>, <parte>, <canal>
        juego, parte, canal = "_".join(partes[1:-2]), partes[-2], partes[-1]
        ruta = tx.ruta(juego, parte, canal, resolucion, estilo=estilo)
        if ruta:
            cmds.setAttr(nodo + ".fileTextureName", ruta, type="string")
            cambiados += 1
    for material in cmds.ls("arboles_*_corteza", "arboles_*_hoja", type=TIPOS) or []:
        if material in CLAY:
            continue
        parte = material.rsplit("_", 1)[-1]
        openpbr.poner(material, "specular", _especular(parte, estilo))
        if cmds.listConnections(material + ".emissionColor", source=True, destination=False):
            openpbr.poner(material, "emission", EMISION_ESTILO.get(estilo, 0.0))
    return cambiados


def convertir_a_openpbr():
    """Pasa a openPBRSurface los materiales de Árboles de escenas viejas (standardSurface).

    Las mallas, las texturas y los ajustes no cambian. Devuelve la lista de
    materiales convertidos (vacía si no había o si este Maya no tiene OpenPBR).
    """
    cmds.undoInfo(openChunk=True, chunkName="Arboles: OpenPBR")
    try:
        return openpbr.convertir_escena(("arboles_*_corteza", "arboles_*_hoja"))
    finally:
        cmds.undoInfo(closeChunk=True)


def cambiar_resolucion(resolucion, estilo=tx.ESTILO_POR_DEFECTO):
    return cambiar_texturas(resolucion, estilo)


def rehacer_material_texturas(juego, resolucion=None, estilo=None):
    """Borra y vuelve a crear los materiales de ``juego`` (p. ej. un material propio con imágenes
    nuevas), y los devuelve a las mismas mallas. Devuelve cuántos materiales ha rehecho."""
    from arboles import construir_maya as cm
    resolucion = resolucion or cm.resolucion_texturas()
    estilo = estilo or cm.estilo_texturas()
    rehechos = 0
    for parte in ("corteza", "hoja"):
        nombre = nombre_material(juego, parte)
        if nombre in CLAY or not cmds.objExists(nombre):
            continue
        viejo = _grupo(nombre)
        miembros = cmds.sets(viejo, query=True) or []
        cmds.delete([n for n in cmds.ls(nombre + "_*") if cmds.objExists(n)] + [nombre, viejo])
        _, nuevo = crear_material_texturas(juego, parte, resolucion, estilo)
        if miembros:
            cmds.sets(miembros, edit=True, forceElement=nuevo)
        rehechos += 1
    return rehechos
