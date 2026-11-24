"""Construye en Maya las mallas y el follaje de un Arbol.

Todo se hace con la API de Maya (sin cmds) para que se pueda llamar desde el
deshacer del comando «arbolesAccion» del plugin. Los materiales se crean
antes, fuera del deshacer (``preparar(arbol)``): clay y, si el árbol tiene
juego de texturas instalado, los de su especie.

Estructura de un árbol en la escena::

    <grupo>            atributos arbolesReceta (JSON) y arbolesNivel
      <id de módulo>   malla de tronco o rama, atributo arbolesModulo
      follaje          una malla de hojas por rama (atributo arbolesModulo)
"""

import maya.api.OpenMaya as om
from maya import cmds

from arboles import follaje, materiales
from arboles.arbol import Arbol
from arboles.modulos import NIVELES

ATRIBUTO_RECETA = "arbolesReceta"
ATRIBUTO_NIVEL = "arbolesNivel"
ATRIBUTO_MODULO = "arbolesModulo"
ATRIBUTO_FOLLAJE = "arbolesFollaje"
CUADROS = "arboles_cuadros"
CORTEZA = "arboles_clay_corteza"
HOJA = "arboles_clay_hoja"


# --- utilidades de la API -----------------------------------------------------

def _objeto(nombre):
    sel = om.MSelectionList()
    sel.add(nombre)
    return sel.getDependNode(0)


def _camino(nombre):
    sel = om.MSelectionList()
    sel.add(nombre)
    return sel.getDagPath(0)


def existe(nombre):
    try:
        _objeto(nombre)
        return True
    except (RuntimeError, ValueError):
        return False


def _transformada(nombre, padre=None):
    fn = om.MFnDagNode()
    obj = fn.create("transform", nombre, padre if padre is not None else om.MObject.kNullObj)
    return obj


def _atributo_texto(obj, nombre, valor):
    fn = om.MFnDependencyNode(obj)
    if not fn.hasAttribute(nombre):
        atributo = om.MFnTypedAttribute().create(nombre, nombre, om.MFnData.kString)
        fn.addAttribute(atributo)
    fn.findPlug(nombre, False).setString(valor)


def leer_texto(nombre_nodo, atributo):
    fn = om.MFnDependencyNode(_objeto(nombre_nodo))
    if not fn.hasAttribute(atributo):
        return None
    return fn.findPlug(atributo, False).asString()


def _borrar(objetos):
    if not objetos:
        return
    mod = om.MDagModifier()
    for obj in objetos:
        mod.deleteNode(obj, False)  # sin borrar el padre si se queda vacío
    mod.doIt()


def _hijos(obj):
    fn = om.MFnDagNode(obj)
    return [fn.child(i) for i in range(fn.childCount())]


def _nombre(obj):
    return om.MFnDagNode(obj).partialPathName()


def _asignar(obj_forma, grupo_sombreado):
    """Asigna el material a la malla en todas sus instancias.

    Si la malla nace bajo un maestro ya plantado tiene varios caminos; con el
    MObject solo quedaría asignada una instancia y Arnold descartaría el resto.
    """
    conjunto = om.MFnSet(_objeto(grupo_sombreado))
    for camino in om.MDagPath.getAllPathsTo(obj_forma):
        conjunto.addMember((camino, om.MObject()))


def grupo_de(material):
    """Grupo de sombreado (shadingEngine) de un material, con la API."""
    plug = om.MFnDependencyNode(_objeto(material)).findPlug("outColor", False)
    for destino in plug.connectedTo(False, True):
        if destino.node().hasFn(om.MFn.kShadingEngine):
            return om.MFnDependencyNode(destino.node()).name()
    raise RuntimeError("{} no tiene grupo de sombreado".format(material))


def _crear_malla(datos, padre, nombre):
    puntos = [om.MPoint(*p) for p in datos.vertices]
    fn = om.MFnMesh()
    forma = fn.create(puntos, datos.conteos, datos.conexiones, datos.us, datos.vs, padre)
    fn.assignUVs(datos.conteos, datos.uv_ids)
    aristas = list(range(fn.numEdges))
    fn.setEdgeSmoothings(aristas, [True] * len(aristas))
    fn.cleanupEdgeSmoothing()
    fn.updateSurface()
    om.MFnDependencyNode(forma).setName(nombre + "Shape")
    return forma


# --- preparación (fuera del deshacer) -----------------------------------------

