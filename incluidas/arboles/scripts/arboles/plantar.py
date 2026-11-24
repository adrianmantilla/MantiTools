"""Plantar árboles de la biblioteca en la escena como copias ligadas a un maestro.

Estructura en la escena::

    arboles_maestros (oculto)
      <arbol>_<nivel>      el maestro: un árbol generado (atributos arbolesReceta,
                           arbolesNivel y arbolesMaestro con el nombre en la biblioteca)
    <arbol>_<nivel>_v2…  maestros de las variantes (otra forma del mismo árbol, ver
                           variantes.py); guardan la receta del original y arbolesVariante
    <arbol>_1, <arbol>_2…  cada copia plantada: un transform propio (posición y giro)
                           con el maestro como hijo instanciado (atributo arbolesPlantado)

Como las copias comparten el grupo del maestro, al regenerar el maestro con
otra receta cambian todas a la vez. «Desligar» convierte una copia en un árbol
independiente. Plantar y desligar se deshacen con Ctrl+Z (son comandos de Maya);
crear o actualizar el maestro va por el comando arbolesAccion.
"""

import random

import maya.api.OpenMaya as om
from maya import cmds

from arboles import acciones
from arboles import construir_maya as cm
from arboles import variantes as var
from arboles.biblioteca import nombre_de_archivo

MAESTROS = "arboles_maestros"
ATRIBUTO_MAESTRO = "arbolesMaestro"
ATRIBUTO_PLANTADO = "arbolesPlantado"
ATRIBUTO_VARIANTE = "arbolesVariante"
CONTEXTO = "arbolesPlantar"
NIVEL_POR_DEFECTO = "medio"


# --- maestros -----------------------------------------------------------------

def _grupo_maestros():
    if not cmds.objExists("|" + MAESTROS):
        cmds.group(empty=True, world=True, name=MAESTROS)
        cmds.setAttr("|" + MAESTROS + ".visibility", 0)
        cmds.setAttr("|" + MAESTROS + ".hiddenInOutliner", 1)
    return "|" + MAESTROS


def nombre_maestro(nombre, nivel, variante=0):
    base = "{}_{}".format(nombre_de_archivo(nombre), nivel)
    return base if not variante else "{}_v{}".format(base, variante + 1)


def ruta_maestro(nombre, nivel, variante=0):
    return "|{}|{}".format(MAESTROS, nombre_maestro(nombre, nivel, variante))


def variante_de(ruta):
    """Número de variante de un maestro (0 si es el original)."""
    if cmds.attributeQuery(ATRIBUTO_VARIANTE, node=ruta, exists=True):
        return int(cmds.getAttr(ruta + "." + ATRIBUTO_VARIANTE))
    return 0


def _rehacer(ruta, arbol, nivel, variante):
    """Reconstruye el maestro con la forma de su variante, guardando la receta del original."""
    cm.reconstruir(ruta, var.variante(arbol, variante), nivel, guardar_receta=False)
    cmds.setAttr(ruta + "." + cm.ATRIBUTO_RECETA, arbol.a_json(), type="string")


def maestros():
    """[(ruta, nombre en la biblioteca, nivel)] de los maestros de la escena."""
    if not cmds.objExists("|" + MAESTROS):
        return []
    resultado = []
    for hijo in cmds.listRelatives("|" + MAESTROS, children=True, fullPath=True) or []:
        nombre = cm.leer_texto(hijo, ATRIBUTO_MAESTRO)
        if nombre:
            resultado.append((hijo, nombre, cm.leer_texto(hijo, cm.ATRIBUTO_NIVEL)))
    return resultado


def _materiales_al_dia(ruta, arbol):
    """True si las mallas del maestro usan el material de corteza que le toca a ``arbol``."""
    from arboles import materiales
    deseado = materiales.nombre_material(arbol.material, "corteza")
    mallas = cmds.listRelatives(ruta, allDescendents=True, type="mesh", fullPath=True) or []
    for malla in mallas:
        for grupo in cmds.listConnections(malla, type="shadingEngine") or []:
            if deseado in (cmds.listConnections(grupo + ".surfaceShader") or []):
                return True
    return not mallas


def asegurar_maestro(arbol, nivel=NIVEL_POR_DEFECTO, variante=0):
    """Ruta del maestro de ``arbol`` a ``nivel`` (y variante); lo crea si no existe (fuera del deshacer)."""
    ruta = ruta_maestro(arbol.nombre, nivel, variante)
    if cm.existe(ruta):
        if not _materiales_al_dia(ruta, arbol):
            # Maestro de una escena anterior en clay (o con otras texturas): se rehace con las suyas.
            estado = cmds.undoInfo(query=True, stateWithoutFlush=True)
            cmds.undoInfo(stateWithoutFlush=False)
            try:
                cm.preparar(arbol)
                _rehacer(ruta, arbol, nivel, variante)
            finally:
                cmds.undoInfo(stateWithoutFlush=estado)
        return ruta
    estado = cmds.undoInfo(query=True, stateWithoutFlush=True)
    cmds.undoInfo(stateWithoutFlush=False)
    try:
        cm.preparar(arbol)
        padre = _grupo_maestros()
        grupo = cm.crear(var.variante(arbol, variante), nivel, nombre_maestro(arbol.nombre, nivel, variante))
        grupo = cmds.parent(grupo, padre)[0]
        cmds.setAttr(grupo + "." + cm.ATRIBUTO_RECETA, arbol.a_json(), type="string")  # la del original
        cmds.addAttr(grupo, longName=ATRIBUTO_MAESTRO, dataType="string")
        cmds.setAttr(grupo + "." + ATRIBUTO_MAESTRO, nombre_de_archivo(arbol.nombre), type="string")
        if variante:
            cmds.addAttr(grupo, longName=ATRIBUTO_VARIANTE, attributeType="long", defaultValue=variante)
    finally:
        cmds.undoInfo(stateWithoutFlush=estado)
    return ruta


