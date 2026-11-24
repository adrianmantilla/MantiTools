"""Todo lo que GrassEditor crea en la escena de Maya, y las funciones para manejarlo.

Estructura::

    grasseditor                         grupo raíz
      grasseditor_prototipos            oculto: las matas de cada tipo
        grasseditor_<tipo>              6 variantes × 3 niveles: grasseditor_<tipo>_v0_n0 ...
      <capa>_instancias             un instanciador por capa
    grasseditor_ajustes   (network)     catálogo de tipos, material y «en render»
    <capa>            (grassEditorCapa) el nodo de cada capa: ajustes, máscara, horneado

Los prototipos se comparten entre capas: si dos capas usan césped, el
césped se guarda una vez. El índice de cada mata en el instanciador es
``hueco_de_la_mezcla * 18 + variante * 3 + nivel``.
"""

import json
import math

import maya.api.OpenMaya as om
from maya import cmds

from grasseditor import capa as cp
from grasseditor import matas, tipos
from grasseditor.i18n import t
from grasseditor.tipos import NIVELES, VARIANTES

RAIZ = "grasseditor"
PROTOTIPOS = "grasseditor_prototipos"
AJUSTES = "grasseditor_ajustes"
TIPO_NODO = "grassEditorCapa"
MATERIAL = "grasseditor_hierba"
SG = "grasseditor_hierba_SG"
ATRIBUTO_FIRMA = "grassEditorFirma"
ATRIBUTO_CANTERA = "canteraPieza"      # contrato con Cantera: sus piezas llevan este atributo
ATRIBUTO_ARBOLES = "arbolesPlantado"   # copias plantadas con Árboles
_BRILLO = 1.15


# --- utilidades -------------------------------------------------------------------------

def _con_gestion_de_color():
    try:
        return bool(cmds.colorManagementPrefs(query=True, cmEnabled=True))
    except (RuntimeError, TypeError):
        return False


def _a_lineal(color, lineal=True, brillo=1.0):
    """Color de pantalla (sRGB) a lineal, como hace Trepadora con sus hojas."""
    if not lineal:
        return tuple(color[:3])
    return tuple(min(1.0, brillo * (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4))
                 for c in color[:3])


def _objeto(nombre):
    sel = om.MSelectionList()
    sel.add(nombre)
    return sel.getDependNode(0)


def _camino(nombre):
    sel = om.MSelectionList()
    sel.add(nombre)
    return sel.getDagPath(0)


def leer_suelo(forma, matriz):
    """Suelo de reparto.py a partir de la forma de malla ``forma`` (nombre), o None."""
    if not forma:
        return None
    from grasseditor import reparto
    fn = om.MFnMesh(_camino(forma))
    puntos = fn.getPoints(om.MSpace.kObject)
    por_cara, vertices = fn.getTriangles()
    caras = []
    for cara, n in enumerate(por_cara):
        caras.extend([cara] * n)
    return reparto.Suelo([(p.x, p.y, p.z) for p in puntos], list(vertices), caras, matriz)


def _conectar(origen, destino):
    """connectAttr sin el aviso «already connected» si el enlace ya existe."""
    if not cmds.isConnected(origen, destino):
        cmds.connectAttr(origen, destino, force=True)


def _sin_deshacer(funcion):
    """Ejecuta ``funcion`` fuera de la cola de deshacer (para cosas internas como los prototipos)."""
    estado = cmds.undoInfo(query=True, stateWithoutFlush=True)
    cmds.undoInfo(stateWithoutFlush=False)
    try:
        return funcion()
    finally:
        cmds.undoInfo(stateWithoutFlush=estado)


def nombre_valido(nombre):
    from grasseditor.tipos import clave_libre
    return clave_libre(nombre, set())


# --- raíz y ajustes ----------------------------------------------------------------------