def resolucion_texturas():
    """Resolución elegida en el menú (1K si no hay preferencias, p. ej. en batch)."""
    from arboles import texturas
    try:
        from arboles import interfaz_maya
        return interfaz_maya.cargar_ajustes().resolucion_texturas
    except Exception:  # sin preferencias legibles: la de por defecto
        return texturas.RESOLUCION_POR_DEFECTO


def estilo_texturas():
    """Estilo elegido en el menú (realista si no hay preferencias)."""
    from arboles import texturas
    try:
        from arboles import interfaz_maya
        return interfaz_maya.cargar_ajustes().estilo_texturas
    except Exception:
        return texturas.ESTILO_POR_DEFECTO


def preparar(arbol=None):
    """Materiales clay y, si ``arbol`` tiene juego de texturas instalado, los suyos.

    Usa cmds: llamar antes de construir (fuera del deshacer).
    """
    corteza = materiales.crear_material(CORTEZA)[1]
    hoja = materiales.crear_material(HOJA)[1]
    resolucion_texturas()  # lee los ajustes: registra también los materiales propios de la biblioteca
    if arbol is not None and materiales.tx.existe(arbol.material):
        resolucion, estilo = resolucion_texturas(), estilo_texturas()
        corteza = materiales.crear_material_texturas(arbol.material, "corteza", resolucion, estilo)[1]
        hoja = materiales.crear_material_texturas(arbol.material, "hoja", resolucion, estilo)[1]
    return corteza, hoja


def _grupo_material(arbol, parte, clay):
    """Grupo de sombreado del material de ``parte``; el clay si el de texturas no está en la escena."""
    nombre = materiales.nombre_material(arbol.material, parte)
    if nombre != clay and existe(nombre):
        try:
            return grupo_de(nombre)
        except RuntimeError:
            pass
    return grupo_de(clay)


# --- construcción ---------------------------------------------------------------

def _construir_modulo(grupo, arbol, modulo, nivel, sg_corteza):
    from arboles import modulos as mod
    datos = mod.malla_modulo(modulo.guia, nivel, modulo.id, modulo.valores["torsion"], arbol.escala_textura)
    t = _transformada(modulo.id, grupo)
    _atributo_texto(t, ATRIBUTO_MODULO, modulo.id)
    _asignar(_crear_malla(datos, t, modulo.id), sg_corteza)
    return t


def _construir_follaje(contenedor, modulo, nivel, sg_hoja):
    from arboles import follaje as fol
    matrices = fol.colocar(modulo)
    if not matrices:
        return None
    nombre = modulo.id + "_hojas"
    datos = fol.combinar(modulo.valores["follaje"], nivel, matrices, nombre)
    t = _transformada(nombre, contenedor)
    _atributo_texto(t, ATRIBUTO_MODULO, modulo.id)
    _asignar(_crear_malla(datos, t, nombre), sg_hoja)
    return t


def _contenedor_follaje(grupo, crear=True):
    for h in _hijos(grupo):
        if om.MFnDependencyNode(h).hasAttribute(ATRIBUTO_FOLLAJE):
            return h
    if not crear:
        return None
    contenedor = _transformada("follaje", grupo)
    _atributo_texto(contenedor, ATRIBUTO_FOLLAJE, "1")
    return contenedor


def _modulo_de(obj):
    fn = om.MFnDependencyNode(obj)
    return fn.findPlug(ATRIBUTO_MODULO, False).asString() if fn.hasAttribute(ATRIBUTO_MODULO) else None


def reconstruir(grupo, arbol, nivel, ids=None, guardar_receta=True):
    """(Re)construye en ``grupo`` los módulos ``ids`` (todos si es None) al ``nivel``.

    Quita las mallas y el follaje de módulos que ya no existen en el árbol.
    """
    grupo_obj = _objeto(grupo)
    sg_corteza = _grupo_material(arbol, "corteza", CORTEZA)
    sg_hoja = _grupo_material(arbol, "hoja", HOJA)
    arbol.calcular()
    todos = set(arbol.modulos)
    rehacer = todos if ids is None else set(ids) & todos
    contenedor = _contenedor_follaje(grupo_obj)
    viejos = []
    for h in _hijos(grupo_obj):
        id_ = _modulo_de(h)
        if id_ is not None and (id_ in rehacer or id_ not in todos):
            viejos.append(h)
    for h in _hijos(contenedor):
        id_ = _modulo_de(h)
        if id_ is not None and (id_ in rehacer or id_ not in todos):
            viejos.append(h)
    _borrar(viejos)
    for m in arbol._orden():
        if m.id in rehacer:
            _construir_modulo(grupo_obj, arbol, m, nivel, sg_corteza)
            _construir_follaje(contenedor, m, nivel, sg_hoja)
    if guardar_receta:
        _atributo_texto(grupo_obj, ATRIBUTO_RECETA, arbol.a_json())
    _atributo_texto(grupo_obj, ATRIBUTO_NIVEL, nivel)
    return grupo


