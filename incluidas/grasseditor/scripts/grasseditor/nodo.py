"""Nodo «grassEditorCapa»: calcula las matas de una capa y se las da al instanciador.

Entradas (las conecta escena.py):
    suelo, sueloMatriz      la malla del suelo y su matriz de mundo
    tipos                   el catálogo de tipos de la escena (del nodo grasseditor_ajustes)
    ajustes, mascara        los de la capa (JSON y máscara pintada)
    camMatriz, camFocal, camApertura, aspecto, conCamara   la cámara de render
    enRender                True mientras se renderiza (lo pone el comando grassEditorRender)
    modo                    0 automático, 1 siempre visor, 2 siempre render
    horneado                matas congeladas («Hornear»); vacío = se calculan

Salidas:
    salida                  posiciones, giros, escalas e índices para instancer.inputPoints
    informe                 JSON con las cifras del render (matas, triángulos, memoria...)

En modo automático, Maya con interfaz muestra el visor ligero y Maya sin
interfaz (render por lotes, mayapy) da el render completo.

Usa la API clásica de Maya (maya.OpenMaya / OpenMayaMPx): la API 2.0 de
Maya 2026-2027 no tiene MFnArrayAttrsData, que es lo que lee el instanciador.
"""

import json

import maya.OpenMaya as om
import maya.OpenMayaMPx as mpx

from grasseditor import camara as cam
from grasseditor import capa as cp
from grasseditor import reparto, tipos

NOMBRE = "grassEditorCapa"
ID = om.MTypeId(0x0007F2A1)   # rango de Autodesk para desarrollo local


def _texto(datos, atributo):
    return datos.inputValue(atributo).asString()


def _matriz(datos, atributo):
    m = datos.inputValue(atributo).asMatrix()
    return [m(f, c) for f in range(4) for c in range(4)]


def _suelo(objeto_malla, matriz):
    """Suelo de reparto.py a partir del MObject de malla que llega al nodo (o None)."""
    if objeto_malla is None or objeto_malla.isNull():
        return None
    fn = om.MFnMesh(objeto_malla)
    puntos = om.MPointArray()
    fn.getPoints(puntos, om.MSpace.kObject)
    por_cara, vertices = om.MIntArray(), om.MIntArray()
    fn.getTriangles(por_cara, vertices)
    caras = []
    for cara in range(por_cara.length()):
        caras.extend([cara] * por_cara[cara])
    lista = [(puntos[i].x, puntos[i].y, puntos[i].z) for i in range(puntos.length())]
    return reparto.Suelo(lista, [vertices[i] for i in range(vertices.length())], caras, matriz)


def _llenar_vectores(arr, valores):
    arr.setLength(len(valores))
    V = om.MVector
    for i, v in enumerate(valores):
        arr.set(V(v[0], v[1], v[2]), i)


def _llenar_numeros(arr, valores):
    arr.setLength(len(valores))
    for i, v in enumerate(valores):
        arr.set(float(v), i)


def datos_instanciador(salida):
    """MObject con los arrays que lee el instanciador de Maya."""
    fn = om.MFnArrayAttrsData()
    objeto = fn.create()
    posiciones = fn.vectorArray("position")
    giros = fn.vectorArray("rotation")
    escalas = fn.vectorArray("scale")
    indices = fn.doubleArray("objectIndex")
    ids = fn.doubleArray("id")
    if salida is not None and len(salida):
        _llenar_vectores(posiciones, salida.posiciones)
        _llenar_vectores(giros, salida.giros)
        _llenar_vectores(escalas, salida.escalas)
        _llenar_numeros(indices, salida.indices)
        _llenar_numeros(ids, salida.ids)
    return objeto


