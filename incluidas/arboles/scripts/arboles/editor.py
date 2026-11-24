"""Lógica del editor de árboles en Maya (sin interfaz Qt).

El árbol en edición vive en el grupo «arboles_editor» con la malla densa.
Mientras se arrastra un deslizador se reconstruye en calidad media para ir
rápido; al soltar se reconstruye en densa y el cambio entra en el deshacer
de Maya como un solo paso.
"""

import math

import maya.api.OpenMaya as om
from maya import cmds

from arboles import acciones, ejemplos
from arboles import construir_maya as cm
from arboles import modulos as mod
from arboles import vectores as v
from arboles.arbol import Arbol

GRUPO = "arboles_editor"
TIRADORES = "arboles_tiradores"
FIGURA = "arboles_figura_humana"
CONTEXTO_CLIC = "arbolesClicRama"
NIVEL_EDICION = "denso"
NIVEL_ARRASTRE = "medio"


def _sin_deshacer(funcion, *args, **kwargs):
    estado = cmds.undoInfo(query=True, stateWithoutFlush=True)
    cmds.undoInfo(stateWithoutFlush=False)
    try:
        return funcion(*args, **kwargs)
    finally:
        cmds.undoInfo(stateWithoutFlush=estado)


def _refrescar():
    if not cmds.about(batch=True):
        cmds.refresh(currentView=True)


def cambiados(antes, despues):
    """Ids de módulos que cambian entre dos recetas, más todo lo que cuelga de ellos."""
    a = {m["id"]: m for m in antes.get("modulos", [])}
    d = {m["id"]: m for m in despues.get("modulos", [])}
    directos = {i for i in set(a) | set(d) if a.get(i) != d.get(i)}
    hijos = {}
    for m in d.values():
        hijos.setdefault(m["padre"], []).append(m["id"])
    resultado, pila = set(), list(directos)
    while pila:
        i = pila.pop()
        if i not in resultado:
            resultado.add(i)
            pila += hijos.get(i, [])
    return resultado


