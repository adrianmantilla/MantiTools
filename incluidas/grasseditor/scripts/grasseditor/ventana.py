"""Ventana de GrassEditor: cuatro pestañas en el orden en que se trabaja.

1 · Zonas        dónde crece la capa: todo el suelo, pincel, reglas, curvas y objetos
2 · Hierba       la mezcla de tipos, la densidad y el editor de matas
3 · Rendimiento  visor ligero, cámara de render, detalle por distancia, semáforo
4 · Acabado      material, convertir y exportar

Arriba está la capa con la que se trabaja. Cada cambio es un paso de Ctrl+Z.
"""

from maya import cmds

try:
    from PySide6 import QtCore, QtWidgets
except ImportError:  # Maya anterior a 2025
    from PySide2 import QtCore, QtWidgets

import grasseditor
from grasseditor import escena, estilo, pincel, tipos
from grasseditor import estadisticas as est
from grasseditor.i18n import t

_ventana = None
_COLORES = {"verde": "#3fa34d", "ambar": "#e0b000", "rojo": "#d64541"}


def _ventana_maya():
    from maya import OpenMayaUI as omui
    try:
        from shiboken6 import wrapInstance
    except ImportError:
        from shiboken2 import wrapInstance
    puntero = omui.MQtUtil.mainWindow()
    return wrapInstance(int(puntero), QtWidgets.QWidget) if puntero else None


def _nombre_tipo(clave):
    texto = t("tipo_" + clave)
    return clave if texto == "tipo_" + clave else texto


