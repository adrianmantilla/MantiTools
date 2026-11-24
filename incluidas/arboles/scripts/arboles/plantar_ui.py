"""Panel de plantar: la biblioteca con miniaturas y la herramienta de clic sobre el suelo."""

import os

from maya import cmds

try:
    from PySide6 import QtCore, QtGui, QtWidgets
except ImportError:  # Maya anterior a 2025
    from PySide2 import QtCore, QtGui, QtWidgets

from arboles import construir_maya as cm
from arboles import estilo, interfaz_maya, plantar
from arboles import modulos as mod
from arboles.arbol import SEMAFORO
from arboles.biblioteca import Biblioteca
from arboles.i18n import t

_panel = None
_TAMANO = 112
_COLORES = {"verde": "#3fa34d", "amarillo": "#e0b000", "rojo": "#d64541"}
_ARBOLES_JARDIN = 50  # el semáforo de cada árbol está pensado para 50 copias


def _miles(n):
    return "{:,}".format(int(n)).replace(",", ".")


def semaforo_jardin(triangulos):
    for limite, color in SEMAFORO:
        if triangulos <= limite * _ARBOLES_JARDIN:
            return color
    return "rojo"


def _icono(ruta):
    """Icono leído del disco cada vez: QIcon(ruta) guarda en caché la miniatura vieja."""
    if not os.path.isfile(ruta):
        return None
    imagen = QtGui.QPixmap()
    with open(ruta, "rb") as f:
        if not imagen.loadFromData(f.read()):
            return None
    return QtGui.QIcon(imagen)


def refrescar_si_abierto():
    """Tras guardar en el editor: el panel muestra la miniatura nueva sin pulsar Refrescar."""
    if _panel is not None:
        _panel.refrescar()


