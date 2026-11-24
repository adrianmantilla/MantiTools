"""Ventana del editor de árboles (Qt).

Izquierda: la lista de tronco y ramas (se pueden seleccionar varias) y las
herramientas. Derecha: los deslizadores del módulo seleccionado, en tres
bloques (Forma, Follaje y Avanzado, este plegado). Abajo: el semáforo de
polígonos, Generar y la biblioteca.
"""

from maya import cmds
import maya.OpenMayaUI as omui1

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from shiboken6 import wrapInstance
except ImportError:  # Maya anterior a 2025
    from PySide2 import QtCore, QtGui, QtWidgets
    from shiboken2 import wrapInstance

from arboles import construir_maya as cm
from arboles import ejemplos, estilo, follaje, i18n, interfaz_maya
from arboles import modulos as mod
from arboles.biblioteca import Biblioteca
from arboles.editor import Editor
from arboles.i18n import t

_ventana = None
_PASOS = 1000
_COLORES = {"verde": "#3fa34d", "amarillo": "#e0b000", "rojo": "#d64541"}


def _texto(*claves):
    """Primer texto que exista entre ``claves`` (para etiquetas por tipo de módulo)."""
    disponibles = i18n.claves()
    for clave in claves:
        if clave in disponibles:
            return t(clave)
    return claves[-1]


def _miles(n):
    return "{:,}".format(int(n)).replace(",", ".")


def _ventana_maya():
    return wrapInstance(int(omui1.MQtUtil.mainWindow()), QtWidgets.QWidget)


def nombre_modulo(id_):
    numero = "".join(c for c in id_ if c.isdigit())
    return t("lista_tronco") if id_.startswith(mod.TRONCO) else t("lista_rama", n=numero)



def opciones_material():
    """«clay», las especies de serie y cualquier otro juego de texturas instalado."""
    from arboles import especies, texturas
    return [texturas.CLAY] + list(especies.ESPECIES) + [j for j in texturas.juegos() if j not in especies.ESPECIES]


def texto_material(clave):
    from arboles import texturas
    if clave == texturas.CLAY:
        return t("material_clay")
    from arboles import materiales_propios
    if materiales_propios.es_propio(clave):
        return t("material_propio_nombre", nombre=materiales_propios.nombre_visible(clave))
    nombre = t("plantilla_" + clave)
    nombre = clave if nombre == "plantilla_" + clave else nombre
    return nombre if texturas.existe(clave) else t("material_sin_texturas", nombre=nombre)

def _ayuda_con_miniatura(ayuda, tipo, nombre):
    """La frase de ayuda y, si la hay, la miniatura de qué hace el deslizador (de menos a más)."""
    import html
    import os
    from arboles import texturas
    ruta = os.path.join(os.path.dirname(texturas.carpeta_texturas()), "iconos", "ayuda",
                        "{}_{}.png".format(tipo, nombre))
    if not os.path.isfile(ruta):
        return ayuda
    return "<p style='white-space:pre-wrap; width:320px'>{}</p><p><img src='{}'></p>".format(
        html.escape(ayuda), QtCore.QUrl.fromLocalFile(ruta).toString())