def asegurar_raiz():
    if not cmds.objExists("|" + RAIZ):
        cmds.group(empty=True, world=True, name=RAIZ)
    if not cmds.objExists("|{}|{}".format(RAIZ, PROTOTIPOS)):
        cmds.group(empty=True, parent="|" + RAIZ, name=PROTOTIPOS)
        cmds.setAttr("|{}|{}.visibility".format(RAIZ, PROTOTIPOS), 0)
    return "|" + RAIZ


def asegurar_ajustes():
    if not cmds.objExists(AJUSTES):
        cmds.createNode("network", name=AJUSTES)
        cmds.addAttr(AJUSTES, longName="tipos", dataType="string")
        cmds.setAttr(AJUSTES + ".tipos", "{}", type="string")
        cmds.addAttr(AJUSTES, longName="enRender", attributeType="bool", defaultValue=False)
        cmds.addAttr(AJUSTES, longName="material", dataType="string")
        cmds.setAttr(AJUSTES + ".material", "hierba", type="string")
        cmds.addAttr(AJUSTES, longName="translucidez", attributeType="double", defaultValue=0.5)
        cmds.addAttr(AJUSTES, longName="version", dataType="string")
    import grasseditor
    cmds.setAttr(AJUSTES + ".version", grasseditor.__version__, type="string")
    return AJUSTES


def catalogo():
    if not cmds.objExists(AJUSTES):
        return tipos.Catalogo()
    return tipos.Catalogo.desde_json(cmds.getAttr(AJUSTES + ".tipos") or "")


def guardar_tipo(tipo):
    """Guarda ``tipo`` en el catálogo de la escena y rehace sus prototipos si existen."""
    asegurar_ajustes()
    cat = catalogo()
    cat.poner(tipo)
    cmds.setAttr(AJUSTES + ".tipos", cat.a_json(), type="string")
    if cmds.objExists(_grupo_tipo(tipo.clave)):
        prototipos(tipo.clave, cat)
    return tipo


def restaurar_tipo(clave):
    """Vuelve a los valores de serie del tipo ``clave``."""
    if clave in tipos.SERIE:
        return guardar_tipo(tipos.de_serie(clave))
    return None


def fijar_render(activo):
    """Pone toda la hierba en calidad de render (True) o de visor (False)."""
    if cmds.objExists(AJUSTES):
        cmds.setAttr(AJUSTES + ".enRender", bool(activo))


def en_render():
    return cmds.objExists(AJUSTES) and bool(cmds.getAttr(AJUSTES + ".enRender"))


_MEL_ANTES = "if (`exists grassEditorRender`) grassEditorRender -antes;"
_MEL_DESPUES = "if (`exists grassEditorRender`) grassEditorRender -despues;"


def instalar_ganchos():
    """Añade a los MEL de antes y después del render el cambio a calidad de render.

    Se escriben con ``exists`` para que la escena se pueda renderizar en un
    ordenador sin GrassEditor. No se borra lo que ya hubiera en esos campos.
    """
    for atributo, linea in (("preMel", _MEL_ANTES), ("postMel", _MEL_DESPUES)):
        plug = "defaultRenderGlobals." + atributo
        actual = cmds.getAttr(plug) or ""
        if linea not in actual:
            nuevo = (actual.rstrip().rstrip(";") + "; " + linea) if actual.strip() else linea
            cmds.setAttr(plug, nuevo, type="string")


# --- materiales ----------------------------------------------------------------------------

def _arnold():
    try:
        if not cmds.pluginInfo("mtoa", query=True, loaded=True):
            cmds.loadPlugin("mtoa", quiet=True)
        return True
    except RuntimeError:
        return False


def asegurar_materiales():
    """El grupo de sombreado de la hierba: color de los vértices en el visor y en Arnold."""
    if not cmds.objExists(SG):
        material = cmds.shadingNode("lambert", asShader=True, name=MATERIAL)
        cmds.setAttr(material + ".color", 0.25, 0.45, 0.15, type="double3")
        grupo = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=SG)
        _conectar(material + ".outColor", grupo + ".surfaceShader")
    if _arnold():
        _materiales_arnold()
        fijar_material(material_actual())
    return SG