def actualizar_maestros(arbol):
    """Regenera con la receta de ``arbol`` todos sus maestros (y así todas sus copias).

    Un solo paso de deshacer. Devuelve cuántos maestros se han actualizado.
    """
    nombre = nombre_de_archivo(arbol.nombre)
    afectados = [(ruta, nivel) for ruta, n, nivel in maestros() if n == nombre]
    if not afectados:
        return 0
    cm.preparar(arbol)
    antes = [(ruta, nivel, cm.arbol_de(ruta)) for ruta, nivel in afectados]
    despues = arbol.copiar()

    def hacer():
        for ruta, nivel, _ in antes:
            _rehacer(ruta, despues, nivel, variante_de(ruta))

    def deshacer():
        for ruta, nivel, viejo in antes:
            _rehacer(ruta, viejo, nivel, variante_de(ruta))

    acciones.ejecutar(hacer, deshacer, "Arboles_actualizar_maestros")
    return len(afectados)


def anadir_ejemplos(biblioteca, titulo=lambda plantilla: plantilla):
    """Guarda en ``biblioteca`` las plantillas de serie (con miniatura) que aún no estén.

    ``titulo(plantilla)`` da el nombre con el que se guardan. Devuelve los nombres añadidos.
    """
    from arboles import editor, ejemplos
    anadidos = []
    estado = cmds.undoInfo(query=True, stateWithoutFlush=True)
    cmds.undoInfo(stateWithoutFlush=False)
    try:
        cm.preparar()
        for plantilla in ejemplos.PLANTILLAS:
            if plantilla == "vacio":
                continue
            arbol = ejemplos.crear(plantilla)
            arbol.nombre = titulo(plantilla)
            if biblioteca.existe(arbol.nombre):
                continue
            cm.preparar(arbol)
            biblioteca.guardar(arbol)
            grupo = cm.crear(arbol, NIVEL_POR_DEFECTO, "arboles_ejemplo_temporal")
            try:
                editor.miniatura_de(grupo, biblioteca.ruta_miniatura(arbol.nombre))
            finally:
                cmds.delete(grupo)
            anadidos.append(arbol.nombre)
    finally:
        cmds.undoInfo(stateWithoutFlush=estado)
    return anadidos


# --- copias plantadas ------------------------------------------------------------

def _nombre_libre(base):
    n = 1
    while cmds.objExists("{}_{}".format(base, n)):
        n += 1
    return "{}_{}".format(base, n)


def plantar(arbol, posicion, nivel=NIVEL_POR_DEFECTO, giro=None, girar_al_azar=True, variantes=1,
            tamano=0.0, inclinacion=0.0):
    """Planta una copia ligada en ``posicion``. Devuelve el nombre del transform.

    ``variantes`` (1-4): la copia usa al azar una de esas formas del árbol. ``tamano`` (0.2 = ±20 %)
    e ``inclinacion`` (grados como mucho) cambian al azar la escala y la inclinación de la copia.
    """
    maestro = asegurar_maestro(arbol, nivel, var.sorteo(variantes))
    if giro is None:
        giro = random.uniform(0.0, 360.0) if girar_al_azar else 0.0
    escala, giro_x, giro_z = var.escala_e_inclinacion(tamano, inclinacion)
    cmds.undoInfo(openChunk=True, chunkName="Arboles_plantar")
    try:
        copia = cmds.group(empty=True, world=True, name=_nombre_libre(nombre_de_archivo(arbol.nombre)))
        cmds.addAttr(copia, longName=ATRIBUTO_PLANTADO, dataType="string")
        cmds.setAttr(copia + "." + ATRIBUTO_PLANTADO, maestro, type="string")
        cmds.parent(maestro, copia, addObject=True, relative=True)  # instancia del maestro
        cmds.xform(copia, worldSpace=True, translation=posicion)
        # La copia cuelga del mundo: sus valores locales son los del mundo, tal cual (sin que
        # Maya los cambie por otro giro equivalente).
        cmds.setAttr(copia + ".rotate", giro_x, giro, giro_z, type="double3")
        cmds.setAttr(copia + ".scale", escala, escala, escala, type="double3")
    finally:
        cmds.undoInfo(closeChunk=True)
    return cmds.ls(copia, long=True)[0]