class Editor(object):
    def __init__(self):
        self.arbol = None
        self.grupo = None
        self.oyentes = []          # funciones sin argumentos: el árbol ha cambiado
        self._antes = None
        self._inicio = {}
        self._tiradores = []       # (localizador, id de módulo, índice de control)
        self._trabajos = []
        self._moviendo_tiradores = False

    # --- arranque ------------------------------------------------------------

    def abrir(self, plantilla="roble"):
        """Recupera el árbol del grupo del editor o crea uno desde ``plantilla``."""
        if cm.es_arbol(GRUPO):
            self.grupo = cmds.ls(GRUPO, long=True)[0]
            self.arbol = cm.arbol_de(self.grupo)
            _sin_deshacer(cm.preparar, self.arbol)
        else:
            self.arbol = ejemplos.crear(plantilla)
            _sin_deshacer(cm.preparar, self.arbol)
            self.grupo = _sin_deshacer(cm.crear, self.arbol, NIVEL_EDICION, GRUPO)
        self._luz_dos_caras()
        self._avisar()
        return self

    @staticmethod
    def _luz_dos_caras():
        """Las hojas son de una cara: sin luz por las dos caras, la mitad sale negra en el visor."""
        if cmds.about(batch=True):
            return
        for panel in cmds.getPanel(type="modelPanel") or []:
            cmds.modelEditor(panel, edit=True, twoSidedLighting=True)

    def _avisar(self):
        for oyente in list(self.oyentes):
            oyente()

    def _aplicar(self, datos, ids=None):
        self.arbol = Arbol.de_dict(datos)
        cm.reconstruir(self.grupo, self.arbol, NIVEL_EDICION, ids)
        self._avisar()
        _refrescar()

    def _accion(self, antes, despues, nombre="Arboles"):
        """Registra el paso antes → después en el deshacer de Maya."""
        if antes == despues:
            return
        ids = cambiados(antes, despues)
        if antes.get("material") != despues.get("material"):
            ids = None  # cambia el material de todas las mallas
            _sin_deshacer(cm.preparar, Arbol.de_dict(despues))
        acciones.ejecutar(lambda: self._aplicar(despues, ids), lambda: self._aplicar(antes, ids), nombre)

    def _cambiar(self, funcion, nombre="Arboles"):
        """Aplica ``funcion(arbol)`` sobre una copia y la registra como un paso."""
        antes = self.arbol.a_dict()
        copia = Arbol.de_dict(antes)
        resultado = funcion(copia)
        self._accion(antes, copia.a_dict(), nombre)
        return resultado

    # --- plantillas y receta ------------------------------------------------------

    def nueva(self, plantilla, frondosidad="normal"):
        nueva = ejemplos.crear(plantilla, frondosidad)
        self._accion(self.arbol.a_dict(), nueva.a_dict(), "Arboles_plantilla")

    def cargar(self, arbol):
        self._accion(self.arbol.a_dict(), arbol.a_dict(), "Arboles_abrir")

    def renombrar(self, nombre):
        self._cambiar(lambda a: setattr(a, "nombre", nombre), "Arboles_nombre")

    def cambiar_material(self, material):
        """Juego de texturas del árbol («clay» o una especie). Un paso de deshacer."""
        self._cambiar(lambda a: setattr(a, "material", material), "Arboles_material")

    # --- deslizadores (vista previa en vivo + un paso de deshacer al soltar) ------

    def empezar_cambio(self, ids):
        self._antes = self.arbol.a_dict()
        self._inicio = {i: dict(self.arbol.modulos[i].valores) for i in ids if i in self.arbol.modulos}

    def cambiar_valor(self, ids, nombre, valor, principal=None):
        """Cambia ``nombre`` en ``ids``. Con varios módulos el cambio es relativo:
        cada uno se mueve lo mismo que el ``principal`` desde su propio valor."""
        if self._antes is None:
            self.empezar_cambio(ids)
        principal = principal or ids[0]
        base = self._inicio.get(principal, {}).get(nombre)
        afectados = []
        for i in ids:
            m = self.arbol.modulos.get(i)
            if m is None or nombre not in mod.PARAMETROS[m.tipo]:
                continue
            if nombre in mod.OPCIONES or base is None or not isinstance(base, (int, float)):
                m.fijar(nombre, valor)
            else:
                m.fijar(nombre, self._inicio[i][nombre] + (valor - base))
            afectados.append(i)
        ids_vista = set(afectados)
        for i in afectados:
            ids_vista.update(self.arbol.descendientes(i))
        cm.reconstruir(self.grupo, self.arbol, NIVEL_ARRASTRE, ids_vista, guardar_receta=False)
        self._colocar_tiradores()
        _refrescar()

    def terminar_cambio(self):
        if self._antes is None:
            return
        antes, self._antes, self._inicio = self._antes, None, {}
        despues = self.arbol.a_dict()
        if antes == despues:
            return
        self._accion(antes, despues, "Arboles_ajuste")

    def fijar_valor(self, ids, nombre, valor):
        """Cambio de una vez (casilla numérica o lista): un paso de deshacer."""
        self.empezar_cambio(ids)
        self.cambiar_valor(ids, nombre, valor)
        self.terminar_cambio()

    # --- ramas -----------------------------------------------------------------

    def anadir_rama(self, padre, **valores):
        padre_mod = self.arbol.modulos[padre]
        if "longitud" not in valores:
            largo = padre_mod.valores.get("longitud", padre_mod.valores.get("altura", 200.0))
            valores["longitud"] = max(20.0, largo * 0.5)
        if "giro" not in valores:
            valores["giro"] = (len(self.arbol.hijos(padre)) * 137.5) % 360.0
        return self._cambiar(lambda a: a.anadir_rama(padre, **valores).id, "Arboles_rama")

    def quitar(self, ids):
        ids = [i for i in ids if self.arbol.modulos.get(i) and self.arbol.modulos[i].tipo == mod.RAMA]

        def quitar(a):
            for i in ids:
                a.quitar(i)
        if ids:
            self._cambiar(quitar, "Arboles_quitar")
        return ids

    def repetir(self, id_, copias):
        return self._cambiar(lambda a: [m.id for m in a.repetir_alrededor(id_, copias)], "Arboles_repetir")

    def pegar(self, valores, ids):
        return self._cambiar(lambda a: a.pegar_ajustes(valores, ids), "Arboles_pegar")

    def injertar(self, subarbol, padre):
        return self._cambiar(lambda a: a.injertar(subarbol, padre).id, "Arboles_favorita")

    # --- tiradores de la curva guía ---------------------------------------------

    def mostrar_tiradores(self, id_):
        """Localizadores en los puntos de control de la curva de ``id_`` (o ninguno)."""
        _sin_deshacer(self._crear_tiradores, id_)

    def _crear_tiradores(self, id_):
        self.quitar_tiradores()
        if id_ is None or id_ not in self.arbol.modulos:
            return
        if not cmds.objExists(TIRADORES):
            cmds.group(empty=True, name=TIRADORES)
        self.arbol.calcular()
        guia = self.arbol.modulos[id_].guia
        tamano = max(8.0, guia.radio_base * 1.5)
        for i, s in enumerate(mod.CONTROLES):
            loc = cmds.spaceLocator(name="arboles_tirador{}".format(i + 1))[0]
            cmds.setAttr(loc + ".localScale", tamano, tamano, tamano, type="double3")
            cmds.setAttr(loc + ".overrideEnabled", 1)
            cmds.setAttr(loc + ".overrideColor", 17)  # amarillo
            loc = cmds.parent(loc, TIRADORES)[0]
            cmds.xform(loc, worldSpace=True, translation=guia.punto(s))
            self._tiradores.append((cmds.ls(loc, long=True)[0], id_, i))
            trabajo = cmds.scriptJob(attributeChange=[loc + ".translate", self._tirador_movido])
            if trabajo is not None:  # en modo batch (mayapy) no hay scriptJobs
                self._trabajos.append(trabajo)

    def quitar_tiradores(self):
        for trabajo in self._trabajos:
            if trabajo is not None and cmds.scriptJob(exists=trabajo):
                cmds.scriptJob(kill=trabajo, force=True)
        self._trabajos, self._tiradores = [], []
        if cmds.objExists(TIRADORES):
            _sin_deshacer(cmds.delete, TIRADORES)

    def _colocar_tiradores(self):
        if not self._tiradores:
            return
        self.arbol.calcular()
        self._moviendo_tiradores = True
        try:
            for loc, id_, i in self._tiradores:
                if cmds.objExists(loc) and id_ in self.arbol.modulos:
                    _sin_deshacer(cmds.xform, loc, worldSpace=True,
                                  translation=self.arbol.modulos[id_].guia.punto(mod.CONTROLES[i]))
        finally:
            self._moviendo_tiradores = False

    def _tirador_movido(self):
        if self._moviendo_tiradores:
            return
        self.arbol.calcular()
        afectados = set()
        for loc, id_, i in self._tiradores:
            if not cmds.objExists(loc) or id_ not in self.arbol.modulos:
                continue
            m = self.arbol.modulos[id_]
            posicion = cmds.xform(loc, query=True, worldSpace=True, translation=True)
            m.fijar_control(i, v.resta(posicion, m.guia.punto_base(mod.CONTROLES[i])))
            afectados.add(id_)
        for id_ in list(afectados):
            afectados.update(self.arbol.descendientes(id_))
        cm.reconstruir(self.grupo, self.arbol, NIVEL_EDICION, afectados)
        self._avisar()

    def enderezar(self, ids):
        """Quita los retoques a mano de la curva."""
        def enderezar(a):
            for i in ids:
                a.modulos[i].curva = {}
        self._cambiar(enderezar, "Arboles_enderezar")
        self._colocar_tiradores()

    # --- clic en el visor para añadir ramas -------------------------------------------

    def modulo_bajo_rayo(self, origen, direccion):
        """(id, punto) del primer tronco o rama que corta el rayo, o (None, None)."""
        mejor = (None, None, float("inf"))
        rayo_o = om.MFloatPoint(*origen)
        rayo_d = om.MFloatVector(*direccion)
        for nombre in cm.mallas(self.grupo):
            camino = cm._camino(nombre)
            camino.extendToShape()
            corte = om.MFnMesh(camino).closestIntersection(
                rayo_o, rayo_d, om.MSpace.kWorld, 1e7, False)
            if corte and corte[2] >= 0 and 0 < corte[1] < mejor[2]:
                punto = (corte[0].x, corte[0].y, corte[0].z)
                mejor = (cm.leer_texto(nombre, cm.ATRIBUTO_MODULO), punto, corte[1])
        return mejor[0], mejor[1]

    def rama_en_punto(self, id_, punto):
        """Valores de posición y giro para una rama que nazca en ``punto`` de ``id_``."""
        grupo = cmds.xform(self.grupo, query=True, worldSpace=True, translation=True)
        punto = v.resta(punto, grupo)
        self.arbol.calcular()
        guia = self.arbol.modulos[id_].guia
        s = guia.mas_cercano(punto)
        _, n, b = guia.marco(s)
        radial = v.resta(punto, guia.punto(s))
        giro = math.degrees(math.atan2(v.punto(radial, b), v.punto(radial, n))) % 360.0
        return {"posicion": s, "giro": giro}

    def herramienta_clic(self, al_anadir=None):
        """Activa la herramienta: cada clic sobre el árbol añade una rama ahí."""
        def pulsar():
            x, y, _ = cmds.draggerContext(CONTEXTO_CLIC, query=True, anchorPoint=True)
            id_, punto = self.modulo_bajo_rayo(*cm.rayo_del_visor(x, y))
            if id_ is None:
                return
            nuevo = self.anadir_rama(id_, **self.rama_en_punto(id_, punto))
            if al_anadir:
                al_anadir(nuevo)

        if cmds.draggerContext(CONTEXTO_CLIC, exists=True):
            cmds.deleteUI(CONTEXTO_CLIC)
        cmds.draggerContext(CONTEXTO_CLIC, pressCommand=pulsar, space="screen", cursor="crossHair",
                            name=CONTEXTO_CLIC, undoMode="step")
        cmds.setToolTo(CONTEXTO_CLIC)

    # --- selección --------------------------------------------------------------------

    def seleccionar(self, ids):
        """Selecciona en el visor las mallas de ``ids`` (sin entrar en el deshacer)."""
        sel = om.MSelectionList()
        for nombre in cm.mallas(self.grupo):
            if cm.leer_texto(nombre, cm.ATRIBUTO_MODULO) in ids:
                sel.add(nombre)
        om.MGlobal.setActiveSelectionList(sel)

    def ids_seleccionados_en_visor(self):
        ids = []
        for nodo in cmds.ls(selection=True, long=True) or []:
            grupo, id_ = cm.modulo_de_nodo(nodo)
            if grupo and cmds.ls(grupo, long=True) == cmds.ls(self.grupo, long=True) and id_ and id_ not in ids:
                ids.append(id_)
        return ids

    # --- ayudas -----------------------------------------------------------------------

    def figura_humana(self, visible):
        """Silueta de 1,75 m junto al árbol para no perder la escala."""
        def crear():
            cuerpo = cmds.polyCylinder(radius=17, height=140, subdivisionsAxis=12, name="figura_cuerpo")[0]
            cmds.move(0, 70, 0, cuerpo)
            cabeza = cmds.polySphere(radius=12, subdivisionsAxis=12, subdivisionsHeight=8)[0]
            cmds.move(0, 162, 0, cabeza)
            figura = cmds.polyUnite(cuerpo, cabeza, constructionHistory=False, name=FIGURA)[0]
            forma = cmds.listRelatives(figura, shapes=True)[0]
            cmds.setAttr(forma + ".overrideEnabled", 1)
            cmds.setAttr(forma + ".overrideDisplayType", 2)  # referencia: no se selecciona
            cmds.setAttr(forma + ".castsShadows", 0)
            cmds.setAttr(forma + ".primaryVisibility", 0)  # no sale en el render
        if visible and not cmds.objExists(FIGURA):
            _sin_deshacer(crear)
        if cmds.objExists(FIGURA):
            self.arbol.calcular()
            radio = max(abs(c) for m in self.arbol.modulos.values() for p in m.guia.puntos for c in (p[0], p[2]))
            base = cmds.xform(self.grupo, query=True, worldSpace=True, translation=True)
            _sin_deshacer(cmds.xform, FIGURA, worldSpace=True,
                          translation=(base[0] + radio + 60, base[1], base[2]))
            _sin_deshacer(cmds.setAttr, FIGURA + ".visibility", bool(visible))

    def generar(self, nivel):
        """Crea al lado una copia terminada del árbol en la calidad ``nivel`` (un paso de deshacer)."""
        _sin_deshacer(cm.preparar, self.arbol)
        copia = self.arbol.copiar()
        copia.calcular()
        radio = max(abs(p[0]) for m in copia.modulos.values() for p in m.guia.puntos) + 100
        base = cmds.xform(self.grupo, query=True, worldSpace=True, translation=True)
        hechos = []
        nombre = "{}_{}".format(copia.nombre, nivel)

        def hacer():
            hechos.append(cm.crear(copia, nivel, nombre, (base[0] + 2 * radio, base[1], base[2])))

        def deshacer():
            if hechos and cm.existe(hechos[-1]):
                cm.borrar(hechos.pop())
        acciones.ejecutar(hacer, deshacer, "Arboles_generar")
        return hechos[-1] if hechos else None

    def miniatura(self, ruta, tamano=256):
        """Captura del árbol en edición desde una cámara a tres cuartos (solo con interfaz)."""
        return miniatura_de(self.grupo, ruta, tamano)

    def cerrar(self):
        self.quitar_tiradores()
        if not cmds.about(batch=True) and cmds.draggerContext(CONTEXTO_CLIC, exists=True):
            cmds.setToolTo("selectSuperContext")