class Ventana(QtWidgets.QDialog):

    def __init__(self, padre=None):
        super(Ventana, self).__init__(padre or _ventana_maya())
        self.setWindowTitle(t("ventana_titulo"))
        estilo.aplicar(self, "GrassEditorVentana")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self.resize(460, 720)
        self._cargando = False
        self._temporizador = QtCore.QTimer(self)
        self._temporizador.setSingleShot(True)
        self._temporizador.timeout.connect(self.refrescar_cifras)
        self._construir()
        self.refrescar()

    # --- construcción --------------------------------------------------------------------

    def _boton(self, clave, funcion, ayuda=True):
        b = QtWidgets.QPushButton(t(clave))
        if ayuda:
            b.setToolTip(t("ayuda_" + clave))
        b.clicked.connect(lambda *_: funcion())
        return b

    def _numero(self, minimo, maximo, valor, paso=1.0, decimales=0, sufijo="", al_cambiar=None):
        caja = QtWidgets.QDoubleSpinBox() if decimales else QtWidgets.QSpinBox()
        if decimales:
            caja.setDecimals(decimales)
        caja.setRange(minimo, maximo)
        caja.setSingleStep(paso)
        caja.setValue(valor)
        caja.setSuffix(sufijo)
        caja.setKeyboardTracking(False)
        if al_cambiar:
            caja.valueChanged.connect(lambda *_: self._si_no_carga(al_cambiar))
        return caja

    def _si_no_carga(self, funcion):
        if not self._cargando:
            funcion()

    def _grupo(self, clave):
        caja = QtWidgets.QGroupBox(t(clave))
        capa = QtWidgets.QVBoxLayout(caja)
        capa.setSpacing(4)
        return caja, capa

    def _fila(self, *widgets):
        fila = QtWidgets.QHBoxLayout()
        for w in widgets:
            if isinstance(w, str):
                fila.addWidget(QtWidgets.QLabel(w))
            elif w is None:
                fila.addStretch(1)
            else:
                fila.addWidget(w)
        return fila

    def _construir(self):
        exterior = QtWidgets.QVBoxLayout(self)
        exterior.setContentsMargins(0, 0, 0, 0)
        exterior.setSpacing(0)
        cabecera, _ = estilo.cabecera("GrassEditor", estilo.COLORES["grasseditor"], grasseditor.__version__)
        exterior.addWidget(cabecera)
        capa = QtWidgets.QVBoxLayout()
        capa.setContentsMargins(10, 8, 10, 8)
        exterior.addLayout(capa, 1)
        # Capa activa
        self.combo_capa = QtWidgets.QComboBox()
        self.combo_capa.setToolTip(t("ayuda_combo_capa"))
        self.combo_capa.currentIndexChanged.connect(lambda *_: self._si_no_carga(self.cargar_capa))
        capa.addLayout(self._fila(t("etiqueta_capa"), self.combo_capa))
        capa.addLayout(self._fila(estilo.primario(self._boton("boton_nueva_capa", self._nueva_capa)),
                                  self._boton("boton_nueva_pincel", lambda: self._nueva_capa("pincel")),
                                  self._boton("boton_duplicar", self._duplicar),
                                  self._boton("boton_borrar_capa", self._borrar)))
        self.casilla_activa = QtWidgets.QCheckBox(t("casilla_activa"))
        self.casilla_activa.setToolTip(t("ayuda_casilla_activa"))
        self.casilla_activa.toggled.connect(lambda v: self._cambiar(activa=bool(v)))
        self.etiqueta_suelo = QtWidgets.QLabel()
        estilo.rol(self.etiqueta_suelo, "tenue")
        capa.addLayout(self._fila(self.casilla_activa, None, self.etiqueta_suelo))

        self.pestanas = QtWidgets.QTabWidget()
        self.pestanas.addTab(self._pestana_zonas(), t("pestana_zonas"))
        self.pestanas.addTab(self._pestana_hierba(), t("pestana_hierba"))
        self.pestanas.addTab(self._pestana_rendimiento(), t("pestana_rendimiento"))
        self.pestanas.addTab(self._pestana_acabado(), t("pestana_acabado"))
        capa.addWidget(self.pestanas, 1)

        self.semaforo = QtWidgets.QLabel()
        self.semaforo.setWordWrap(True)
        self.semaforo.setToolTip(t("ayuda_semaforo"))
        capa.addWidget(self.semaforo)
        self.estado = QtWidgets.QLabel()
        estilo.rol(self.estado, "tenue")
        self.estado.setWordWrap(True)
        capa.addWidget(self.estado)

    def _envolver(self, widget):
        area = QtWidgets.QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QtWidgets.QFrame.NoFrame)
        area.setWidget(widget)
        return area

    def _pestana_zonas(self):
        w = QtWidgets.QWidget()
        capa = QtWidgets.QVBoxLayout(w)

        caja, c = self._grupo("grupo_zona")
        c.addLayout(self._fila(self._boton("boton_todo_suelo", lambda: self._llenar(255)),
                               self._boton("boton_vaciar", lambda: self._llenar(0))))
        self.pinceles = QtWidgets.QButtonGroup(self)
        botones = []
        for i, modo in enumerate(("poner", "quitar", "suavizar")):
            b = QtWidgets.QPushButton(t("pincel_" + modo))
            b.setCheckable(True)
            b.setToolTip(t("ayuda_pincel_" + modo))
            self.pinceles.addButton(b, i)
            botones.append(b)
        self.pinceles.buttonClicked.connect(lambda *_: self._pincel())
        c.addLayout(self._fila(*botones))
        self.radio = self._numero(5, 5000, 100, 10, sufijo=" cm", al_cambiar=self._ajustar_pincel)
        self.radio.setToolTip(t("ayuda_radio"))
        self.fuerza = self._numero(0.05, 1.0, 0.6, 0.05, 2, al_cambiar=self._ajustar_pincel)
        self.fuerza.setToolTip(t("ayuda_fuerza"))
        c.addLayout(self._fila(t("etiqueta_radio"), self.radio, t("etiqueta_fuerza"), self.fuerza,
                               self._boton("boton_soltar_pincel", self._soltar_pincel)))
        c.addWidget(QtWidgets.QLabel(t("pincel_consejo")))
        capa.addWidget(caja)

        caja, c = self._grupo("grupo_reglas")
        self.pendiente = self._numero(0, 90, 90, 1, sufijo="°", al_cambiar=self._reglas)
        self.pendiente.setToolTip(t("ayuda_pendiente"))
        c.addLayout(self._fila(t("etiqueta_pendiente"), self.pendiente, None))
        self.casilla_hmin = QtWidgets.QCheckBox(t("etiqueta_altura_min"))
        self.casilla_hmax = QtWidgets.QCheckBox(t("etiqueta_altura_max"))
        self.hmin = self._numero(-100000, 100000, 0, 10, sufijo=" cm", al_cambiar=self._reglas)
        self.hmax = self._numero(-100000, 100000, 500, 10, sufijo=" cm", al_cambiar=self._reglas)
        for casilla in (self.casilla_hmin, self.casilla_hmax):
            casilla.setToolTip(t("ayuda_altura"))
            casilla.toggled.connect(lambda *_: self._si_no_carga(self._reglas))
        c.addLayout(self._fila(self.casilla_hmin, self.hmin, self.casilla_hmax, self.hmax))
        self.borde = self._numero(1, 1000, 40, 5, sufijo=" cm", al_cambiar=self._reglas)
        self.borde.setToolTip(t("ayuda_borde"))
        c.addLayout(self._fila(t("etiqueta_borde"), self.borde, None))
        capa.addWidget(caja)

        caja, c = self._grupo("grupo_curvas")
        self.lista_curvas = QtWidgets.QListWidget()
        self.lista_curvas.setMaximumHeight(80)
        c.addWidget(self.lista_curvas)
        self.ancho_camino = self._numero(10, 5000, 120, 10, sufijo=" cm")
        self.ancho_camino.setToolTip(t("ayuda_ancho_camino"))
        c.addLayout(self._fila(self._boton("boton_curva_dentro", lambda: self._anadir_curvas("dentro", True)),
                               self._boton("boton_curva_fuera", lambda: self._anadir_curvas("fuera", True))))
        c.addLayout(self._fila(self._boton("boton_camino", lambda: self._anadir_curvas("fuera", False)),
                               t("etiqueta_ancho"), self.ancho_camino,
                               self._boton("boton_quitar_curva", self._quitar_curva)))
        capa.addWidget(caja)

        caja, c = self._grupo("grupo_objetos")
        self.etiqueta_objetos = QtWidgets.QLabel()
        c.addWidget(self.etiqueta_objetos)
        c.addLayout(self._fila(self._boton("boton_objetos_sel", self._anadir_objetos),
                               self._boton("boton_objetos_auto", self._objetos_auto),
                               self._boton("boton_quitar_objetos", self._quitar_objetos)))
        self.copa = self._numero(0.0, 1.0, 0.5, 0.05, 2, al_cambiar=self._reglas)
        self.copa.setToolTip(t("ayuda_copa"))
        c.addLayout(self._fila(t("etiqueta_copa"), self.copa, None))
        capa.addWidget(caja)
        capa.addStretch(1)
        return self._envolver(w)

    def _pestana_hierba(self):
        w = QtWidgets.QWidget()
        capa = QtWidgets.QVBoxLayout(w)
        caja, c = self._grupo("grupo_mezcla")
        self.tabla = QtWidgets.QTableWidget(0, 2)
        self.tabla.setHorizontalHeaderLabels([t("columna_tipo"), t("columna_parte")])
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setMaximumHeight(150)
        c.addWidget(self.tabla)
        c.addLayout(self._fila(self._boton("boton_anadir_tipo", self._anadir_tipo),
                               self._boton("boton_quitar_tipo", self._quitar_tipo), None))
        self.densidad = self._numero(1, 400, 100, 5, sufijo=" %", al_cambiar=self._hierba)
        self.densidad.setToolTip(t("ayuda_densidad"))
        self.semilla = self._numero(1, 99999, 1, 1, al_cambiar=self._hierba)
        self.semilla.setToolTip(t("ayuda_semilla"))
        c.addLayout(self._fila(t("etiqueta_densidad"), self.densidad, t("etiqueta_semilla"), self.semilla,
                               self._boton("boton_otra_semilla", self._otra_semilla)))
        self.escala_var = self._numero(0, 80, 25, 5, sufijo=" %", al_cambiar=self._hierba)
        self.inclinacion = self._numero(0, 45, 12, 1, sufijo="°", al_cambiar=self._hierba)
        c.addLayout(self._fila(t("etiqueta_escala_var"), self.escala_var, t("etiqueta_inclinacion"),
                               self.inclinacion))
        capa.addWidget(caja)

        caja, c = self._grupo("grupo_mata")
        self.combo_tipo = QtWidgets.QComboBox()
        self.combo_tipo.currentIndexChanged.connect(lambda *_: self._cargar_tipo())
        c.addLayout(self._fila(t("etiqueta_tipo"), self.combo_tipo))
        self.campos_tipo = {}
        rejilla = QtWidgets.QGridLayout()
        campos = (("altura_min", 0.5, 1000, 1, 1, " cm"), ("altura_max", 0.5, 1000, 1, 1, " cm"),
                  ("densidad", 0.1, 2000, 1, 1, " /m²"), ("briznas", 1, 200, 1, 0, ""),
                  ("segmentos", 1, 10, 1, 0, ""), ("anchura", 0.02, 10, 0.05, 2, " cm"),
                  ("curvatura", 0, 1, 0.05, 2, ""), ("abertura", 0, 85, 1, 0, "°"),
                  ("radio", 0, 100, 0.5, 1, " cm"))
        for i, (campo, mi, ma, paso, dec, suf) in enumerate(campos):
            caja_num = self._numero(mi, ma, mi, paso, dec, suf)
            caja_num.setToolTip(t("ayuda_campo_" + campo))
            self.campos_tipo[campo] = caja_num
            rejilla.addWidget(QtWidgets.QLabel(t("campo_" + campo)), i // 2, (i % 2) * 2)
            rejilla.addWidget(caja_num, i // 2, (i % 2) * 2 + 1)
        c.addLayout(rejilla)
        self.etiqueta_tris_tipo = QtWidgets.QLabel()
        estilo.rol(self.etiqueta_tris_tipo, "tenue")
        c.addWidget(self.etiqueta_tris_tipo)
        c.addLayout(self._fila(self._boton("boton_aplicar_tipo", self._aplicar_tipo),
                               self._boton("boton_serie_tipo", self._serie_tipo),
                               self._boton("boton_nuevo_tipo", self._nuevo_tipo)))
        capa.addWidget(caja)
        capa.addStretch(1)
        return self._envolver(w)

    def _pestana_rendimiento(self):
        w = QtWidgets.QWidget()
        capa = QtWidgets.QVBoxLayout(w)
        caja, c = self._grupo("grupo_visor")
        self.visor = self._numero(0.1, 100, 10, 1, 1, " %", al_cambiar=self._rendimiento)
        self.visor.setToolTip(t("ayuda_visor"))
        self.como = QtWidgets.QComboBox()
        for como in ("cajas", "tarjetas", "matas"):
            self.como.addItem(t("como_" + como), como)
        self.como.setToolTip(t("ayuda_como"))
        self.como.currentIndexChanged.connect(lambda *_: self._si_no_carga(self._rendimiento))
        c.addLayout(self._fila(t("etiqueta_visor"), self.visor, t("etiqueta_como"), self.como))
        capa.addWidget(caja)

        caja, c = self._grupo("grupo_render")
        self.combo_camara = QtWidgets.QComboBox()
        self.combo_camara.setToolTip(t("ayuda_camara"))
        self.combo_camara.activated.connect(lambda *_: self._camara())
        c.addLayout(self._fila(t("etiqueta_camara"), self.combo_camara,
                               self._boton("boton_refrescar", self.refrescar)))
        self.recorte = QtWidgets.QCheckBox(t("casilla_recorte"))
        self.recorte.setToolTip(t("ayuda_recorte"))
        self.margen = self._numero(0, 45, 10, 1, sufijo="°", al_cambiar=self._rendimiento)
        self.recorte.toggled.connect(lambda *_: self._si_no_carga(self._rendimiento))
        c.addLayout(self._fila(self.recorte, t("etiqueta_margen"), self.margen))
        self.lod = QtWidgets.QCheckBox(t("casilla_lod"))
        self.lod.setToolTip(t("ayuda_lod"))
        self.lod.toggled.connect(lambda *_: self._si_no_carga(self._rendimiento))
        self.cerca = self._numero(0.5, 500, 8, 0.5, 1, " m", al_cambiar=self._rendimiento)
        self.medio = self._numero(0.5, 1000, 20, 0.5, 1, " m", al_cambiar=self._rendimiento)
        c.addWidget(self.lod)
        c.addLayout(self._fila(t("etiqueta_cerca"), self.cerca, t("etiqueta_medio"), self.medio))
        self.aclarar = QtWidgets.QCheckBox(t("casilla_aclarar"))
        self.aclarar.setToolTip(t("ayuda_aclarar"))
        self.aclarar.toggled.connect(lambda *_: self._si_no_carga(self._rendimiento))
        self.aclarar_cantidad = self._numero(0, 90, 50, 5, sufijo=" %", al_cambiar=self._rendimiento)
        c.addLayout(self._fila(self.aclarar, self.aclarar_cantidad, None))
        self.vista_render = QtWidgets.QPushButton(t("boton_vista_render"))
        self.vista_render.setCheckable(True)
        self.vista_render.setToolTip(t("ayuda_boton_vista_render"))
        self.vista_render.toggled.connect(self._vista_render)
        c.addWidget(self.vista_render)
        capa.addWidget(caja)

        caja, c = self._grupo("grupo_cifras")
        self.cifras = QtWidgets.QLabel()
        self.cifras.setTextFormat(QtCore.Qt.RichText)
        self.cifras.setWordWrap(True)
        c.addWidget(self.cifras)
        c.addLayout(self._fila(self._boton("boton_analizar", self._analizar),
                               self._boton("boton_hornear", self._hornear),
                               self._boton("boton_deshornear", self._deshornear)))
        capa.addWidget(caja)
        capa.addStretch(1)
        return self._envolver(w)

    def _pestana_acabado(self):
        w = QtWidgets.QWidget()
        capa = QtWidgets.QVBoxLayout(w)
        caja, c = self._grupo("grupo_material")
        self.material = QtWidgets.QComboBox()
        self.material.addItem(t("material_hierba"), "hierba")
        self.material.addItem(t("material_clay"), "clay")
        self.material.setToolTip(t("ayuda_material"))
        self.material.activated.connect(lambda *_: self._material())
        self.translucidez = self._numero(0, 1, 0.5, 0.05, 2, al_cambiar=self._material)
        self.translucidez.setToolTip(t("ayuda_translucidez"))
        c.addLayout(self._fila(self.material, t("etiqueta_translucidez"), self.translucidez))
        c.addWidget(QtWidgets.QLabel(t("material_nota")))
        c.addWidget(self._boton("boton_tenir_suelo", self._tenir_suelo))
        capa.addWidget(caja)
        caja, c = self._grupo("grupo_convertir")
        c.addLayout(self._fila(self._boton("boton_sueltas", self._sueltas),
                               self._boton("boton_unir", self._unir)))
        capa.addWidget(caja)
        caja, c = self._grupo("grupo_exportar")
        c.addLayout(self._fila(self._boton("boton_exportar_puntos", self._exportar_puntos),
                               self._boton("boton_exportar_fbx", self._exportar_fbx)))
        capa.addWidget(caja)
        capa.addStretch(1)
        return self._envolver(w)

    # --- estado ---------------------------------------------------------------------------

    def capa(self):
        nombre = self.combo_capa.currentText()
        return nombre if nombre and cmds.objExists(nombre) else None

    def mensaje(self, texto):
        self.estado.setText(texto)
        print("GrassEditor | " + texto)

    def refrescar(self):
        """Vuelve a leer la escena: capas, cámaras, tipos y cifras."""
        self._cargando = True
        try:
            actual = self.combo_capa.currentText()
            self.combo_capa.clear()
            for capa in escena.capas():
                self.combo_capa.addItem(capa)
            if actual and self.combo_capa.findText(actual) >= 0:
                self.combo_capa.setCurrentIndex(self.combo_capa.findText(actual))
            self.combo_camara.clear()
            for camara in escena.camaras():
                self.combo_camara.addItem(camara.split("|")[-1], camara)
            cat = escena.catalogo()
            tipo_actual = self.combo_tipo.currentData()
            self.combo_tipo.clear()
            for clave in cat.claves():
                self.combo_tipo.addItem(_nombre_tipo(clave), clave)
            if tipo_actual and self.combo_tipo.findData(tipo_actual) >= 0:
                self.combo_tipo.setCurrentIndex(self.combo_tipo.findData(tipo_actual))
            self.material.setCurrentIndex(0 if escena.material_actual() == "hierba" else 1)
            if cmds.objExists(escena.AJUSTES):
                self.translucidez.setValue(cmds.getAttr(escena.AJUSTES + ".translucidez"))
            self.vista_render.setChecked(escena.en_render())
        finally:
            self._cargando = False
        self.cargar_capa()
        self._cargar_tipo()

    def cargar_capa(self):
        capa = self.capa()
        self.pestanas.setEnabled(bool(capa))
        self.casilla_activa.setEnabled(bool(capa))
        if not capa:
            self.etiqueta_suelo.setText(t("sin_capas"))
            self.refrescar_cifras()
            return
        aj = escena.ajustes(capa)
        self._cargando = True
        try:
            suelo = escena.suelo(capa)
            texto = t("etiqueta_suelo", suelo=(suelo or "?").split("|")[-1])
            if aj.caras:
                texto += " · " + t("etiqueta_caras", n=len(aj.caras))
            if escena.horneada(capa):
                texto += " · " + t("etiqueta_horneada")
            self.etiqueta_suelo.setText(texto)
            self.casilla_activa.setChecked(aj.activa)
            r = aj.reglas
            self.pendiente.setValue(r.get("pendiente_max", 90))
            self.casilla_hmin.setChecked(r.get("altura_min") is not None)
            self.casilla_hmax.setChecked(r.get("altura_max") is not None)
            if r.get("altura_min") is not None:
                self.hmin.setValue(r["altura_min"])
            if r.get("altura_max") is not None:
                self.hmax.setValue(r["altura_max"])
            self.borde.setValue(r.get("borde", 40))
            self.copa.setValue(r.get("factor_copa", 0.5))
            self.lista_curvas.clear()
            for curva in r.get("curvas", []):
                tipo = "camino" if not curva.get("cerrada") else curva.get("modo")
                self.lista_curvas.addItem("{} · {}".format(curva.get("nombre", "?"), t("curva_" + tipo)))
            self.etiqueta_objetos.setText(t("etiqueta_objetos", objetos=len(r.get("objetos", [])),
                                            copas=len(r.get("copas", []))))
            self._cargar_mezcla(aj)
            self.densidad.setValue(aj.densidad)
            self.semilla.setValue(aj.semilla)
            self.escala_var.setValue(int(round(aj.escala_var * 100)))
            self.inclinacion.setValue(int(round(aj.inclinacion)))
            o = aj.opciones
            self.visor.setValue(o["visor_porcentaje"])
            self.como.setCurrentIndex(max(0, self.como.findData(o["visor_como"])))
            self.recorte.setChecked(o["recorte"])
            self.margen.setValue(int(o["margen"]))
            self.lod.setChecked(o["lod"])
            self.cerca.setValue(o["cerca"] / 100.0)
            self.medio.setValue(o["medio"] / 100.0)
            self.aclarar.setChecked(o["aclarar"])
            self.aclarar_cantidad.setValue(int(round(o["aclarar_cantidad"] * 100)))
            camara = escena.camara_de(capa)
            indice = self.combo_camara.findData(camara) if camara else -1
            if indice < 0 and camara:
                indice = self.combo_camara.findText(camara.split("|")[-1])
            self.combo_camara.setCurrentIndex(max(0, indice))
        finally:
            self._cargando = False
        pincel.ajustar(capa=capa)
        self.refrescar_cifras()

    def _cargar_mezcla(self, aj):
        cat = escena.catalogo()
        self.tabla.setRowCount(0)
        for clave, parte in aj.mezcla:
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)
            combo = QtWidgets.QComboBox()
            for c in cat.claves():
                combo.addItem(_nombre_tipo(c), c)
            combo.setCurrentIndex(max(0, combo.findData(clave)))
            combo.currentIndexChanged.connect(lambda *_: self._si_no_carga(self._hierba))
            self.tabla.setCellWidget(fila, 0, combo)
            caja = self._numero(1, 100, int(round(parte)), 5, sufijo=" %", al_cambiar=self._hierba)
            self.tabla.setCellWidget(fila, 1, caja)

    def _mezcla_tabla(self):
        mezcla = []
        for fila in range(self.tabla.rowCount()):
            clave = self.tabla.cellWidget(fila, 0).currentData()
            mezcla.append([clave, float(self.tabla.cellWidget(fila, 1).value())])
        return mezcla

    def programar_cifras(self, ms=400):
        self._temporizador.start(ms)

    def refrescar_cifras(self):
        capa = self.capa()
        inf = escena.informe_escena()
        color = inf.color
        punto = "<span style='color:{}'>●</span> ".format(_COLORES[color])
        texto = punto + t("semaforo_" + color, triangulos=est.corto(inf.triangulos), matas=est.miles(inf.matas),
                          memoria=est.bytes_legibles(inf.memoria))
        consejos = est.consejos(inf, {c: escena.ajustes(c).opciones for c in escena.capas()})
        if consejos:
            clave, valores = consejos[0]
            if "tipo" in valores:
                valores = dict(valores, tipo=_nombre_tipo(valores["tipo"]))
            texto += "<br>" + t(clave, **valores)
        self.semaforo.setText(texto)
        if not capa:
            self.cifras.setText("")
            return
        datos = escena.informe(capa)
        filas = [
            (t("cifra_matas"), est.miles(datos.get("matas", 0))),
            (t("cifra_descartadas"), est.miles(datos.get("descartadas", 0))),
            (t("cifra_triangulos"), est.corto(datos.get("triangulos", 0))),
            (t("cifra_unicos"), est.miles(inf.unicos)),
            (t("cifra_memoria"), est.bytes_legibles(datos.get("memoria", 0))),
            (t("cifra_sin_instancias"), est.bytes_legibles(datos.get("memoria_sin_instancias", 0))),
            (t("cifra_visor"), est.miles(datos.get("visor", 0))),
        ]
        self.cifras.setText("<table>" + "".join(
            "<tr><td>{}</td><td align='right'>&nbsp;&nbsp;<b>{}</b></td></tr>".format(a, b) for a, b in filas)
            + "</table>")

    # --- cambios de ajustes ------------------------------------------------------------------

    def _cambiar(self, **cambios):
        capa = self.capa()
        if not capa or self._cargando:
            return
        aj = escena.ajustes(capa)
        for clave, valor in cambios.items():
            if clave in ("reglas", "opciones"):
                getattr(aj, clave).update(valor)
            else:
                setattr(aj, clave, valor)
        escena.guardar_ajustes(capa, aj)
        self.programar_cifras()

    def _reglas(self):
        self._cambiar(reglas={
            "pendiente_max": float(self.pendiente.value()),
            "altura_min": float(self.hmin.value()) if self.casilla_hmin.isChecked() else None,
            "altura_max": float(self.hmax.value()) if self.casilla_hmax.isChecked() else None,
            "borde": float(self.borde.value()),
            "factor_copa": float(self.copa.value())})

    def _hierba(self):
        mezcla = self._mezcla_tabla()
        if not mezcla:
            return
        self._cambiar(mezcla=mezcla, densidad=float(self.densidad.value()), semilla=int(self.semilla.value()),
                      escala_var=self.escala_var.value() / 100.0, inclinacion=float(self.inclinacion.value()))

    def _rendimiento(self):
        self._cambiar(opciones={
            "visor_porcentaje": float(self.visor.value()), "visor_como": self.como.currentData(),
            "recorte": self.recorte.isChecked(), "margen": float(self.margen.value()),
            "lod": self.lod.isChecked(), "cerca": self.cerca.value() * 100.0, "medio": self.medio.value() * 100.0,
            "aclarar": self.aclarar.isChecked(), "aclarar_cantidad": self.aclarar_cantidad.value() / 100.0})

    # --- capas ------------------------------------------------------------------------------

    def _nueva_capa(self, zona="objeto"):
        suelo, caras = escena.suelo_de_seleccion()
        if not suelo:
            self.mensaje(t("error_sin_malla"))
            return
        mezcla = self._mezcla_tabla() if self.capa() else None
        try:
            capa = escena.crear_capa(suelo, caras, zona=zona, mezcla=mezcla or None)
        except Exception as error:
            self.mensaje(t("error_crear_capa", error=error))
            raise
        cmds.select(clear=True)
        self.refrescar()
        self.combo_capa.setCurrentIndex(self.combo_capa.findText(capa))
        if zona == "pincel":
            self.pinceles.button(0).setChecked(True)
            self._pincel()
        self.mensaje(t("capa_creada", capa=capa, suelo=suelo.split("|")[-1]))

    def _duplicar(self):
        capa = self.capa()
        if capa:
            nueva = escena.duplicar_capa(capa)
            self.refrescar()
            self.combo_capa.setCurrentIndex(self.combo_capa.findText(nueva))

    def _borrar(self):
        capa = self.capa()
        if not capa:
            return
        si, no = t("boton_si"), t("boton_no")
        if cmds.confirmDialog(title=t("ventana_titulo"), message=t("confirmar_borrar", capa=capa),
                              button=[si, no], defaultButton=no, cancelButton=no, dismissString=no) != si:
            return
        pincel.soltar()
        escena.borrar_capa(capa)
        self.refrescar()

    # --- zonas --------------------------------------------------------------------------------

    def _llenar(self, valor):
        capa = self.capa()
        if capa:
            pincel.llenar(capa, valor)
            self.programar_cifras()

    def _pincel(self):
        capa = self.capa()
        if not capa:
            return
        modo = ("poner", "quitar", "suavizar")[max(0, self.pinceles.checkedId())]
        pincel.activar(capa, modo, self.radio.value(), self.fuerza.value(), al_pintar=self.programar_cifras)
        self.mensaje(t("pincel_activo", modo=t("pincel_" + modo)))

    def _ajustar_pincel(self):
        if self.pinceles.checkedId() >= 0:
            pincel.ajustar(radio=self.radio.value(), fuerza=self.fuerza.value())

    def _soltar_pincel(self):
        pincel.soltar()
        boton = self.pinceles.checkedButton()
        if boton:
            self.pinceles.setExclusive(False)
            boton.setChecked(False)
            self.pinceles.setExclusive(True)

    def _anadir_curvas(self, modo, cerrada):
        capa = self.capa()
        if not capa:
            return
        nuevas = escena.curvas_de_seleccion()
        if not nuevas:
            self.mensaje(t("error_sin_curvas"))
            return
        aj = escena.ajustes(capa)
        for curva in nuevas:
            if cerrada and not curva["cerrada"]:
                self.mensaje(t("aviso_curva_abierta", curva=curva["nombre"]))
                curva["cerrada"] = True
            if not cerrada:
                curva["cerrada"] = False
            curva["modo"] = modo
            curva["ancho"] = float(self.ancho_camino.value()) if not cerrada else 0.0
            aj.reglas["curvas"].append(curva)
        escena.guardar_ajustes(capa, aj)
        self.cargar_capa()

    def _quitar_curva(self):
        capa = self.capa()
        fila = self.lista_curvas.currentRow()
        if not capa or fila < 0:
            return
        aj = escena.ajustes(capa)
        del aj.reglas["curvas"][fila]
        escena.guardar_ajustes(capa, aj)
        self.cargar_capa()

    def _anadir_objetos(self):
        capa = self.capa()
        if not capa:
            return
        nuevos = escena.objetos_de_seleccion()
        if not nuevos:
            self.mensaje(t("error_sin_objetos"))
            return
        aj = escena.ajustes(capa)
        aj.reglas["objetos"] = list(aj.reglas.get("objetos", [])) + nuevos
        escena.guardar_ajustes(capa, aj)
        self.cargar_capa()

    def _objetos_auto(self):
        capa = self.capa()
        if not capa:
            return
        objetos, copas = escena.objetos_automaticos(excluir=escena.suelo(capa))
        aj = escena.ajustes(capa)
        aj.reglas["objetos"], aj.reglas["copas"] = objetos, copas
        escena.guardar_ajustes(capa, aj)
        self.mensaje(t("objetos_encontrados", objetos=len(objetos), copas=len(copas)))
        self.cargar_capa()

    def _quitar_objetos(self):
        capa = self.capa()
        if capa:
            aj = escena.ajustes(capa)
            aj.reglas["objetos"], aj.reglas["copas"] = [], []
            escena.guardar_ajustes(capa, aj)
            self.cargar_capa()

    # --- hierba ------------------------------------------------------------------------------

    def _anadir_tipo(self):
        mezcla = self._mezcla_tabla()
        usadas = {c for c, _ in mezcla}
        libre = next((c for c in escena.catalogo().claves() if c not in usadas), None)
        if libre:
            mezcla.append([libre, 20.0])
            self._cambiar(mezcla=mezcla)
            self.cargar_capa()

    def _quitar_tipo(self):
        fila = self.tabla.currentRow()
        mezcla = self._mezcla_tabla()
        if len(mezcla) <= 1:
            return
        del mezcla[fila if fila >= 0 else -1]
        self._cambiar(mezcla=mezcla)
        self.cargar_capa()

    def _otra_semilla(self):
        self.semilla.setValue(self.semilla.value() % 99999 + 1)

    def _cargar_tipo(self):
        clave = self.combo_tipo.currentData()
        if not clave:
            return
        tipo = escena.catalogo()[clave]
        self._cargando = True
        try:
            for campo, caja in self.campos_tipo.items():
                caja.setValue(getattr(tipo, campo))
        finally:
            self._cargando = False
        from grasseditor.capa import triangulos_tipo
        tris = triangulos_tipo(tipo)
        self.etiqueta_tris_tipo.setText(t("tris_tipo", completa=tris[0], simple=tris[1], tarjeta=tris[2]))

    def _tipo_editado(self, clave=None):
        tipo = escena.catalogo()[self.combo_tipo.currentData()]
        cambios = {campo: caja.value() for campo, caja in self.campos_tipo.items()}
        if clave:
            cambios["clave"] = clave
            cambios["propio"] = True
        return tipo.copiar(**cambios).validar()

    def _aplicar_tipo(self):
        tipo = escena.guardar_tipo(self._tipo_editado())
        self.mensaje(t("tipo_guardado", tipo=_nombre_tipo(tipo.clave)))
        self._cargar_tipo()
        self.programar_cifras()

    def _serie_tipo(self):
        if escena.restaurar_tipo(self.combo_tipo.currentData()):
            self._cargar_tipo()
            self.programar_cifras()

    def _nuevo_tipo(self):
        nombre, ok = QtWidgets.QInputDialog.getText(self, t("ventana_titulo"), t("pedir_nombre_tipo"))
        if not ok or not nombre.strip():
            return
        clave = tipos.clave_libre(nombre, set(escena.catalogo().claves()))
        escena.guardar_tipo(self._tipo_editado(clave))
        self.refrescar()
        self.combo_tipo.setCurrentIndex(self.combo_tipo.findData(clave))
        self.mensaje(t("tipo_nuevo", tipo=clave))

    # --- rendimiento --------------------------------------------------------------------------

    def _camara(self):
        capa = self.capa()
        camara = self.combo_camara.currentData()
        if capa and camara:
            escena.conectar_camara(capa, camara)
            self.programar_cifras()

    def _vista_render(self, activo):
        if self._cargando:
            return
        escena.fijar_render(activo)
        self.mensaje(t("vista_render_si" if activo else "vista_render_no"))
        self.programar_cifras()

    def _analizar(self):
        inf = escena.informe_escena()
        lineas = [t("analisis_total", matas=est.miles(inf.matas), triangulos=est.corto(inf.triangulos),
                    memoria=est.bytes_legibles(inf.memoria),
                    sin=est.bytes_legibles(inf.memoria_sin_instancias)), ""]
        for capa, tris in sorted(inf.por_capa.items(), key=lambda x: -x[1]):
            datos = escena.informe(capa)
            lineas.append(t("analisis_capa", capa=capa, matas=est.miles(datos.get("matas", 0)),
                            triangulos=est.corto(tris), parte=int(round(100.0 * tris / (inf.triangulos or 1)))))
        lineas.append("")
        for clave, valores in est.consejos(inf, {c: escena.ajustes(c).opciones for c in escena.capas()}):
            if "tipo" in valores:
                valores = dict(valores, tipo=_nombre_tipo(valores["tipo"]))
            lineas.append("• " + t(clave, **valores))
        texto = "\n".join(lineas)
        print("GrassEditor |\n" + texto)
        cmds.confirmDialog(title=t("boton_analizar"), message=texto, button=[t("boton_aceptar")])

    def _hornear(self):
        capa = self.capa()
        if capa:
            n = escena.hornear(capa)
            self.mensaje(t("horneada", capa=capa, matas=est.miles(n)))
            self.cargar_capa()

    def _deshornear(self):
        capa = self.capa()
        if capa:
            escena.deshornear(capa)
            self.mensaje(t("deshorneada", capa=capa))
            self.cargar_capa()

    # --- acabado ---------------------------------------------------------------------------------

    def _material(self):
        if self._cargando:
            return
        escena.fijar_material(self.material.currentData(), self.translucidez.value())

    def _tenir_suelo(self):
        capa = self.capa()
        suelo = escena.suelo(capa) if capa else None
        if not suelo:
            cmds.warning(t("pincel_sin_suelo"))
            return
        escena.tenir_suelo(suelo)
        self.mensaje(t("estado_suelo_tenido", suelo=suelo.split("|")[-1]))

    def _confirmar(self, clave, **valores):
        si, no = t("boton_si"), t("boton_no")
        return cmds.confirmDialog(title=t("ventana_titulo"), message=t(clave, **valores), button=[si, no],
                                  defaultButton=no, cancelButton=no, dismissString=no) == si

    def _sueltas(self):
        from grasseditor import convertir
        capa = self.capa()
        if not capa:
            return
        n = escena.informe(capa).get("matas", 0)
        if n > convertir.AVISO_SUELTAS and not self._confirmar("aviso_sueltas", matas=est.miles(n)):
            return
        grupo = convertir.instancias_sueltas(capa)
        self.mensaje(t("sueltas_hecho", grupo=grupo))

    def _unir(self):
        from grasseditor import convertir
        capa = self.capa()
        if not capa:
            return
        tris = escena.informe(capa).get("triangulos", 0)
        if tris > convertir.AVISO_TRIANGULOS and not self._confirmar("aviso_unir", triangulos=est.corto(tris)):
            return
        malla = convertir.unir_en_malla(capa)
        self.mensaje(t("unir_hecho", malla=malla))

    def _exportar_puntos(self):
        from grasseditor import convertir
        capa = self.capa()
        if not capa:
            return
        ruta = cmds.fileDialog2(fileMode=0, caption=t("boton_exportar_puntos"),
                                fileFilter="CSV (*.csv);;JSON (*.json)")
        if ruta:
            n = convertir.exportar_puntos(capa, ruta[0])
            self.mensaje(t("exportado_puntos", matas=est.miles(n), ruta=ruta[0]))

    def _exportar_fbx(self):
        from grasseditor import convertir
        capa = self.capa()
        if not capa:
            return
        ruta = cmds.fileDialog2(fileMode=0, caption=t("boton_exportar_fbx"), fileFilter="FBX (*.fbx)")
        if ruta:
            convertir.exportar_fbx(capa, ruta[0])
            self.mensaje(t("exportado_fbx", ruta=ruta[0]))

    def closeEvent(self, evento):
        pincel.soltar()
        global _ventana
        _ventana = None
        super(Ventana, self).closeEvent(evento)


def mostrar():
    global _ventana
    if _ventana is None:
        _ventana = Ventana()
    _ventana.refrescar()
    _ventana.show()
    _ventana.raise_()
    return _ventana


def refrescar_si_abierta():
    if _ventana is not None:
        _ventana.refrescar()