def _materiales_arnold():
    hierba = MATERIAL + "_ai"
    if not cmds.objExists(hierba):
        hierba = cmds.shadingNode("aiStandardSurface", asShader=True, name=hierba)
        dato = cmds.shadingNode("aiUserDataColor", asUtility=True, name=MATERIAL + "_color_ai")
        cmds.setAttr(dato + ".attribute", "colorSet1", type="string")
        cmds.setAttr(dato + ".default", 0.05, 0.2, 0.03, type="double3")
        _conectar(dato + ".outColor", hierba + ".baseColor")
        _conectar(dato + ".outColor", hierba + ".subsurfaceColor")
        # Hoja fina: la luz la atraviesa (subsurface con thinWalled) y un poco de
        # sheen da el brillo aterciopelado que tiene la hierba a contraluz.
        for atributo, valor in (("base", 1.0), ("specular", 0.25), ("specularRoughness", 0.5),
                                ("thinWalled", 1), ("subsurface", 0.5), ("sheen", 0.25),
                                ("sheenRoughness", 0.4)):
            if cmds.attributeQuery(atributo, node=hierba, exists=True):
                cmds.setAttr(hierba + "." + atributo, valor)
        if cmds.attributeQuery("sheenColor", node=hierba, exists=True):
            cmds.setAttr(hierba + ".sheenColor", 0.75, 0.85, 0.55, type="double3")
    clay = "grasseditor_clay_ai"
    if not cmds.objExists(clay):
        clay = cmds.shadingNode("aiStandardSurface", asShader=True, name=clay)
        cmds.setAttr(clay + ".baseColor", 0.55, 0.53, 0.5, type="double3")
        cmds.setAttr(clay + ".specular", 0.2)
        cmds.setAttr(clay + ".specularRoughness", 0.6)
        cmds.setAttr(clay + ".thinWalled", 1)


SUELO_MATERIAL = "grasseditor_suelo"
SUELO_SG = "grasseditor_suelo_SG"
COLOR_SUELO = (0.075, 0.095, 0.04)   # verde oscuro, casi tierra: disimula los huecos entre matas


def tenir_suelo(suelo_tr, color=None):
    """Asigna al suelo un material verde oscuro para que no se vea tierra entre las matas.

    Es un material normal de Maya (y de Arnold si está cargado): se puede
    cambiar o quitar como cualquier otro. Un paso de Ctrl+Z.
    """
    color = tuple(color or COLOR_SUELO)
    cmds.undoInfo(openChunk=True, chunkName="GrassEditor_tenir_suelo")
    try:
        if not cmds.objExists(SUELO_SG):
            lambert = cmds.shadingNode("lambert", asShader=True, name=SUELO_MATERIAL)
            grupo = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=SUELO_SG)
            _conectar(lambert + ".outColor", grupo + ".surfaceShader")
        cmds.setAttr(SUELO_MATERIAL + ".color", *color, type="double3")
        if _arnold() and cmds.attributeQuery("aiSurfaceShader", node=SUELO_SG, exists=True):
            ai = SUELO_MATERIAL + "_ai"
            if not cmds.objExists(ai):
                ai = cmds.shadingNode("aiStandardSurface", asShader=True, name=ai)
                cmds.setAttr(ai + ".specular", 0.1)
                cmds.setAttr(ai + ".specularRoughness", 0.8)
            cmds.setAttr(ai + ".baseColor", *color, type="double3")
            _conectar(ai + ".outColor", SUELO_SG + ".aiSurfaceShader")
        cmds.sets(suelo_tr, edit=True, forceElement=SUELO_SG)
    finally:
        cmds.undoInfo(closeChunk=True)
    return SUELO_SG


def material_actual():
    if cmds.objExists(AJUSTES):
        return cmds.getAttr(AJUSTES + ".material") or "hierba"
    return "hierba"