def crear(arbol, nivel="denso", nombre=None, posicion=None):
    """Crea un grupo nuevo con el árbol y devuelve su nombre. Llamar a preparar(arbol) antes."""
    obj = _transformada((nombre or arbol.nombre))
    if posicion:
        om.MFnTransform(obj).setTranslation(om.MVector(*posicion), om.MSpace.kTransform)
    grupo = om.MFnDagNode(obj).fullPathName()
    reconstruir(grupo, arbol, nivel)
    return grupo


def borrar(grupo):
    _borrar([_objeto(grupo)])


# --- consultas ------------------------------------------------------------------

def es_arbol(nodo):
    return existe(nodo) and leer_texto(nodo, ATRIBUTO_RECETA) is not None


def arbol_de(grupo):
    return Arbol.de_json(leer_texto(grupo, ATRIBUTO_RECETA))


def modulo_de_nodo(nodo):
    """(grupo del árbol, id del módulo) de una malla u hoja seleccionada."""
    actual = nodo
    modulo = None
    while actual:
        if modulo is None and existe(actual):
            modulo = leer_texto(actual, ATRIBUTO_MODULO) or None
        if es_arbol(actual):
            return actual, modulo
        padres = cmds.listRelatives(actual, parent=True, fullPath=True)
        actual = padres[0] if padres else None
    return None, None


def grupos_seleccionados():
    encontrados = []
    for nodo in cmds.ls(selection=True, long=True) or []:
        grupo, _ = modulo_de_nodo(nodo)
        if grupo and grupo not in encontrados:
            encontrados.append(grupo)
    return encontrados


def mallas(grupo):
    return [om.MFnDagNode(h).fullPathName() for h in _hijos(_objeto(grupo)) if _modulo_de(h)]


def triangulos(grupo):
    total = 0
    for nombre in mallas(grupo):
        total += cmds.polyEvaluate(nombre, triangle=True)
    contenedor = _contenedor_follaje(_objeto(grupo), crear=False)
    for hojas in (_hijos(contenedor) if contenedor is not None else []):
        camino = om.MDagPath.getAPathTo(hojas)
        camino.extendToShape()
        total += sum(om.MFnMesh(camino).getTriangles()[0])
    return total


def generar(grupo, nivel):
    """Reconstruye el árbol del grupo al nivel indicado (fuera del editor)."""
    if nivel not in NIVELES:
        raise ValueError("nivel desconocido: {}".format(nivel))
    arbol = arbol_de(grupo)
    preparar(arbol)
    return reconstruir(grupo, arbol, nivel)


def textura_cuadros(activar=True, repeticiones=8):
    """Pone (o quita) una textura de cuadros en la corteza para revisar las UVs."""
    material, _ = materiales.crear_material(CORTEZA)
    destino = material + ".baseColor"
    if activar:
        if not cmds.objExists(CUADROS):
            cmds.shadingNode("checker", asTexture=True, name=CUADROS)
            colocacion = cmds.shadingNode("place2dTexture", asUtility=True, name=CUADROS + "_place")
            cmds.connectAttr(colocacion + ".outUV", CUADROS + ".uvCoord")
            cmds.connectAttr(colocacion + ".outUvFilterSize", CUADROS + ".uvFilterSize")
        colocacion = CUADROS + "_place"
        cmds.setAttr(colocacion + ".repeatU", repeticiones)
        cmds.setAttr(colocacion + ".repeatV", repeticiones)
        cmds.connectAttr(CUADROS + ".outColor", destino, force=True)
    else:
        for origen in cmds.listConnections(destino, plugs=True, source=True, destination=False) or []:
            cmds.disconnectAttr(origen, destino)
        color = materiales.CLAY[CORTEZA][0]
        cmds.setAttr(destino, *color, type="double3")
    return activar


def rayo_del_visor(x, y):
    """((origen), (dirección)) en mundo del píxel (x, y) del visor activo.

    Usa la API 1: en la API 2 la firma de viewToWorld cambia entre versiones
    de Maya (en 2027 pide cuatro argumentos).
    """
    import maya.OpenMaya as om1
    import maya.OpenMayaUI as omui1
    origen, direccion = om1.MPoint(), om1.MVector()
    omui1.M3dView.active3dView().viewToWorld(int(x), int(y), origen, direccion)
    return (origen.x, origen.y, origen.z), (direccion.x, direccion.y, direccion.z)