class FilaParametro(QtWidgets.QWidget):
    """Etiqueta + deslizador + casilla numérica (o lista para opciones)."""

    def __init__(self, ventana, tipo, nombre, padre=None):
        super(FilaParametro, self).__init__(padre)
        self.ventana, self.tipo, self.nombre = ventana, tipo, nombre
        defecto, self.minimo, self.maximo, _ = mod.PARAMETROS[tipo][nombre]
        self.entero = isinstance(defecto, int)
        capa = QtWidgets.QHBoxLayout(self)
        capa.setContentsMargins(0, 0, 0, 0)
        etiqueta = QtWidgets.QLabel(_texto("p_{}_{}".format(tipo, nombre), "p_" + nombre))
        etiqueta.setMinimumWidth(110)
        ayuda = _texto("ayuda_{}_{}".format(tipo, nombre), "ayuda_" + nombre)
        self.setToolTip(_ayuda_con_miniatura(ayuda, tipo, nombre))
        capa.addWidget(etiqueta)
        self._quieto = False
        if nombre in mod.OPCIONES:
            self.lista = QtWidgets.QComboBox()
            for opcion in mod.OPCIONES[nombre]:
                self.lista.addItem(_texto("opcion_" + opcion, opcion), opcion)
            if nombre == "follaje":  # las hojas propias del alumno, después de las de serie
                for hoja in sorted(follaje.HOJAS_PROPIAS):
                    self.lista.addItem(t("opcion_propia", nombre=hoja.replace("_", " ")), follaje.PROPIA + hoja)
            self.lista.currentIndexChanged.connect(self._lista_cambiada)
            capa.addWidget(self.lista, 1)
            self.deslizador = self.casilla = None
            return
        self.lista = None
        self.deslizador = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.deslizador.setRange(0, _PASOS)
        self.casilla = QtWidgets.QSpinBox() if self.entero else QtWidgets.QDoubleSpinBox()
        self.casilla.setRange(self.minimo, self.maximo)
        if not self.entero:
            self.casilla.setDecimals(2 if self.maximo <= 10 else 1)
            self.casilla.setSingleStep((self.maximo - self.minimo) / 100.0)
        self.casilla.setKeyboardTracking(False)
        self.casilla.setMinimumWidth(70)
        capa.addWidget(self.deslizador, 1)
        capa.addWidget(self.casilla)
        self.deslizador.sliderPressed.connect(lambda: self.ventana.empezar(self.nombre))
        self.deslizador.valueChanged.connect(self._deslizador_movido)
        self.deslizador.sliderReleased.connect(self.ventana.terminar)
        self.casilla.valueChanged.connect(self._casilla_cambiada)

    def _a_pasos(self, valor):
        return int(round((valor - self.minimo) / float(self.maximo - self.minimo) * _PASOS))

    def _de_pasos(self, pasos):
        valor = self.minimo + (self.maximo - self.minimo) * pasos / float(_PASOS)
        return int(round(valor)) if self.entero else valor

    def poner(self, valor):
        self._quieto = True
        try:
            if self.lista is not None:
                self.lista.setCurrentIndex(max(0, self.lista.findData(valor)))
            else:
                self.deslizador.setValue(self._a_pasos(valor))
                self.casilla.setValue(valor)
        finally:
            self._quieto = False

    def _deslizador_movido(self, pasos):
        if self._quieto:
            return
        valor = self._de_pasos(pasos)
        self._quieto = True
        self.casilla.setValue(valor)
        self._quieto = False
        if self.deslizador.isSliderDown():
            self.ventana.cambiar(self.nombre, valor)
        else:  # clic en la barra o teclado
            self.ventana.fijar(self.nombre, valor)

    def _casilla_cambiada(self, valor):
        if self._quieto:
            return
        self._quieto = True
        self.deslizador.setValue(self._a_pasos(valor))
        self._quieto = False
        self.ventana.fijar(self.nombre, valor)

    def _lista_cambiada(self, _indice):
        if not self._quieto:
            self.ventana.fijar(self.nombre, self.lista.currentData())


class Seccion(QtWidgets.QWidget):
    """Bloque con título que se puede plegar."""

    def __init__(self, titulo, plegada=False, padre=None):
        super(Seccion, self).__init__(padre)
        capa = QtWidgets.QVBoxLayout(self)
        capa.setContentsMargins(0, 4, 0, 4)
        self.boton = QtWidgets.QToolButton()
        self.boton.setText(titulo)
        self.boton.setCheckable(True)
        self.boton.setChecked(not plegada)
        self.boton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.boton.setStyleSheet("QToolButton { border: none; font-weight: bold; }")
        self.cuerpo = QtWidgets.QWidget()
        self.filas = QtWidgets.QVBoxLayout(self.cuerpo)
        self.filas.setContentsMargins(8, 0, 0, 0)
        capa.addWidget(self.boton)
        capa.addWidget(self.cuerpo)
        self.boton.toggled.connect(self._plegar)
        self._plegar(not plegada)

    def _plegar(self, abierta):
        self.boton.setArrowType(QtCore.Qt.DownArrow if abierta else QtCore.Qt.RightArrow)
        self.cuerpo.setVisible(abierta)