def fijar_material(material, translucidez=None):
    """«hierba» (color de cada mata, con luz que la atraviesa) o «clay» (gris, como Árboles)."""
    asegurar_ajustes()
    material = material if material in ("hierba", "clay") else "hierba"
    cmds.setAttr(AJUSTES + ".material", material, type="string")
    if translucidez is not None:
        cmds.setAttr(AJUSTES + ".translucidez", float(translucidez))
    if not cmds.objExists(SG) or not _arnold():
        return material
    _materiales_arnold()
    if cmds.attributeQuery("aiSurfaceShader", node=SG, exists=True):
        origen = (MATERIAL + "_ai" if material == "hierba" else "grasseditor_clay_ai") + ".outColor"
        _conectar(origen, SG + ".aiSurfaceShader")
    cmds.setAttr(MATERIAL + "_ai.subsurface", float(cmds.getAttr(AJUSTES + ".translucidez")))
    for forma in cmds.ls("grasseditor_*_v*_n*Shape", type="mesh", long=True) or []:
        cmds.setAttr(forma + ".displayColors", 1 if material == "hierba" else 0)
    return material


# --- prototipos ----------------------------------------------------------------------------

def _grupo_tipo(clave):
    return "|{}|{}|grasseditor_{}".format(RAIZ, PROTOTIPOS, clave)


def nombre_prototipo(clave, variante, nivel):
    return "grasseditor_{}_v{}_n{}".format(clave, variante, nivel)


def _firma(tipo):
    import grasseditor
    return json.dumps([tipo.a_dict(), grasseditor.__version__], sort_keys=True)


def _crear_malla(malla, transform, lineal):
    """Crea la forma de ``malla`` bajo el transform existente ``transform``."""
    fn = om.MFnMesh()
    puntos = om.MPointArray([om.MPoint(*p) for p in malla.vertices])
    us = om.MFloatArray([u for u, _ in malla.uvs])
    vs = om.MFloatArray([v for _, v in malla.uvs])
    forma = fn.create(puntos, malla.conteos, malla.indices, us, vs, _objeto(transform))
    fn.assignUVs(om.MIntArray(malla.conteos), om.MIntArray(malla.indices))
    fn.createColorSet("colorSet1", True)
    fn.setCurrentColorSetName("colorSet1")
    colores = om.MColorArray([om.MColor(_a_lineal(c, lineal, _BRILLO) + (1.0,)) for c in malla.colores])
    fn.setVertexColors(colores, list(range(len(malla.vertices))))
    try:
        aristas = fn.numEdges
        fn.setEdgeSmoothings(list(range(aristas)), [True] * aristas)
        fn.cleanupEdgeSmoothing()
        fn.updateSurface()
    except (AttributeError, RuntimeError, TypeError):
        pass
    nombre = om.MFnDagNode(forma).fullPathName()
    nombre = cmds.rename(nombre, transform.split("|")[-1] + "Shape")
    nombre = cmds.ls(nombre, long=True)[0]
    cmds.setAttr(nombre + ".displayColors", 1 if material_actual() == "hierba" else 0)
    for atributo, valor in (("aiExportColors", 1), ("castsShadows", 1), ("doubleSided", 1)):
        if cmds.attributeQuery(atributo, node=nombre, exists=True):
            cmds.setAttr(nombre + "." + atributo, valor)
    cmds.sets(nombre, edit=True, forceElement=SG)
    return nombre