def miniatura_de(grupo, ruta, tamano=256):
    """Captura del árbol ``grupo`` desde una cámara a tres cuartos (solo con interfaz)."""
    if cmds.about(batch=True):
        return None
    caja = cmds.exactWorldBoundingBox(grupo)
    centro = [(caja[i] + caja[i + 3]) / 2.0 for i in range(3)]
    alto = max(caja[4] - caja[1], caja[3] - caja[0], 1.0)
    ventana = cmds.window(widthHeight=(tamano + 20, tamano + 20), visible=False)
    cmds.paneLayout()
    panel = cmds.modelPanel(menuBarVisible=False)
    camara = cmds.camera(name="arboles_cam_miniatura")[0]
    try:
        cmds.viewPlace(camara, eye=(centro[0] + alto * 1.1, centro[1] + alto * 0.15, centro[2] + alto * 1.1),
                       lookAt=centro, perspective=True)
        editor = cmds.modelPanel(panel, query=True, modelEditor=True)
        cmds.modelEditor(editor, edit=True, camera=camara, displayAppearance="smoothShaded", twoSidedLighting=True,
                         grid=False, headsUpDisplay=False, allObjects=False, polymeshes=True,
                         selectionHiliteDisplay=False)
        cmds.isolateSelect(panel, state=True)
        cmds.select(grupo)
        cmds.isolateSelect(panel, addSelected=True)
        cmds.select(clear=True)  # si no, la miniatura sale con el color de selección
        cmds.showWindow(ventana)
        cmds.viewFit(camara, grupo, fitFactor=0.9)
        cmds.setFocus(panel)
        cmds.playblast(frame=cmds.currentTime(query=True), format="image", compression="png",
                       completeFilename=ruta, widthHeight=(tamano, tamano), percent=100,
                       viewer=False, showOrnaments=False, offScreen=True, forceOverwrite=True)
    finally:
        cmds.select(clear=True)
        cmds.deleteUI(ventana)
        cmds.delete(camara)
    return ruta