class VentanaEditor(QtWidgets.QDialog):
    def __init__(self, padre=None):
        super(VentanaEditor, self).__init__(padre or _ventana_maya())
        self.setWindowTitle(t("editor_titulo"))
        estilo.aplicar(self, "ArbolesEditor")  # la línea de Materials, compartida con MantiTools
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self.resize(720, 640)
        try:
            self._biblioteca().cargar_hojas()  # hojas propias del alumno, para la lista de hojas
        except OSError:
            pass
        self.editor = Editor().abrir()
        self.editor.oyentes.append(self.refrescar)
        self._ids = []
        self._filas = {}
        self._portapapeles = None
        self._sincronizando = False
        self._avanzado_abierto = False
        self._construir()
        self._trabajo = cmds.scriptJob(event=["SelectionChanged", self._seleccion_en_visor])
        atajo = getattr(QtGui, "QShortcut", None) or QtWidgets.QShortcut  # PySide6 / PySide2
        atajo(QtGui.QKeySequence.Undo, self, activated=lambda: cmds.undo())
        atajo(QtGui.QKeySequence.Redo, self, activated=lambda: cmds.redo())
        self.refrescar()
        self._seleccionar_ids([self.editor.arbol.tronco.id])

    # --- construcción de la ventana ---------------------------------------------------

    def _boton(self, clave, funcion, ayuda=None):
        b = QtWidgets.QPushButton(t(clave))
        b.clicked.connect(funcion)
        b.setToolTip(t(ayuda or "ayuda_" + clave))
        return b

    def _construir(self):
        capa = QtWidgets.QVBoxLayout(self)

        # Barra de arriba: plantilla, nombre y biblioteca
        arriba = QtWidgets.QHBoxLayout()
        self.plantillas = QtWidgets.QComboBox()
        for clave in ejemplos.PLANTILLAS:
            self.plantillas.addItem(t("plantilla_" + clave), clave)
        self.plantillas.setToolTip(t("ayuda_plantilla"))
        arriba.addWidget(QtWidgets.QLabel(t("empezar_desde")))
        arriba.addWidget(self.plantillas)
        self.frondosidad = QtWidgets.QComboBox()
        for clave in ejemplos.FRONDOSIDADES:
            self.frondosidad.addItem(t("frondosidad_" + clave), clave)
        self.frondosidad.setCurrentIndex(ejemplos.FRONDOSIDADES.index("normal"))
        self.frondosidad.setToolTip(t("ayuda_frondosidad"))
        arriba.addWidget(self.frondosidad)
        arriba.addWidget(self._boton("boton_empezar", self._empezar_plantilla))
        arriba.addSpacing(16)
        arriba.addWidget(QtWidgets.QLabel(t("nombre")))
        self.nombre = QtWidgets.QLineEdit()
        self.nombre.editingFinished.connect(self._renombrar)
        arriba.addWidget(self.nombre, 1)
        arriba.addWidget(QtWidgets.QLabel(t("material")))
        self.material = QtWidgets.QComboBox()
        self.material.setToolTip(t("ayuda_material"))
        for clave in opciones_material():
            self.material.addItem(texto_material(clave), clave)
        self.material.activated.connect(self._cambiar_material)
        arriba.addWidget(self.material)
        arriba.addWidget(self._boton("boton_material_propio", self._material_propio))
        arriba.addWidget(self._boton("boton_abrir", self._abrir))
        arriba.addWidget(self._boton("boton_guardar", self._guardar))
        capa.addLayout(arriba)

        division = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        # Izquierda: lista y herramientas
        izquierda = QtWidgets.QWidget()
        ci = QtWidgets.QVBoxLayout(izquierda)
        ci.setContentsMargins(0, 0, 0, 0)
        self.lista = QtWidgets.QTreeWidget()
        self.lista.setHeaderHidden(True)
        self.lista.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.lista.setToolTip(t("ayuda_lista"))
        self.lista.itemSelectionChanged.connect(self._seleccion_en_lista)
        ci.addWidget(self.lista, 1)
        rejilla = QtWidgets.QGridLayout()
        botones = [
            self._boton("boton_anadir", self._anadir),
            self._boton("boton_clic", self._clic_visor),
            self._boton("boton_repetir", self._repetir),
            self._boton("boton_quitar", self._quitar),
            self._boton("boton_copiar", self._copiar),
            self._boton("boton_pegar", self._pegar),
        ]
        self.favoritas = QtWidgets.QPushButton(t("boton_favoritas"))
        self.favoritas.setToolTip(t("ayuda_boton_favoritas"))
        self.menu_favoritas = QtWidgets.QMenu(self)
        self.menu_favoritas.aboutToShow.connect(self._llenar_favoritas)
        self.favoritas.setMenu(self.menu_favoritas)
        botones.append(self.favoritas)
        botones.append(self._boton("boton_enderezar", self._enderezar))
        botones.append(self._boton("boton_plantar", self._plantar))
        for i, b in enumerate(botones):
            rejilla.addWidget(b, i // 2, i % 2)
        ci.addLayout(rejilla)
        division.addWidget(izquierda)

        # Derecha: parámetros
        self.parametros = QtWidgets.QWidget()
        self.capa_parametros = QtWidgets.QVBoxLayout(self.parametros)
        self.capa_parametros.setAlignment(QtCore.Qt.AlignTop)
        desplazable = QtWidgets.QScrollArea()
        desplazable.setWidgetResizable(True)
        desplazable.setWidget(self.parametros)
        division.addWidget(desplazable)
        division.setSizes([240, 480])
        capa.addWidget(division, 1)

        # Abajo: ayudas visuales, semáforo y Generar
        ayudas = QtWidgets.QHBoxLayout()
        self.tiradores = QtWidgets.QCheckBox(t("casilla_tiradores"))
        self.tiradores.setToolTip(t("ayuda_casilla_tiradores"))
        self.tiradores.toggled.connect(lambda _: self._actualizar_tiradores())
        self.figura = QtWidgets.QCheckBox(t("casilla_figura"))
        self.figura.setToolTip(t("ayuda_casilla_figura"))
        self.figura.toggled.connect(self.editor.figura_humana)
        self.cuadros = QtWidgets.QCheckBox(t("casilla_cuadros"))
        self.cuadros.setToolTip(t("ayuda_casilla_cuadros"))
        self.cuadros.toggled.connect(cm.textura_cuadros)
        for c in (self.tiradores, self.figura, self.cuadros):
            ayudas.addWidget(c)
        ayudas.addStretch(1)
        capa.addLayout(ayudas)

        abajo = QtWidgets.QHBoxLayout()
        self.semaforo = QtWidgets.QLabel()
        self.semaforo.setToolTip(t("ayuda_semaforo"))
        abajo.addWidget(self.semaforo, 1)
        self.generar = {}
        for nivel in mod.NIVELES_GENERAR:
            b = QtWidgets.QPushButton()
            b.setToolTip(t("ayuda_generar"))
            b.clicked.connect(lambda _=False, n=nivel: self._generar(n))
            self.generar[nivel] = b
            if nivel == "medio":
                estilo.primario(b)
            abajo.addWidget(b)
        capa.addLayout(abajo)
        self.estado = estilo.etiqueta("", "tenue")
        capa.addWidget(self.estado)

    # --- refresco ---------------------------------------------------------------------

    def refrescar(self):
        """El árbol ha cambiado (acción, deshacer o rehacer): lista, valores e informe."""
        arbol = self.editor.arbol
        self.nombre.setText(arbol.nombre)
        if self.material.findData(arbol.material) < 0:
            self.material.addItem(texto_material(arbol.material), arbol.material)
        self.material.setCurrentIndex(self.material.findData(arbol.material))
        ids = [i for i in self._ids if i in arbol.modulos] or [arbol.tronco.id]
        self._sincronizando = True
        try:
            self.lista.clear()
            elementos = {}
            for m in arbol._orden():
                madre = elementos.get(m.padre)
                e = QtWidgets.QTreeWidgetItem(madre if madre is not None else self.lista)
                e.setText(0, nombre_modulo(m.id))
                e.setData(0, QtCore.Qt.UserRole, m.id)
                elementos[m.id] = e
            self.lista.expandAll()
            for i in ids:
                elementos[i].setSelected(True)
        finally:
            self._sincronizando = False
        self._ids = ids
        self._construir_parametros()
        self._informe()

    def _informe(self):
        arbol = self.editor.arbol
        color, triangulos = arbol.semaforo("medio")
        self.semaforo.setText('<span style="color:{}; font-size:16px;">&#9679;</span> {}'.format(
            _COLORES[color], t("semaforo_" + color, triangulos=_miles(triangulos))))
        for nivel, boton in self.generar.items():
            boton.setText(t("boton_generar", nivel=t("nivel_" + nivel),
                            triangulos=_miles(arbol.triangulos(nivel))))

    def _construir_parametros(self):
        abierto = self._avanzado_abierto
        while self.capa_parametros.count():
            w = self.capa_parametros.takeAt(0).widget()
            if w is not None:
                w.hide()  # deleteLater tarda: sin esto se ven dos juegos de deslizadores
                w.setParent(None)
                w.deleteLater()
        self._filas = {}
        if not self._ids:
            return
        principal = self.editor.arbol.modulos[self._ids[0]]
        tipo = principal.tipo
        titulo = QtWidgets.QLabel("<b>{}</b>{}".format(
            nombre_modulo(principal.id),
            t("varias_seleccionadas", n=len(self._ids)) if len(self._ids) > 1 else ""))
        self.capa_parametros.addWidget(titulo)
        forma = Seccion(t("seccion_forma"))
        hojas = Seccion(t("seccion_follaje"))
        avanzado = Seccion(t("seccion_avanzado"), plegada=not abierto)
        avanzado.boton.toggled.connect(lambda a: setattr(self, "_avanzado_abierto", a))
        for nombre, (_, _, _, es_avanzado) in mod.PARAMETROS[tipo].items():
            fila = FilaParametro(self, tipo, nombre)
            fila.poner(principal.valores[nombre])
            seccion = hojas if nombre in mod.PARAMETROS_FOLLAJE else (avanzado if es_avanzado else forma)
            seccion.filas.addWidget(fila)
            self._filas[nombre] = fila
        self.capa_parametros.addWidget(forma)
        if tipo == mod.RAMA:
            usar = QtWidgets.QPushButton(t("boton_usar_como_hoja"))
            usar.setToolTip(t("ayuda_boton_usar_como_hoja"))
            usar.clicked.connect(self._usar_como_hoja)
            hojas.filas.addWidget(usar)
            self.capa_parametros.addWidget(hojas)
        self.capa_parametros.addWidget(avanzado)

    # --- deslizadores --------------------------------------------------------------------

    def empezar(self, _nombre):
        self.editor.empezar_cambio(self._ids)

    def cambiar(self, nombre, valor):
        self.editor.cambiar_valor(self._ids, nombre, valor, self._ids[0])

    def terminar(self):
        self.editor.terminar_cambio()

    def fijar(self, nombre, valor):
        self.editor.fijar_valor(self._ids, nombre, valor)

    # --- selección ------------------------------------------------------------------------

    def _seleccionar_ids(self, ids):
        self._ids = [i for i in ids if i in self.editor.arbol.modulos]
        self._sincronizando = True
        try:
            it = QtWidgets.QTreeWidgetItemIterator(self.lista)
            while it.value():
                e = it.value()
                e.setSelected(e.data(0, QtCore.Qt.UserRole) in self._ids)
                it += 1
        finally:
            self._sincronizando = False
        self.editor.seleccionar(self._ids)
        self._construir_parametros()
        self._actualizar_tiradores()

    def _seleccion_en_lista(self):
        if self._sincronizando:
            return
        ids = [e.data(0, QtCore.Qt.UserRole) for e in self.lista.selectedItems()]
        if ids:
            self._sincronizando = True
            try:
                self.editor.seleccionar(ids)
            finally:
                self._sincronizando = False
            self._ids = ids
            self._construir_parametros()
            self._actualizar_tiradores()

    def _seleccion_en_visor(self):
        if self._sincronizando or not self.isVisible():
            return
        ids = self.editor.ids_seleccionados_en_visor()
        if ids and ids != self._ids:
            self._sincronizando = True
            try:
                self._ids = ids
                it = QtWidgets.QTreeWidgetItemIterator(self.lista)
                while it.value():
                    e = it.value()
                    e.setSelected(e.data(0, QtCore.Qt.UserRole) in ids)
                    it += 1
            finally:
                self._sincronizando = False
            self._construir_parametros()
            self._actualizar_tiradores()

    def _actualizar_tiradores(self):
        if self.tiradores.isChecked() and len(self._ids) == 1:
            self.editor.mostrar_tiradores(self._ids[0])
            self._mensaje(t("tiradores_ayuda"))
        else:
            self.editor.quitar_tiradores()

    # --- herramientas -------------------------------------------------------------------

    def _mensaje(self, texto):
        self.estado.setText(texto)
        print("Árboles | " + texto)

    def _empezar_plantilla(self):
        self.editor.nueva(self.plantillas.currentData(), self.frondosidad.currentData())
        self._seleccionar_ids([self.editor.arbol.tronco.id])

    def _renombrar(self):
        nombre = self.nombre.text().strip()
        if nombre and nombre != self.editor.arbol.nombre:
            self.editor.renombrar(nombre)

    def _cambiar_material(self, *_):
        material = self.material.currentData()
        if material and material != self.editor.arbol.material:
            self.editor.cambiar_material(material)

    def _material_propio(self):
        from arboles import materiales_propios_ui
        juego = materiales_propios_ui.pedir(self, interfaz_maya.carpeta_biblioteca())
        if not juego:
            return
        indice = self.material.findData(juego)
        if indice < 0:
            self.material.addItem(texto_material(juego), juego)
            indice = self.material.findData(juego)
        else:
            self.material.setItemText(indice, texto_material(juego))
        self.material.setCurrentIndex(indice)
        if juego == self.editor.arbol.material:
            # Mismo nombre con imágenes nuevas: rehace el material de la escena
            from arboles import materiales
            materiales.rehacer_material_texturas(juego)
        self._cambiar_material()

    def _anadir(self):
        nuevo = self.editor.anadir_rama(self._ids[0])
        self._seleccionar_ids([nuevo])

    def _clic_visor(self):
        self.editor.herramienta_clic(al_anadir=lambda nuevo: self._seleccionar_ids([nuevo]))
        self._mensaje(t("clic_ayuda"))

    def _repetir(self):
        ramas = [i for i in self._ids if self.editor.arbol.modulos[i].tipo == mod.RAMA]
        if not ramas:
            self._mensaje(t("elige_rama"))
            return
        copias, ok = QtWidgets.QInputDialog.getInt(self, t("boton_repetir"), t("repetir_cuantas"), 4, 1, 12)
        if ok:
            nuevas = self.editor.repetir(ramas[0], copias)
            self._seleccionar_ids([ramas[0]] + nuevas)

    def _quitar(self):
        if not self.editor.quitar(self._ids):
            self._mensaje(t("no_quitar_tronco"))

    def _copiar(self):
        m = self.editor.arbol.modulos[self._ids[0]]
        self._portapapeles = (m.tipo, dict(m.valores))
        self._mensaje(t("ajustes_copiados", modulo=nombre_modulo(m.id)))

    def _pegar(self):
        if not self._portapapeles:
            self._mensaje(t("nada_copiado"))
            return
        tipo, valores = self._portapapeles
        destinos = [i for i in self._ids if self.editor.arbol.modulos[i].tipo == tipo]
        if destinos:
            self.editor.pegar(valores, destinos)
            self._mensaje(t("ajustes_pegados", n=len(destinos)))

    def _enderezar(self):
        self.editor.enderezar(self._ids)

    def _biblioteca(self):
        return Biblioteca(interfaz_maya.carpeta_biblioteca())

    def _usar_como_hoja(self):
        """Guarda la malla seleccionada en la escena como hoja propia y la pone en las ramas elegidas."""
        from arboles import hoja_maya
        ids = list(self._ids)
        forma = hoja_maya.malla_seleccionada(excluir=self.editor.grupo)
        if forma is None:
            self._mensaje(t("hoja_propia_sin_malla"))
            return
        sugerido = cmds.listRelatives(forma, parent=True)[0] if cmds.listRelatives(forma, parent=True) else "hoja"
        nombre, aceptado = QtWidgets.QInputDialog.getText(self, t("boton_usar_como_hoja"), t("hoja_propia_nombre"),
                                                          text=sugerido)
        if not aceptado or not nombre.strip():
            return
        try:
            datos = hoja_maya.leer_hoja(forma)
        except ValueError as error:
            self._mensaje(t("hoja_propia_mal", error=error))
            return
        tipo = self._biblioteca().guardar_hoja(nombre.strip(), datos)
        ramas = [i for i in ids if i in self.editor.arbol.modulos and self.editor.arbol.modulos[i].tipo == mod.RAMA]
        con_hojas = [i for i in ramas if self.editor.arbol.modulos[i].valores.get("follaje", "ninguno") != "ninguno"]
        ramas = con_hojas or ramas  # cambia las hojas que ya había; las ramas sin hojas, solo si no hay otras
        if ramas:
            self._ids = ramas
            self.editor.fijar_valor(ramas, "follaje", tipo)
            self._seleccionar_ids(ramas)
        else:
            self._construir_parametros()
        self._mensaje(t("hoja_propia_guardada", nombre=tipo[len(follaje.PROPIA):].replace("_", " "), n=len(ramas)))

    def _llenar_favoritas(self):
        self.menu_favoritas.clear()
        self.menu_favoritas.addAction(t("favorita_guardar"), self._guardar_favorita)
        nombres = self._biblioteca().ramas()
        if nombres:
            self.menu_favoritas.addSeparator()
        for nombre in nombres:
            self.menu_favoritas.addAction(t("favorita_insertar", nombre=nombre),
                                          lambda n=nombre: self._insertar_favorita(n))

    def _guardar_favorita(self):
        id_ = self._ids[0]
        if self.editor.arbol.modulos[id_].tipo != mod.RAMA:
            self._mensaje(t("elige_rama"))
            return
        nombre, ok = QtWidgets.QInputDialog.getText(self, t("boton_favoritas"), t("favorita_nombre"))
        if ok and nombre.strip():
            self._biblioteca().guardar_rama(nombre.strip(), self.editor.arbol.subarbol(id_))
            self._mensaje(t("favorita_guardada", nombre=nombre.strip()))

    def _insertar_favorita(self, nombre):
        nuevo = self.editor.injertar(self._biblioteca().cargar_rama(nombre), self._ids[0])
        self._seleccionar_ids([nuevo])

    def _plantar(self):
        from arboles import plantar_ui
        plantar_ui.mostrar()

    def _generar(self, nivel):
        grupo = self.editor.generar(nivel)
        if grupo:
            cmds.select(grupo)
            self._mensaje(t("generado_editor", grupo=grupo.split("|")[-1], nivel=t("nivel_" + nivel)))

    def _guardar(self):
        self._renombrar()
        bib = self._biblioteca()
        arbol = self.editor.arbol
        if bib.existe(arbol.nombre):
            r = QtWidgets.QMessageBox.question(self, t("boton_guardar"), t("sobrescribir", nombre=arbol.nombre))
            if r != QtWidgets.QMessageBox.Yes:
                return
        ruta = bib.guardar(arbol)
        try:
            self.editor.quitar_tiradores()
            self.editor.miniatura(bib.ruta_miniatura(arbol.nombre))
        except Exception as error:  # la miniatura no debe impedir guardar
            print("Árboles | miniatura: {}".format(error))
        finally:
            self._actualizar_tiradores()
        self._mensaje(t("guardado", ruta=ruta))
        self._ofrecer_actualizar(arbol)
        from arboles import plantar_ui
        plantar_ui.refrescar_si_abierto()

    def _ofrecer_actualizar(self, arbol):
        """Si el árbol está plantado en la escena, ofrece actualizar todas sus copias."""
        from arboles import plantar
        from arboles.biblioteca import nombre_de_archivo
        nombre = nombre_de_archivo(arbol.nombre)
        copias = [c for c in plantar.plantados()
                  if cm.leer_texto(cmds.getAttr(c + "." + plantar.ATRIBUTO_PLANTADO), plantar.ATRIBUTO_MAESTRO) == nombre]
        if not copias:
            return
        r = QtWidgets.QMessageBox.question(self, t("boton_guardar"), t("actualizar_copias", n=len(copias)))
        if r == QtWidgets.QMessageBox.Yes:
            plantar.actualizar_maestros(arbol)
            self._mensaje(t("copias_actualizadas", n=len(copias)))

    def _abrir(self):
        bib = self._biblioteca()
        nombres = bib.arboles()
        if not nombres:
            self._mensaje(t("biblioteca_vacia"))
            return
        nombre, ok = QtWidgets.QInputDialog.getItem(self, t("boton_abrir"), t("abrir_cual"), nombres, 0, False)
        if ok:
            self.editor.cargar(bib.cargar(nombre))
            self._seleccionar_ids([self.editor.arbol.tronco.id])

    # --- cierre ---------------------------------------------------------------------------------

    def closeEvent(self, evento):
        if self._trabajo is not None and cmds.scriptJob(exists=self._trabajo):
            cmds.scriptJob(kill=self._trabajo, force=True)
        self.editor.cerrar()
        global _ventana
        _ventana = None
        super(VentanaEditor, self).closeEvent(evento)


def mostrar():
    global _ventana
    if _ventana is None:
        _ventana = VentanaEditor()
    _ventana.show()
    _ventana.raise_()
    return _ventana