def prototipos(clave, cat=None):
    """Las 18 rutas (variante × nivel) de los prototipos del tipo ``clave``; las crea o rehace."""
    cat = cat or catalogo()
    tipo = cat[clave]

    def hacer():
        asegurar_raiz()
        asegurar_materiales()
        grupo = _grupo_tipo(clave)
        if not cmds.objExists(grupo):
            cmds.group(empty=True, parent="|{}|{}".format(RAIZ, PROTOTIPOS), name="grasseditor_" + clave)
        if not cmds.attributeQuery(ATRIBUTO_FIRMA, node=grupo, exists=True):
            cmds.addAttr(grupo, longName=ATRIBUTO_FIRMA, dataType="string")
        firma = _firma(tipo)
        al_dia = cmds.getAttr(grupo + "." + ATRIBUTO_FIRMA) == firma
        lineal = _con_gestion_de_color()
        rutas = []
        for v in range(VARIANTES):
            for n in range(NIVELES):
                ruta = "{}|{}".format(grupo, nombre_prototipo(clave, v, n))
                existe = cmds.objExists(ruta)
                if existe and al_dia and cmds.listRelatives(ruta, shapes=True):
                    rutas.append(ruta)
                    continue
                if not existe:
                    cmds.createNode("transform", name=nombre_prototipo(clave, v, n), parent=grupo)
                for forma in cmds.listRelatives(ruta, shapes=True, fullPath=True) or []:
                    cmds.delete(forma)
                _crear_malla(matas.mata(tipo, v, n), ruta, lineal)
                rutas.append(ruta)
        cmds.setAttr(grupo + "." + ATRIBUTO_FIRMA, firma, type="string")
        return rutas

    return _sin_deshacer(hacer)


def triangulos_prototipos():
    """Triángulos de todos los prototipos de la escena (la geometría que se guarda de verdad)."""
    total = 0
    for forma in cmds.ls("grasseditor_*_v*_n*Shape", type="mesh") or []:
        total += cmds.polyEvaluate(forma, triangle=True)
    return total


# --- capas -------------------------------------------------------------------------------

def capas():
    """Nodos de capa de la escena, en orden de creación."""
    return cmds.ls(type=TIPO_NODO) or []


def ajustes(capa):
    return cp.AjustesCapa.desde_json(cmds.getAttr(capa + ".ajustes") or "")


def guardar_ajustes(capa, nuevos, reconectar=None):
    """Guarda los ajustes (un paso de Ctrl+Z). Si cambia la mezcla, reconecta los prototipos."""
    viejos = ajustes(capa)
    if reconectar is None:
        reconectar = viejos.claves() != nuevos.claves()
    cmds.undoInfo(openChunk=True, chunkName="GrassEditor_ajustes")
    try:
        if reconectar:
            for clave in nuevos.claves():
                prototipos(clave)
        cmds.setAttr(capa + ".ajustes", nuevos.a_json(), type="string")
        if reconectar:
            _sin_deshacer(lambda: reconectar_prototipos(capa))
        instancias = instanciador(capa)
        if instancias:
            _fijar_si_cambia(instancias + ".visibility", 1 if nuevos.activa else 0)
            if cmds.attributeQuery("levelOfDetail", node=instancias, exists=True):
                _fijar_si_cambia(instancias + ".levelOfDetail",
                                 1 if nuevos.opciones.get("visor_como") == "cajas" else 0)
    finally:
        cmds.undoInfo(closeChunk=True)
    return nuevos


def _fijar_si_cambia(atributo, valor):
    if cmds.getAttr(atributo) != valor:
        cmds.setAttr(atributo, valor)


def instanciador(capa):
    conectados = cmds.listConnections(capa + ".salida", destination=True, source=False, type="instancer") or []
    return cmds.ls(conectados[0], long=True)[0] if conectados else None


def suelo(capa):
    """Transform del suelo de la capa (o None)."""
    formas = cmds.listConnections(capa + ".suelo", source=True, destination=False, shapes=True) or []
    if not formas:
        return None
    padre = cmds.listRelatives(formas[0], parent=True, fullPath=True)
    return padre[0] if padre else None


def forma_suelo(capa):
    formas = cmds.listConnections(capa + ".suelo", source=True, destination=False, shapes=True) or []
    return cmds.ls(formas[0], long=True)[0] if formas else None