def plantados():
    return [n for n in cmds.ls(type="transform", long=True) or []
            if cmds.attributeQuery(ATRIBUTO_PLANTADO, node=n, exists=True)]


def plantado_de(nodo):
    """La copia plantada que contiene ``nodo`` (o None)."""
    actual = nodo
    while actual:
        if cmds.attributeQuery(ATRIBUTO_PLANTADO, node=actual, exists=True):
            return actual
        padres = cmds.listRelatives(actual, parent=True, fullPath=True)
        actual = padres[0] if padres else None
    return None


def plantados_seleccionados():
    encontrados = []
    for nodo in cmds.ls(selection=True, long=True) or []:
        copia = plantado_de(nodo)
        if copia and copia not in encontrados:
            encontrados.append(copia)
    return encontrados


def desligar(copias):
    """Convierte cada copia en un árbol independiente (un paso de deshacer)."""
    nuevos = []
    cmds.undoInfo(openChunk=True, chunkName="Arboles_desligar")
    try:
        for copia in copias:
            nuevo = cmds.duplicate(copia, name=copia.split("|")[-1] + "_libre")[0]
            nuevo = cmds.ls(nuevo, long=True)[0]
            cmds.deleteAttr(nuevo + "." + ATRIBUTO_PLANTADO)
            cmds.delete(copia)
            nuevos.append(nuevo)
    finally:
        cmds.undoInfo(closeChunk=True)
    return nuevos


def informe():
    """(número de copias, triángulos de todas las copias)."""
    por_maestro = {}
    copias = plantados()
    for copia in copias:
        maestro = cmds.getAttr(copia + "." + ATRIBUTO_PLANTADO)
        por_maestro[maestro] = por_maestro.get(maestro, 0) + 1
    total = 0
    for maestro, n in por_maestro.items():
        if cm.existe(maestro):
            total += n * cm.triangulos(maestro)
    return len(copias), total


# --- clic sobre el suelo ------------------------------------------------------------

def _es_de_arboles(camino):
    """True si la malla es de un árbol (maestro, copia, editor): el suelo es lo demás."""
    nodo = om.MDagPath(camino)
    while nodo.length() > 0:
        fn = om.MFnDependencyNode(nodo.node())
        if fn.hasAttribute(cm.ATRIBUTO_RECETA) or fn.hasAttribute(ATRIBUTO_PLANTADO):
            return True
        if fn.name().startswith("arboles_"):
            return True
        nodo.pop()
    return False


def punto_en_suelo(origen, direccion):
    """Primer punto donde el rayo toca una malla visible que no sea un árbol.

    Si no hay ninguna, el plano del suelo (Y = 0). None si el rayo no baja hacia él.
    """
    mejor, distancia = None, float("inf")
    rayo_o = om.MFloatPoint(*origen)
    rayo_d = om.MFloatVector(*direccion)
    it = om.MItDag(om.MItDag.kDepthFirst, om.MFn.kMesh)
    while not it.isDone():
        camino = it.getPath()
        it.next()
        if not camino.isVisible() or om.MFnDagNode(camino).isIntermediateObject:
            continue
        if _es_de_arboles(camino):
            continue
        corte = om.MFnMesh(camino).closestIntersection(rayo_o, rayo_d, om.MSpace.kWorld, 1e7, False)
        if corte and corte[2] >= 0 and 0 < corte[1] < distancia:
            mejor, distancia = (corte[0].x, corte[0].y, corte[0].z), corte[1]
    if mejor is None and direccion[1] < -1e-6:
        t = -origen[1] / direccion[1]
        mejor = (origen[0] + direccion[0] * t, 0.0, origen[2] + direccion[2] * t)
    return mejor


def herramienta(obtener_arbol, nivel=lambda: NIVEL_POR_DEFECTO, girar=lambda: True, al_plantar=None,
                variacion=lambda: (1, 0.0, 0.0)):
    """Activa la herramienta: cada clic en el visor planta el árbol elegido. Esc para terminar."""
    def pulsar():
        arbol = obtener_arbol()
        if arbol is None:
            return
        x, y, _ = cmds.draggerContext(CONTEXTO, query=True, anchorPoint=True)
        punto = punto_en_suelo(*cm.rayo_del_visor(x, y))
        if punto is None:
            return
        variantes, tamano, inclinacion = variacion()
        copia = plantar(arbol, punto, nivel(), girar_al_azar=girar(), variantes=variantes, tamano=tamano,
                        inclinacion=inclinacion)
        if al_plantar:
            al_plantar(copia)

    if cmds.draggerContext(CONTEXTO, exists=True):
        cmds.deleteUI(CONTEXTO)
    cmds.draggerContext(CONTEXTO, pressCommand=pulsar, space="screen", cursor="crossHair",
                        name=CONTEXTO, undoMode="step")
    cmds.setToolTo(CONTEXTO)


def soltar_herramienta():
    if not cmds.about(batch=True) and cmds.draggerContext(CONTEXTO, exists=True):
        cmds.setToolTo("selectSuperContext")