class NodoCapa(mpx.MPxNode):

    def __init__(self):
        mpx.MPxNode.__init__(self)
        self.motor = cp.Motor()
        self._catalogo_texto = None
        self._catalogo = tipos.Catalogo()

    @staticmethod
    def crear():
        return mpx.asMPxPtr(NodoCapa())

    def _catalogo_de(self, texto):
        if texto != self._catalogo_texto:
            self._catalogo = tipos.Catalogo.desde_json(texto)
            self._catalogo_texto = texto
        return self._catalogo

    def _camara(self, datos):
        if not datos.inputValue(NodoCapa.conCamara).asBool():
            return None
        return cam.Camara(_matriz(datos, NodoCapa.camMatriz), datos.inputValue(NodoCapa.camFocal).asFloat(),
                          datos.inputValue(NodoCapa.camApertura).asFloat(),
                          datos.inputValue(NodoCapa.aspecto).asFloat())

    def _en_render(self, datos):
        if datos.inputValue(NodoCapa.enRender).asBool():
            return True   # renderizando: siempre calidad de render, también en modo «visor»
        modo = datos.inputValue(NodoCapa.modo).asShort()
        if modo == 1:
            return False
        if modo == 2:
            return True
        return om.MGlobal.mayaState() != om.MGlobal.kInteractive

    def compute(self, plug, datos):
        es_salida = plug == NodoCapa.salida
        if not es_salida and not plug == NodoCapa.informe:
            return om.kUnknownParameter
        try:
            malla = datos.inputValue(NodoCapa.suelo).asMesh()
            suelo = _suelo(malla, _matriz(datos, NodoCapa.sueloMatriz))
            ajustes = cp.AjustesCapa.desde_json(_texto(datos, NodoCapa.ajustes))
            catalogo = self._catalogo_de(_texto(datos, NodoCapa.tipos))
            self.motor.preparar(suelo, ajustes, catalogo, _texto(datos, NodoCapa.mascara),
                                _texto(datos, NodoCapa.horneado))
            camara = self._camara(datos)
            if es_salida:
                salida = self.motor.salida(camara, self._en_render(datos))
                datos.outputValue(NodoCapa.salida).setMObject(datos_instanciador(salida))
            else:
                informe = self.motor.informe(camara).a_dict()
                informe["horneada"] = self.motor.horneada
                informe["aceptadas"] = informe.get("posibles", 0)
                datos.outputValue(NodoCapa.informe).setString(json.dumps(informe))
        except Exception as error:  # el nodo nunca debe tumbar Maya
            om.MGlobal.displayWarning("GrassEditor | {}: {}".format(self.name(), error))
            if es_salida:
                datos.outputValue(NodoCapa.salida).setMObject(datos_instanciador(None))
            else:
                datos.outputValue(NodoCapa.informe).setString("{}")
        datos.setClean(plug)
        return None

    @staticmethod
    def inicializar():
        tA, nA, mA, eA = (om.MFnTypedAttribute(), om.MFnNumericAttribute(), om.MFnMatrixAttribute(),
                          om.MFnEnumAttribute())

        def texto(largo, corto, guardar=True):
            a = tA.create(largo, corto, om.MFnData.kString, om.MFnStringData().create(""))
            tA.setStorable(guardar)
            return a

        NodoCapa.suelo = tA.create("suelo", "su", om.MFnData.kMesh)
        tA.setStorable(False)
        NodoCapa.sueloMatriz = mA.create("sueloMatriz", "sm")
        mA.setStorable(False)
        NodoCapa.tipos = texto("tipos", "ti", guardar=False)
        NodoCapa.ajustes = texto("ajustes", "aj")
        NodoCapa.mascara = texto("mascara", "ma")
        NodoCapa.horneado = texto("horneado", "ho")
        NodoCapa.camMatriz = mA.create("camMatriz", "cm")
        mA.setStorable(False)
        NodoCapa.camFocal = nA.create("camFocal", "cf", om.MFnNumericData.kFloat, 35.0)
        NodoCapa.camApertura = nA.create("camApertura", "ca", om.MFnNumericData.kFloat, 1.417)
        NodoCapa.aspecto = nA.create("aspecto", "as", om.MFnNumericData.kFloat, 16.0 / 9.0)
        NodoCapa.conCamara = nA.create("conCamara", "cc", om.MFnNumericData.kBoolean, False)
        NodoCapa.enRender = nA.create("enRender", "er", om.MFnNumericData.kBoolean, False)
        nA.setStorable(False)
        NodoCapa.modo = eA.create("modo", "mo", 0)
        for i, nombre in enumerate(("automatico", "visor", "render")):
            eA.addField(nombre, i)
        NodoCapa.salida = tA.create("salida", "sa", om.MFnData.kDynArrayAttrs)
        tA.setWritable(False)
        tA.setStorable(False)
        NodoCapa.informe = texto("informe", "in", guardar=False)
        tA.setWritable(False)

        entradas = (NodoCapa.suelo, NodoCapa.sueloMatriz, NodoCapa.tipos, NodoCapa.ajustes, NodoCapa.mascara,
                    NodoCapa.horneado, NodoCapa.camMatriz, NodoCapa.camFocal, NodoCapa.camApertura,
                    NodoCapa.aspecto, NodoCapa.conCamara, NodoCapa.enRender, NodoCapa.modo)
        for atributo in entradas + (NodoCapa.salida, NodoCapa.informe):
            NodoCapa.addAttribute(atributo)
        for atributo in entradas:
            NodoCapa.attributeAffects(atributo, NodoCapa.salida)
            NodoCapa.attributeAffects(atributo, NodoCapa.informe)