def reconectar_prototipos(capa):
    instancias = instanciador(capa)
    if not instancias:
        return
    for indice in cmds.getAttr(instancias + ".inputHierarchy", multiIndices=True) or []:
        plug = "{}.inputHierarchy[{}]".format(instancias, indice)
        for origen in cmds.listConnections(plug, source=True, destination=False, plugs=True) or []:
            cmds.disconnectAttr(origen, plug)
        cmds.removeMultiInstance(plug, b=True)
    cat = catalogo()
    i = 0
    for clave in ajustes(capa).claves():
        rutas = prototipos(clave, cat) if clave in cat else []
        for ruta in rutas:
            cmds.connectAttr(ruta + ".matrix", "{}.inputHierarchy[{}]".format(instancias, i), force=True)
            i += 1


def _forma_y_transform(objeto):
    if cmds.nodeType(objeto) == "mesh":
        return objeto, cmds.listRelatives(objeto, parent=True, fullPath=True)[0]
    formas = cmds.listRelatives(objeto, shapes=True, fullPath=True, noIntermediate=True, type="mesh") or []
    return (formas[0], objeto) if formas else (None, None)


def suelo_de_seleccion():
    """(transform del suelo, caras o None) a partir de la selección; (None, None) si no hay malla."""
    seleccion = cmds.ls(selection=True, long=True, flatten=False) or []
    caras = []
    suelo_tr = None
    for elemento in seleccion:
        if ".f[" in elemento:
            objeto = elemento.split(".")[0]
            _, tr = _forma_y_transform(objeto)
            if tr:
                suelo_tr = suelo_tr or tr
                if tr == suelo_tr:
                    for cara in cmds.ls(elemento, flatten=True):
                        caras.append(int(cara.rsplit("[", 1)[1].rstrip("]")))
        else:
            forma, tr = _forma_y_transform(elemento)
            if forma and not suelo_tr:
                suelo_tr = tr
    return suelo_tr, (sorted(set(caras)) or None)


def nombre_libre(base):
    nombre, n = base, 2
    while cmds.objExists(nombre) or cmds.objExists(nombre + "_instancias"):
        nombre = "{}{}".format(base, n)
        n += 1
    return nombre


def crear_capa(suelo_tr, caras=None, nombre=None, mezcla=None, zona="objeto", opciones=None, reglas=None,
               densidad=None, semilla=None):
    """Crea una capa de hierba sobre ``suelo_tr`` (un paso de Ctrl+Z). Devuelve el nodo.

    ``zona``: «objeto» (todo el suelo) o «pincel» (empieza vacía para pintar).
    """
    forma, suelo_tr = _forma_y_transform(suelo_tr)
    if forma is None:
        raise ValueError(t("error_sin_malla"))
    nombre = nombre_libre(nombre_valido(nombre or "grasseditor_capa"))
    from grasseditor import preferencias
    mezcla = mezcla or [[preferencias.leer("tipo_inicial"), 100.0]]
    if densidad is None:
        densidad = float(preferencias.leer("densidad_inicial"))
    cmds.undoInfo(openChunk=True, chunkName="GrassEditor_crear_capa")
    try:
        asegurar_raiz()
        asegurar_ajustes()
        asegurar_materiales()
        for clave, _ in mezcla:
            prototipos(clave)
        nodo = cmds.createNode(TIPO_NODO, name=nombre)
        cmds.connectAttr(forma + ".outMesh", nodo + ".suelo")
        cmds.connectAttr(forma + ".worldMatrix[0]", nodo + ".sueloMatriz")
        cmds.connectAttr(AJUSTES + ".tipos", nodo + ".tipos")
        cmds.connectAttr(AJUSTES + ".enRender", nodo + ".enRender")
        if cmds.objExists("defaultResolution"):
            cmds.connectAttr("defaultResolution.deviceAspectRatio", nodo + ".aspecto")
        objetos, copas = objetos_automaticos(excluir=suelo_tr)
        reglas = dict(reglas or {})
        reglas.setdefault("objetos", objetos)
        reglas.setdefault("copas", copas)
        aj = cp.AjustesCapa(mezcla=mezcla, densidad=densidad, caras=caras, reglas=reglas, opciones=opciones,
                            semilla=semilla if semilla is not None else (len(capas()) * 7 + 1))
        cmds.setAttr(nodo + ".ajustes", aj.a_json(), type="string")
        if zona == "pincel":
            from grasseditor.mascara import Mascara
            caja = leer_suelo(forma, None).caja_local()
            cmds.setAttr(nodo + ".mascara", Mascara(caja, 0).a_texto(), type="string")
        instancias = cmds.createNode("instancer", name=nombre + "_instancias", parent="|" + RAIZ)
        instancias = cmds.ls(instancias, long=True)[0]
        for atributo, valor in (("rotationAngleUnits", 0), ("rotationOrder", 0)):
            if cmds.attributeQuery(atributo, node=instancias, exists=True):
                cmds.setAttr(instancias + "." + atributo, valor)
        cmds.connectAttr(nodo + ".salida", instancias + ".inputPoints")
        reconectar_prototipos(nodo)
        camara = camara_render()
        if camara:
            conectar_camara(nodo, camara)
        if preferencias.leer("render_automatico"):
            instalar_ganchos()
    finally:
        cmds.undoInfo(closeChunk=True)
    return nodo