class PanelPlantar(QtWidgets.QDialog):
    def __init__(self, padre=None):
        if padre is None:
            from arboles.editor_ui import _ventana_maya
            padre = _ventana_maya()
        super(PanelPlantar, self).__init__(padre)
        self.setWindowTitle(t("plantar_titulo"))
        estilo.aplicar(self, "ArbolesPlantar")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self.resize(520, 560)
        self._construir()
        self.refrescar()

    def _boton(self, clave, funcion):
        b = QtWidgets.QPushButton(t(clave))
        b.setToolTip(t("ayuda_" + clave))
        b.clicked.connect(funcion)
        return b

    def _construir(self):
        capa = QtWidgets.QVBoxLayout(self)
        self.lista = QtWidgets.QListWidget()
        self.lista.setViewMode(QtWidgets.QListView.IconMode)
        self.lista.setIconSize(QtCore.QSize(_TAMANO, _TAMANO))
        self.lista.setGridSize(QtCore.QSize(_TAMANO + 24, _TAMANO + 36))
        self.lista.setResizeMode(QtWidgets.QListView.Adjust)
        self.lista.setMovement(QtWidgets.QListView.Static)
        self.lista.setToolTip(t("ayuda_lista_plantar"))
        self.lista.itemDoubleClicked.connect(lambda _: self._plantar())
        capa.addWidget(self.lista, 1)

        opciones = QtWidgets.QHBoxLayout()
        opciones.addWidget(QtWidgets.QLabel(t("calidad")))
        self.nivel = QtWidgets.QComboBox()
        for nivel in mod.NIVELES_GENERAR:
            self.nivel.addItem(t("nivel_" + nivel), nivel)
        self.nivel.setCurrentIndex(mod.NIVELES_GENERAR.index(plantar.NIVEL_POR_DEFECTO))
        self.nivel.setToolTip(t("ayuda_calidad"))
        opciones.addWidget(self.nivel)
        self.girar = QtWidgets.QCheckBox(t("casilla_girar"))
        self.girar.setChecked(True)
        self.girar.setToolTip(t("ayuda_casilla_girar"))
        opciones.addWidget(self.girar)
        opciones.addStretch(1)
        capa.addLayout(opciones)

        # Variaciones por copia: formas distintas del mismo árbol, tamaño e inclinación al azar
        variacion = QtWidgets.QHBoxLayout()
        self.variantes = self._numero(variacion, "variantes", 1, plantar.var.MAXIMO, 1, 1, "")
        self.tamano = self._numero(variacion, "variacion_tamano", 0, 40, 5, 0, " %")
        self.inclinacion = self._numero(variacion, "variacion_inclinacion", 0, 15, 1, 0, "°")
        variacion.addStretch(1)
        capa.addLayout(variacion)

        botones = QtWidgets.QHBoxLayout()
        for clave, funcion in (("boton_plantar_clic", self._plantar), ("boton_desligar", self._desligar),
                               ("boton_editar_maestro", self._editar), ("boton_ejemplos", self._ejemplos),
                               ("boton_refrescar", self.refrescar)):
            boton = self._boton(clave, funcion)
            if clave == "boton_plantar_clic":
                estilo.primario(boton)
            botones.addWidget(boton)
        capa.addLayout(botones)
        self.jardin = QtWidgets.QLabel()
        self.jardin.setToolTip(t("ayuda_jardin"))
        capa.addWidget(self.jardin)
        self.estado = estilo.etiqueta("", "tenue")
        capa.addWidget(self.estado)

    def _numero(self, capa, clave, minimo, maximo, paso, valor, sufijo):
        capa.addWidget(QtWidgets.QLabel(t("etiqueta_" + clave)))
        caja = QtWidgets.QSpinBox()
        caja.setRange(minimo, maximo)
        caja.setSingleStep(paso)
        caja.setValue(valor)
        caja.setSuffix(sufijo)
        caja.setToolTip(t("ayuda_" + clave))
        capa.addWidget(caja)
        return caja

    def _variacion(self):
        return self.variantes.value(), self.tamano.value() / 100.0, float(self.inclinacion.value())

    def _biblioteca(self):
        return Biblioteca(interfaz_maya.carpeta_biblioteca())

    def _mensaje(self, texto):
        self.estado.setText(texto)
        print("Árboles | " + texto)

    def refrescar(self):
        bib = self._biblioteca()
        actual = self.lista.currentItem().data(QtCore.Qt.UserRole) if self.lista.currentItem() else None
        self.lista.clear()
        for nombre in bib.arboles():
            ruta = bib.ruta_miniatura(nombre)
            icono = _icono(ruta) or self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon)
            e = QtWidgets.QListWidgetItem(icono, nombre.replace("_", " "))
            e.setData(QtCore.Qt.UserRole, nombre)
            self.lista.addItem(e)
            if nombre == actual:
                self.lista.setCurrentItem(e)
        if self.lista.count() and not self.lista.currentItem():
            self.lista.setCurrentRow(0)
        if not self.lista.count():
            self._mensaje(t("biblioteca_vacia"))
        self._informe()

    def _informe(self):
        copias, triangulos = plantar.informe()
        color = semaforo_jardin(triangulos)
        self.jardin.setText('<span style="color:{}; font-size:16px;">&#9679;</span> {}'.format(
            _COLORES[color], t("jardin", n=copias, triangulos=_miles(triangulos))))

    def _ejemplos(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            nuevos = plantar.anadir_ejemplos(self._biblioteca(), lambda p: t("plantilla_" + p))
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        self.refrescar()
        self._mensaje(t("ejemplos_anadidos", n=len(nuevos)))

    def _arbol_elegido(self):
        e = self.lista.currentItem()
        if e is None:
            self._mensaje(t("elige_arbol"))
            return None
        return self._biblioteca().cargar(e.data(QtCore.Qt.UserRole))

    def _plantar(self):
        if self.lista.currentItem() is None:
            self._mensaje(t("elige_arbol"))
            return
        cache = {}

        def arbol():
            nombre = self.lista.currentItem().data(QtCore.Qt.UserRole) if self.lista.currentItem() else None
            if nombre is None:
                return None
            if nombre not in cache:
                cache[nombre] = self._biblioteca().cargar(nombre)
            return cache[nombre]

        plantar.herramienta(arbol, nivel=lambda: self.nivel.currentData(), girar=self.girar.isChecked,
                            al_plantar=lambda _: self._informe(), variacion=self._variacion)
        self._mensaje(t("plantar_ayuda"))

    def _desligar(self):
        copias = plantar.plantados_seleccionados()
        if not copias:
            self._mensaje(t("elige_plantado"))
            return
        nuevos = plantar.desligar(copias)
        cmds.select(nuevos)
        self._mensaje(t("desligados", n=len(nuevos)))
        self._informe()

    def _editar(self):
        """Abre en el editor el árbol elegido (o el de la copia seleccionada)."""
        from arboles import editor_ui
        copias = plantar.plantados_seleccionados()
        if copias:
            arbol = cm.arbol_de(cmds.getAttr(copias[0] + "." + plantar.ATRIBUTO_PLANTADO))
        else:
            arbol = self._arbol_elegido()
        if arbol is None:
            return
        ventana = editor_ui.mostrar()
        ventana.editor.cargar(arbol)
        ventana._seleccionar_ids([ventana.editor.arbol.tronco.id])
        self._mensaje(t("editar_maestro_ayuda"))

    def closeEvent(self, evento):
        plantar.soltar_herramienta()
        global _panel
        _panel = None
        super(PanelPlantar, self).closeEvent(evento)


def mostrar():
    global _panel
    if _panel is None:
        _panel = PanelPlantar()
    _panel.refrescar()
    _panel.show()
    _panel.raise_()
    return _panel