def borrar_capa(capa):
    cmds.undoInfo(openChunk=True, chunkName="GrassEditor_borrar_capa")
    try:
        # Al borrar el instanciador Maya puede llevarse también el nodo (su historia)
        for nodo in (instanciador(capa), capa):
            if nodo and cmds.objExists(nodo):
                cmds.delete(nodo)
    finally:
        cmds.undoInfo(closeChunk=True)


def duplicar_capa(capa):
    suelo_tr = suelo(capa)
    aj = ajustes(capa)
    aj.semilla += 1
    nuevo = crear_capa(suelo_tr, aj.caras, capa + "_copia", aj.mezcla, opciones=aj.opciones, reglas=aj.reglas,
                       densidad=aj.densidad, semilla=aj.semilla)
    cmds.setAttr(nuevo + ".mascara", cmds.getAttr(capa + ".mascara") or "", type="string")
    return nuevo


# --- cámara -----------------------------------------------------------------------------

def camaras():
    """Transforms de las cámaras de la escena (las de render primero)."""
    resultado = []
    for forma in cmds.ls(type="camera", long=True) or []:
        tr = cmds.listRelatives(forma, parent=True, fullPath=True)[0]
        resultado.append((not cmds.getAttr(forma + ".renderable"), cmds.camera(forma, query=True,
                                                                              startupCamera=True), tr))
    resultado.sort()
    return [tr for _, _, tr in resultado]


def camara_render():
    lista = camaras()
    return lista[0] if lista else None


def conectar_camara(capa, camara):
    forma = cmds.listRelatives(camara, shapes=True, fullPath=True, type="camera")
    if not forma:
        return False
    forma = forma[0]
    _conectar(forma + ".worldMatrix[0]", capa + ".camMatriz")
    _conectar(forma + ".focalLength", capa + ".camFocal")
    _conectar(forma + ".horizontalFilmAperture", capa + ".camApertura")
    cmds.setAttr(capa + ".conCamara", True)
    return True


def camara_de(capa):
    origen = cmds.listConnections(capa + ".camMatriz", source=True, destination=False) or []
    return cmds.ls(origen[0], long=True)[0] if origen else None


# --- objetos que apartan la hierba --------------------------------------------------------

def _caja_xz(nodo):
    x0, _, z0, x1, _, z1 = cmds.exactWorldBoundingBox(nodo)
    return (x0 + x1) / 2.0, (z0 + z1) / 2.0, max(x1 - x0, z1 - z0) / 2.0


def objetos_automaticos(excluir=None):
    """([(x, z, r)] de troncos y piedras, [(x, z, r)] de copas) de Árboles y Cantera."""
    objetos, copas = [], []
    for nodo in cmds.ls("*." + ATRIBUTO_ARBOLES, objectsOnly=True, long=True) or []:
        if excluir and nodo == excluir:
            continue
        x, z, r = _caja_xz(nodo)
        escala = cmds.getAttr(nodo + ".scaleX")
        objetos.append((round(x, 2), round(z, 2), round(max(15.0, 25.0 * escala), 2)))
        copas.append((round(x, 2), round(z, 2), round(r * 0.8, 2)))
    for nodo in cmds.ls("*." + ATRIBUTO_CANTERA, objectsOnly=True, long=True) or []:
        if excluir and nodo == excluir:
            continue
        x, z, r = _caja_xz(nodo)
        objetos.append((round(x, 2), round(z, 2), round(r * 0.85, 2)))
    return objetos, copas


def objetos_de_seleccion():
    """[(x, z, r)] de los objetos seleccionados (su caja vista desde arriba)."""
    resultado = []
    for nodo in cmds.ls(selection=True, long=True, transforms=True) or []:
        x, z, r = _caja_xz(nodo)
        resultado.append((round(x, 2), round(z, 2), round(r * 0.85, 2)))
    return resultado


def puntos_de_curva(curva, paso=25.0):
    """({"puntos": [(x, z)...], "cerrada": bool}) de una curva NURBS, muestreada cada ``paso`` cm."""
    formas = cmds.listRelatives(curva, shapes=True, fullPath=True, type="nurbsCurve") or []
    if not formas:
        return None
    fn = om.MFnNurbsCurve(_camino(formas[0]))
    largo = fn.length()
    n = int(min(2000, max(8, math.ceil(largo / paso))))
    cerrada = fn.form in (om.MFnNurbsCurve.kClosed, om.MFnNurbsCurve.kPeriodic)
    puntos = []
    for i in range(n + (0 if cerrada else 1)):
        u = fn.findParamFromLength(largo * i / float(n))
        p = fn.getPointAtParam(u, om.MSpace.kWorld)
        puntos.append((round(p.x, 2), round(p.z, 2)))
    if not cerrada and len(puntos) > 2:
        a, b = puntos[0], puntos[-1]
        if math.hypot(a[0] - b[0], a[1] - b[1]) < paso:
            cerrada = True
            puntos = puntos[:-1]
    return {"puntos": puntos, "cerrada": cerrada}


def curvas_de_seleccion():
    resultado = []
    for nodo in cmds.ls(selection=True, long=True, transforms=True) or []:
        datos = puntos_de_curva(nodo)
        if datos:
            datos["nombre"] = nodo.split("|")[-1]
            resultado.append(datos)
    return resultado


# --- informes y horneado -----------------------------------------------------------------

def informe(capa):
    try:
        return json.loads(cmds.getAttr(capa + ".informe") or "{}")
    except ValueError:
        return {}


def informe_escena():
    """Suma de todas las capas, con los prototipos contados una vez."""
    from grasseditor import estadisticas as est
    total = est.Informe()
    for capa in capas():
        datos = informe(capa)
        parcial = est.Informe()
        for campo in ("matas", "triangulos", "descartadas", "posibles", "visor"):
            setattr(parcial, campo, datos.get(campo, 0))
        parcial.por_tipo = datos.get("por_tipo", {})
        parcial.recortadas = datos.get("recortadas", False)
        parcial.opciones = {None: ajustes(capa).opciones}
        total.sumar(parcial, capa)
    total.unicos = triangulos_prototipos()
    return total


def hornear(capa):
    """Congela las matas de la capa: no se recalculan al abrir la escena (un paso de Ctrl+Z)."""
    from grasseditor import capa as modulo
    motor = modulo.Motor()
    forma = forma_suelo(capa)
    matriz = cmds.getAttr(forma + ".worldMatrix[0]") if forma else None
    s = leer_suelo(forma, matriz)
    motor.preparar(s, ajustes(capa), catalogo(), cmds.getAttr(capa + ".mascara") or "")
    texto = motor.horneado()
    cmds.setAttr(capa + ".horneado", texto, type="string")
    return len(motor.aceptadas())


def deshornear(capa):
    cmds.setAttr(capa + ".horneado", "", type="string")


def horneada(capa):
    return bool(cmds.getAttr(capa + ".horneado"))
