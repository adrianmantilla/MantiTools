"""La ventana central de MantiTools: Herramientas, Ajustes y Ayuda.

Sigue la línea de Materials: cabecera, tarjetas con miniatura y franja de color,
pestañas y pasos numerados. Va en un panel acoplable de Maya, como Materials y Muro.
"""

import os

import mantitools
from mantitools import adaptadores as ad
from mantitools import estilo
from mantitools import herramientas as hr
from mantitools import iconos
from mantitools.i18n import t
from mantitools.qt import QtCore, QtGui, QtWidgets, destruir, sigue_vivo

Qt = QtCore.Qt
CONTROL = "MantiToolsWorkspaceControl"
NOMBRE = "MantiToolsVentana"
PESTANAS = ("herramientas", "ajustes", "ayuda")

_estado = {"ventana": None, "pestana": "herramientas"}


class Servicios(object):
    """Lo que la ventana necesita de Maya y del pack. Las pruebas sin Maya pasan uno falso."""

    def activa(self, ident):
        from mantitools import carga
        return carga.activa(ident)

    def desactivada_por_profesor(self, ident):
        from mantitools import carga
        return ident in carga.clase().desactivadas

    def cargada(self, ident):
        from mantitools import carga
        return carga.cargada(ident)

    def fallo(self, ident):
        from mantitools import carga
        return carga.fallo(ident)

    def version(self, ident):
        import importlib
        try:
            return importlib.import_module(hr.ficha(ident).paquete).__version__
        except Exception:
            return ""

    def ejecutar(self, ident, clave):
        from mantitools import acciones
        acciones.ejecutar(ident, clave)

    def cambiar_activa(self, ident, valor):
        from mantitools import carga
        carga.cambiar_activa(ident, valor)

    def ajustes(self):
        from mantitools import carga
        return carga.ajustes()

    def clase(self):
        from mantitools import carga
        return carga.clase()

    def pagina(self, ident):
        return ad.pagina(ident, self.clase())

    def tras_escribir(self, pagina):
        if pagina.rehacer_menu and self.cargada(pagina.ident):
            from maya import cmds
            from mantitools import menu
            cmds.evalDeferred(lambda: menu.poner_submenu(hr.ficha(pagina.ident)), lowestPriority=True)

    def cambiar_idioma(self, codigo):
        from maya import cmds
        from mantitools import carga, estante, menu
        carga.ajustes()["idioma"] = codigo
        carga.aplicar_idioma(codigo)
        cmds.evalDeferred(lambda: (menu.construir(), estante.crear(forzar=True), reabrir()), lowestPriority=True)

    def cambiar_carpeta_clase(self, ruta):
        from mantitools import carga
        carga.ajustes()["carpeta_clase"] = ruta or ""
        ad.aplicar_clase()

    def recrear_estante(self):
        from mantitools import estante
        estante.crear(forzar=True, seleccionar=True)

    def informe(self):
        from mantitools import comprobar
        return comprobar.informe()

    def guia(self, ident):
        from mantitools import carga
        if ident == "mantitools":
            return os.path.join(carga.RAIZ, "GUIA_ALUMNOS.md")
        return os.path.join(carga.carpeta_incluida(ident), "GUIA_ALUMNOS.md")


# --- Piezas ----------------------------------------------------------------------------------

def _icono(ident, lado, color=iconos.TRAZO, fondo=None, grosor=iconos.GROSOR_TARJETA):
    mapa = iconos.pixmap(ident, lado, color=color, fondo=fondo, grosor=grosor)
    etiqueta = QtWidgets.QLabel()
    etiqueta.setAlignment(Qt.AlignCenter)
    if mapa is not None:
        etiqueta.setPixmap(mapa)
    return etiqueta


class TarjetaHerramienta(QtWidgets.QFrame):
    """Miniatura con el icono, franja de color, nombre, versión, descripción y botones."""

    def __init__(self, ficha, servicios, al_mensaje, padre=None):
        super(TarjetaHerramienta, self).__init__(padre)
        self.ficha, self.servicios, self.al_mensaje = ficha, servicios, al_mensaje
        estilo.rol(self, "tarjeta")
        self.setMinimumWidth(190)
        capa = QtWidgets.QVBoxLayout(self)
        capa.setContentsMargins(0, 0, 0, 0)
        capa.setSpacing(0)
        mini = QtWidgets.QFrame()
        mini.setFixedHeight(74)
        mini.setStyleSheet("background: {}; border-top-left-radius: 8px; border-top-right-radius: 8px;"
                           .format(iconos.FONDO_TARJETA))
        fila_mini = QtWidgets.QHBoxLayout(mini)
        fila_mini.addWidget(_icono(ficha.id, 40, color="#e6e6e6"))
        capa.addWidget(mini)
        franja = QtWidgets.QFrame()
        estilo.rol(franja, "franja")
        franja.setStyleSheet("background: {};".format(iconos.tono_marca(ficha.color)))
        capa.addWidget(franja)
        info = QtWidgets.QVBoxLayout()
        info.setContentsMargins(10, 8, 10, 10)
        info.setSpacing(5)
        cabeza = QtWidgets.QHBoxLayout()
        nombre = estilo.etiqueta(ficha.nombre)
        nombre.setStyleSheet("font-weight: 600;")
        cabeza.addWidget(nombre)
        cabeza.addStretch(1)
        self.version = estilo.etiqueta("", "tenue")
        cabeza.addWidget(self.version)
        info.addLayout(cabeza)
        self.descripcion = estilo.etiqueta(t("desc_" + ficha.id), "tenue", ajuste=True)
        self.descripcion.setMinimumHeight(44)
        self.descripcion.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        info.addWidget(self.descripcion)
        self.estado = estilo.etiqueta("", "aviso", ajuste=True)
        info.addWidget(self.estado)
        botones = QtWidgets.QHBoxLayout()
        botones.setSpacing(4)
        self.boton_abrir = QtWidgets.QPushButton(t(ficha.texto(ficha.principal)))
        estilo.primario(self.boton_abrir)
        self.boton_abrir.setCursor(Qt.PointingHandCursor)
        self.boton_abrir.clicked.connect(lambda: self._ejecutar(ficha.principal))
        botones.addWidget(self.boton_abrir, 1)
        self.boton_mas = QtWidgets.QToolButton()
        self.boton_mas.setText("···")
        self.boton_mas.setToolTip(t("tarjeta_mas"))
        self.boton_mas.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        menu = QtWidgets.QMenu(self.boton_mas)
        for accion in ficha.secundarias:
            menu.addAction(t(ficha.texto(accion.clave)), lambda c=accion.clave: self._ejecutar(c))
        self.boton_mas.setMenu(menu)
        botones.addWidget(self.boton_mas)
        self.boton_activar = QtWidgets.QPushButton(t("boton_activar"))
        self.boton_activar.clicked.connect(lambda: self.servicios.cambiar_activa(ficha.id, True))
        botones.addWidget(self.boton_activar, 1)
        info.addLayout(botones)
        capa.addLayout(info)
        self.actualizar()

    def actualizar(self):
        s, ident = self.servicios, self.ficha.id
        activa = s.activa(ident)
        version = s.version(ident)
        self.version.setText(version)
        fallo = s.fallo(ident) if activa else ""
        if not activa:
            texto = t("tarjeta_profesor") if s.desactivada_por_profesor(ident) else t("tarjeta_desactivada")
        elif fallo:
            texto = t("tarjeta_fallo")
        else:
            texto = ""
        self.estado.setText(texto)
        self.estado.setVisible(bool(texto))
        self.estado.setToolTip(fallo)
        self.boton_abrir.setVisible(activa)
        self.boton_mas.setVisible(activa and bool(self.ficha.secundarias))
        self.boton_activar.setVisible(not activa and not s.desactivada_por_profesor(ident))

    def _ejecutar(self, clave):
        try:
            self.servicios.ejecutar(self.ficha.id, clave)
        except Exception as error:
            self.al_mensaje(t("aviso_orden", herramienta=self.ficha.nombre, error=error), True)


class Deslizador(QtWidgets.QWidget):
    """Deslizador con su número al lado, como en Materials."""

    cambiado = QtCore.Signal(int)

    def __init__(self, minimo, maximo, sufijo="", padre=None):
        super(Deslizador, self).__init__(padre)
        capa = QtWidgets.QHBoxLayout(self)
        capa.setContentsMargins(0, 0, 0, 0)
        self.barra = QtWidgets.QSlider(Qt.Horizontal)
        self.barra.setRange(minimo, maximo)
        self.numero = QtWidgets.QSpinBox()
        self.numero.setRange(minimo, maximo)
        self.numero.setSuffix(sufijo)
        self.numero.setFixedWidth(78)
        capa.addWidget(self.barra, 1)
        capa.addWidget(self.numero)
        self.barra.valueChanged.connect(self.numero.setValue)
        self.numero.valueChanged.connect(self.barra.setValue)
        self.barra.sliderReleased.connect(lambda: self.cambiado.emit(self.barra.value()))
        self.numero.editingFinished.connect(lambda: self.cambiado.emit(self.numero.value()))

    def fijar(self, valor):
        for w in (self.barra, self.numero):
            w.blockSignals(True)
            w.setValue(int(valor))
            w.blockSignals(False)

    def valor(self):
        return self.numero.value()


class PaginaAjustes(QtWidgets.QScrollArea):
    """Dibuja una ``adaptadores.Pagina``: una tarjeta por sección y un formulario dentro."""

    def __init__(self, pagina, servicios, al_mensaje, padre=None):
        super(PaginaAjustes, self).__init__(padre)
        self.pagina, self.servicios, self.al_mensaje = pagina, servicios, al_mensaje
        self.setWidgetResizable(True)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.controles = {}
        contenido = QtWidgets.QWidget()
        self.capa = QtWidgets.QVBoxLayout(contenido)
        self.capa.setContentsMargins(0, 0, 6, 0)
        self.capa.setSpacing(8)
        ficha = pagina.ficha
        cab, fila = estilo.cabecera(ficha.nombre, None, servicios.version(ficha.id))
        fila.insertWidget(0, _icono(ficha.id, 20, fondo=iconos.FONDO, grosor=iconos.GROSOR_ESTANTE))
        cab.setStyleSheet("border-radius: 8px;")
        self.capa.addWidget(cab)
        for titulo, controles in pagina.secciones():
            marco, capa = estilo.tarjeta()
            capa.addWidget(estilo.etiqueta(titulo, "seccion"))
            formulario = estilo.formulario()
            for control in controles:
                self._fila(formulario, control)
            capa.addLayout(formulario)
            self.capa.addWidget(marco)
        self.capa.addStretch(1)
        self.setWidget(contenido)
        self.recargar()

    def _fila(self, formulario, c):
        bloqueada = self.pagina.bloqueada(c.clave) if c.tipo not in ("boton", "info") else False
        if c.tipo == "opciones":
            w = QtWidgets.QComboBox()
            for valor, texto in c.opciones:
                w.addItem(texto, valor)
            w.currentIndexChanged.connect(lambda _, w=w, c=c: self._escribir(c, w.currentData()))
        elif c.tipo == "casilla":
            w = QtWidgets.QCheckBox(c.texto)
            w.toggled.connect(lambda v, c=c: self._escribir(c, bool(v)))
        elif c.tipo == "entero":
            w = Deslizador(c.minimo, c.maximo, c.sufijo)
            w.cambiado.connect(lambda v, c=c: self._escribir(c, int(v)))
        elif c.tipo == "decimal":
            w = QtWidgets.QDoubleSpinBox()
            w.setRange(c.minimo, c.maximo)
            w.setDecimals(2)
            w.editingFinished.connect(lambda w=w, c=c: self._escribir(c, float(w.value())))
        elif c.tipo in ("carpeta", "archivo", "texto"):
            w = QtWidgets.QWidget()
            fila = QtWidgets.QHBoxLayout(w)
            fila.setContentsMargins(0, 0, 0, 0)
            campo = QtWidgets.QLineEdit()
            campo.editingFinished.connect(lambda campo=campo, c=c: self._escribir(c, campo.text().strip()))
            fila.addWidget(campo, 1)
            if c.tipo != "texto":
                boton = QtWidgets.QToolButton()
                boton.setText("…")
                boton.clicked.connect(lambda _=False, campo=campo, c=c: self._elegir(c, campo))
                fila.addWidget(boton)
            w.campo = campo
        elif c.tipo == "boton":
            w = QtWidgets.QPushButton(c.texto)
            w.clicked.connect(lambda _=False, c=c: self._boton(c))
            fila = QtWidgets.QHBoxLayout()
            fila.addWidget(w)
            fila.addStretch(1)
            formulario.addRow(fila)
            self._ayuda(formulario, c)
            return
        else:  # info
            w = estilo.etiqueta("", ajuste=True)
            w.setTextInteractionFlags(Qt.TextSelectableByMouse)
        w.setEnabled(not bloqueada)
        if bloqueada:
            w.setToolTip(t("bloqueada_ayuda"))
        self.controles[c.clave] = (c, w)
        if c.tipo == "casilla":
            formulario.addRow("", w)
        elif c.tipo == "info":  # a todo lo ancho, para que el texto se parta en líneas
            formulario.addRow(w)
        else:
            etiqueta = c.texto + ("  \U0001F512" if bloqueada else "")
            formulario.addRow(etiqueta, w)
        self._ayuda(formulario, c)

    def _ayuda(self, formulario, c):
        if c.ayuda:
            nota = estilo.etiqueta(c.ayuda, "tenue", ajuste=True)
            formulario.addRow("", nota)

    def recargar(self):
        for clave, (c, w) in self.controles.items():
            try:
                valor = self.pagina.leer(clave)
            except Exception:
                continue
            w.blockSignals(True)
            try:
                if c.tipo == "opciones":
                    i = w.findData(valor)
                    if i < 0:
                        i = w.findData(str(valor))
                    w.setCurrentIndex(max(0, i))
                elif c.tipo == "casilla":
                    w.setChecked(bool(valor))
                elif c.tipo == "entero":
                    w.fijar(valor)
                elif c.tipo == "decimal":
                    w.setValue(float(valor))
                elif c.tipo in ("carpeta", "archivo", "texto"):
                    w.campo.setText(str(valor or ""))
                elif c.tipo == "info":
                    w.setText(str(valor or c.texto))
            finally:
                w.blockSignals(False)

    def _escribir(self, c, valor):
        try:
            self.pagina.escribir(c.clave, valor)
            self.servicios.tras_escribir(self.pagina)
            self.al_mensaje(t("guardado", herramienta=self.pagina.ficha.nombre), False)
        except Exception as error:
            self.al_mensaje(t("aviso_guardar", error=error), True)
            self.recargar()

    def _elegir(self, c, campo):
        if c.tipo == "carpeta":
            ruta = QtWidgets.QFileDialog.getExistingDirectory(self, c.texto, campo.text())
        else:
            ruta, _ = QtWidgets.QFileDialog.getOpenFileName(self, c.texto, campo.text())
        if ruta:
            campo.setText(ruta)
            self._escribir(c, ruta)

    def _boton(self, c):
        try:
            mensaje = self.pagina.boton(c.clave)
            if mensaje:
                self.al_mensaje(mensaje, False)
                self.recargar()
        except Exception as error:
            self.al_mensaje(t("aviso_orden", herramienta=self.pagina.ficha.nombre, error=error), True)


class PaginaGeneral(QtWidgets.QScrollArea):
    """Idioma, herramientas activas, carpeta de clase y estante."""

    def __init__(self, servicios, al_mensaje, padre=None):
        super(PaginaGeneral, self).__init__(padre)
        self.servicios, self.al_mensaje = servicios, al_mensaje
        self.setWidgetResizable(True)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        contenido = QtWidgets.QWidget()
        capa = QtWidgets.QVBoxLayout(contenido)
        capa.setContentsMargins(0, 0, 6, 0)
        capa.setSpacing(8)
        cab, fila_cab = estilo.cabecera(t("pagina_general"), None, mantitools.__version__)
        fila_cab.insertWidget(0, _icono("centro", 20, fondo=iconos.FONDO, grosor=iconos.GROSOR_ESTANTE))
        cab.setStyleSheet("border-radius: 8px;")
        capa.addWidget(cab)

        marco, c = estilo.tarjeta()
        c.addWidget(estilo.etiqueta(t("sec_idioma"), "seccion"))
        f = estilo.formulario()
        self.idioma = QtWidgets.QComboBox()
        for codigo, nombre in (("es", "Español"), ("en", "English")):
            self.idioma.addItem(nombre, codigo)
        self.idioma.setCurrentIndex(max(0, self.idioma.findData(servicios.ajustes().idioma)))
        self.idioma.currentIndexChanged.connect(lambda _: self._idioma())
        f.addRow(t("aj_idioma"), self.idioma)
        f.addRow("", estilo.etiqueta(t("aj_idioma_ayuda"), "tenue", ajuste=True))
        c.addLayout(f)
        capa.addWidget(marco)

        marco, c = estilo.tarjeta()
        c.addWidget(estilo.etiqueta(t("sec_activas"), "seccion"))
        rejilla = QtWidgets.QGridLayout()
        rejilla.setHorizontalSpacing(16)
        self.casillas = {}
        for i, ficha in enumerate(hr.FICHAS):
            fila = QtWidgets.QHBoxLayout()
            fila.setSpacing(6)
            fila.addWidget(_icono(ficha.id, 16, fondo=iconos.FONDO, grosor=iconos.GROSOR_ESTANTE))
            casilla = QtWidgets.QCheckBox(ficha.nombre)
            casilla.toggled.connect(lambda v, i=ficha.id: self._activa(i, v))
            fila.addWidget(casilla)
            fila.addStretch(1)
            rejilla.addLayout(fila, i // 2, i % 2)
            self.casillas[ficha.id] = casilla
        c.addLayout(rejilla)
        c.addWidget(estilo.etiqueta(t("aj_activas_ayuda"), "tenue", ajuste=True))
        capa.addWidget(marco)

        marco, c = estilo.tarjeta()
        c.addWidget(estilo.etiqueta(t("sec_clase"), "seccion"))
        fila = QtWidgets.QHBoxLayout()
        self.carpeta = QtWidgets.QLineEdit()
        self.carpeta.setPlaceholderText(t("aj_clase_vacia"))
        self.carpeta.editingFinished.connect(lambda: self._carpeta(self.carpeta.text().strip()))
        fila.addWidget(self.carpeta, 1)
        elegir = QtWidgets.QToolButton()
        elegir.setText("…")
        elegir.clicked.connect(self._elegir_carpeta)
        fila.addWidget(elegir)
        c.addLayout(fila)
        self.resumen_clase = estilo.etiqueta("", "tenue", ajuste=True)
        c.addWidget(self.resumen_clase)
        capa.addWidget(marco)

        marco, c = estilo.tarjeta()
        c.addWidget(estilo.etiqueta(t("sec_estante"), "seccion"))
        fila = QtWidgets.QHBoxLayout()
        boton = QtWidgets.QPushButton(t("menu_recrear_estante"))
        boton.clicked.connect(self._estante)
        fila.addWidget(boton)
        fila.addStretch(1)
        c.addLayout(fila)
        c.addWidget(estilo.etiqueta(t("aj_estante_ayuda"), "tenue", ajuste=True))
        capa.addWidget(marco)
        capa.addStretch(1)
        self.setWidget(contenido)
        self.recargar()

    def recargar(self):
        s = self.servicios
        for ident, casilla in self.casillas.items():
            casilla.blockSignals(True)
            casilla.setChecked(s.activa(ident))
            profesor = s.desactivada_por_profesor(ident)
            casilla.setEnabled(not profesor)
            casilla.setToolTip(t("tarjeta_profesor") if profesor else "")
            casilla.blockSignals(False)
        self.carpeta.setText(s.ajustes()["carpeta_clase"])
        clase = s.clase()
        if not clase.raiz:
            texto = t("clase_sin")
        elif not clase.existe:
            texto = t("clase_no_existe")
        elif clase.error:
            texto = clase.error
        else:
            fijadas = sum(len(clase.fijadas(i)) for i in hr.ORDEN)
            texto = t("clase_resumen", fijadas=fijadas, desactivadas=len(clase.desactivadas))
        self.resumen_clase.setText(texto)

    def _idioma(self):
        self.servicios.cambiar_idioma(self.idioma.currentData())
        self.al_mensaje(t("idioma_cambiado"), False)

    def _activa(self, ident, valor):
        self.servicios.cambiar_activa(ident, valor)
        self.al_mensaje(t("activa_si" if valor else "activa_no", herramienta=hr.ficha(ident).nombre), False)

    def _elegir_carpeta(self):
        ruta = QtWidgets.QFileDialog.getExistingDirectory(self, t("sec_clase"), self.carpeta.text())
        if ruta:
            self.carpeta.setText(ruta)
            self._carpeta(ruta)

    def _carpeta(self, ruta):
        if ruta == self.servicios.ajustes()["carpeta_clase"]:
            return
        try:
            self.servicios.cambiar_carpeta_clase(ruta)
            self.al_mensaje(t("clase_cambiada"), False)
        except Exception as error:
            self.al_mensaje(t("aviso_guardar", error=error), True)
        self.recargar()

    def _estante(self):
        self.servicios.recrear_estante()
        self.al_mensaje(t("estante_recreado"), False)


class VentanaCentro(QtWidgets.QWidget):
    def __init__(self, servicios=None, padre=None):
        super(VentanaCentro, self).__init__(padre)
        self.servicios = servicios or Servicios()
        estilo.aplicar(self, NOMBRE)
        self.setMinimumWidth(460)
        principal = QtWidgets.QVBoxLayout(self)
        principal.setContentsMargins(0, 0, 0, 6)
        principal.setSpacing(0)
        principal.addWidget(self._cabecera())
        self.pestanas = QtWidgets.QTabWidget()
        self.pestanas.setDocumentMode(True)
        self.pestanas.addTab(self._pestana_herramientas(), t("tab_herramientas"))
        self.pestanas.addTab(self._pestana_ajustes(), t("tab_ajustes"))
        self.pestanas.addTab(self._pestana_ayuda(), t("tab_ayuda"))
        principal.addWidget(self.pestanas, 1)
        self.barra_estado = estilo.etiqueta(t("listo"), "tenue", ajuste=True)
        self.barra_estado.setContentsMargins(10, 4, 10, 0)
        principal.addWidget(self.barra_estado)

    # --- Cabecera
    def _cabecera(self):
        marco = QtWidgets.QFrame()
        estilo.rol(marco, "cabecera")
        fila = QtWidgets.QHBoxLayout(marco)
        fila.setContentsMargins(10, 8, 10, 8)
        fila.setSpacing(8)
        fila.addWidget(_icono("centro", 22, fondo=iconos.FONDO, grosor=iconos.GROSOR_ESTANTE))
        fila.addWidget(estilo.etiqueta("MantiTools", "titulo"))
        self.cuenta = estilo.etiqueta("", "tenue")
        fila.addWidget(self.cuenta)
        fila.addStretch(1)
        fila.addWidget(estilo.etiqueta("v" + mantitools.__version__, "tenue"))
        return marco

    def _contar(self):
        n = sum(1 for f in hr.FICHAS if self.servicios.activa(f.id))
        self.cuenta.setText(t("activas_cuenta", n=n))

    # --- Herramientas
    def _pestana_herramientas(self):
        zona = QtWidgets.QScrollArea()
        zona.setWidgetResizable(True)
        zona.setFrameShape(QtWidgets.QFrame.NoFrame)
        contenido = QtWidgets.QWidget()
        self.rejilla = QtWidgets.QGridLayout(contenido)
        self.rejilla.setContentsMargins(10, 10, 10, 10)
        self.rejilla.setSpacing(8)
        self.tarjetas = [TarjetaHerramienta(f, self.servicios, self.mensaje) for f in hr.FICHAS]
        self._colocar_tarjetas(3)
        zona.setWidget(contenido)
        self._contar()
        return zona

    def _colocar_tarjetas(self, columnas):
        for i, tarjeta in enumerate(self.tarjetas):
            self.rejilla.addWidget(tarjeta, i // columnas, i % columnas)
        self.rejilla.setRowStretch(len(self.tarjetas) // columnas + 1, 1)
        self._columnas = columnas

    def resizeEvent(self, evento):
        super(VentanaCentro, self).resizeEvent(evento)
        columnas = max(1, min(4, (self.width() - 20) // 220))
        if getattr(self, "_columnas", None) != columnas and hasattr(self, "tarjetas"):
            for tarjeta in self.tarjetas:
                self.rejilla.removeWidget(tarjeta)
            self._colocar_tarjetas(columnas)

    # --- Ajustes
    def _pestana_ajustes(self):
        panel = QtWidgets.QWidget()
        fila = QtWidgets.QHBoxLayout(panel)
        fila.setContentsMargins(10, 10, 10, 10)
        fila.setSpacing(10)
        self.lista = QtWidgets.QListWidget()
        self.lista.setFixedWidth(180)
        self.lista.setIconSize(QtCore.QSize(16, 16))
        self.pilas = QtWidgets.QStackedWidget()
        self.paginas = {}
        self._anadir_pagina("general", t("pagina_general"), "centro",
                            lambda: PaginaGeneral(self.servicios, self.mensaje))
        for ficha in hr.FICHAS:
            self._anadir_pagina(ficha.id, ficha.nombre, ficha.id, lambda f=ficha: self._pagina_de(f))
        self.lista.currentRowChanged.connect(self._mostrar_pagina)
        fila.addWidget(self.lista)
        fila.addWidget(self.pilas, 1)
        self.lista.setCurrentRow(0)
        return panel

    def _anadir_pagina(self, ident, texto, icono, fabrica):
        mapa = iconos.pixmap(icono, 32, fondo=iconos.FONDO, grosor=iconos.GROSOR_ESTANTE,
                             marca=hr.ACENTO if icono == "centro" else iconos.tono_marca(hr.ficha(icono).color))
        elemento = QtWidgets.QListWidgetItem(QtGui.QIcon(mapa) if mapa is not None else QtGui.QIcon(), texto)
        elemento.setData(Qt.UserRole, ident)
        self.lista.addItem(elemento)
        hueco = QtWidgets.QWidget()
        QtWidgets.QVBoxLayout(hueco).setContentsMargins(0, 0, 0, 0)
        self.pilas.addWidget(hueco)
        self.paginas[ident] = {"fabrica": fabrica, "hueco": hueco, "widget": None}

    def _pagina_de(self, ficha):
        if not self.servicios.activa(ficha.id) or not self.servicios.cargada(ficha.id):
            marco, capa = estilo.tarjeta(14)
            cab, _ = estilo.cabecera(ficha.nombre)
            capa.addWidget(cab)
            texto = t("pagina_inactiva") if not self.servicios.activa(ficha.id) else t("pagina_sin_cargar")
            capa.addWidget(estilo.etiqueta(texto, "tenue", ajuste=True))
            capa.addStretch(1)
            return marco
        return PaginaAjustes(self.servicios.pagina(ficha.id), self.servicios, self.mensaje)

    def _mostrar_pagina(self, fila):
        elemento = self.lista.item(fila)
        if elemento is None:
            return
        datos = self.paginas[elemento.data(Qt.UserRole)]
        if datos["widget"] is None:
            try:
                datos["widget"] = datos["fabrica"]()
            except Exception as error:
                datos["widget"] = estilo.etiqueta(t("aviso_pagina", error=error), "aviso", ajuste=True)
            datos["hueco"].layout().addWidget(datos["widget"])
        elif hasattr(datos["widget"], "recargar"):
            datos["widget"].recargar()
        self.pilas.setCurrentWidget(datos["hueco"])

    def ir_a_ajustes(self, ident="general"):
        for i in range(self.lista.count()):
            if self.lista.item(i).data(Qt.UserRole) == ident:
                self.lista.setCurrentRow(i)
        self.pestanas.setCurrentIndex(1)

    # --- Ayuda
    def _pestana_ayuda(self):
        zona = QtWidgets.QScrollArea()
        zona.setWidgetResizable(True)
        zona.setFrameShape(QtWidgets.QFrame.NoFrame)
        contenido = QtWidgets.QWidget()
        capa = QtWidgets.QVBoxLayout(contenido)
        capa.setContentsMargins(10, 10, 10, 10)
        capa.setSpacing(8)
        marco, c = estilo.tarjeta(12, 8)
        c.addWidget(estilo.etiqueta(t("ayuda_primeros"), "seccion"))
        for n in (1, 2, 3):
            c.addWidget(estilo.paso(n, t("ayuda_paso_{}".format(n))))
        capa.addWidget(marco)

        marco, c = estilo.tarjeta(12, 6)
        c.addWidget(estilo.etiqueta(t("ayuda_guias"), "seccion"))
        rejilla = QtWidgets.QGridLayout()
        rejilla.setHorizontalSpacing(10)
        filas = [("mantitools", "MantiTools", "centro")] + [(f.id, f.nombre, f.id) for f in hr.FICHAS]
        for i, (ident, nombre, icono) in enumerate(filas):
            rejilla.addWidget(_icono(icono, 16, fondo=iconos.FONDO, grosor=iconos.GROSOR_ESTANTE), i, 0)
            rejilla.addWidget(estilo.etiqueta(nombre), i, 1)
            version = mantitools.__version__ if ident == "mantitools" else self.servicios.version(ident)
            rejilla.addWidget(estilo.etiqueta(version or "—", "tenue"), i, 2)
            boton = QtWidgets.QPushButton(t("boton_guia"))
            boton.clicked.connect(lambda _=False, i=ident: self._guia(i))
            rejilla.addWidget(boton, i, 3)
        rejilla.setColumnStretch(1, 1)
        c.addLayout(rejilla)
        capa.addWidget(marco)

        marco, c = estilo.tarjeta(12, 6)
        c.addWidget(estilo.etiqueta(t("ayuda_problemas"), "seccion"))
        c.addWidget(estilo.etiqueta(t("ayuda_problemas_texto"), "tenue", ajuste=True))
        fila = QtWidgets.QHBoxLayout()
        comprobar = QtWidgets.QPushButton(t("menu_comprobar"))
        estilo.primario(comprobar)
        comprobar.clicked.connect(self._comprobar)
        copiar = QtWidgets.QPushButton(t("boton_copiar_informe"))
        copiar.clicked.connect(self._copiar)
        fila.addWidget(comprobar)
        fila.addWidget(copiar)
        fila.addStretch(1)
        c.addLayout(fila)
        self.informe = QtWidgets.QPlainTextEdit()
        self.informe.setReadOnly(True)
        self.informe.setMinimumHeight(140)
        self.informe.setVisible(False)
        c.addWidget(self.informe)
        capa.addWidget(marco)
        capa.addStretch(1)
        zona.setWidget(contenido)
        return zona

    def _guia(self, ident):
        ruta = self.servicios.guia(ident)
        if ruta and os.path.isfile(ruta):
            ad.abrir_en_explorador(ruta)
        else:
            self.mensaje(t("guia_no_hay"), True)

    def _comprobar(self):
        bien, lineas = self.servicios.informe()
        self.informe.setPlainText("\n".join(lineas))
        self.informe.setVisible(True)
        self.mensaje(t("comprobar_ok") if bien else t("comprobar_avisos"), not bien)

    def _copiar(self):
        if not self.informe.isVisible():
            self._comprobar()
        QtWidgets.QApplication.clipboard().setText(self.informe.toPlainText())
        self.mensaje(t("informe_copiado"), False)

    # --- Comunes
    def ir_a(self, pestana):
        if pestana in PESTANAS:
            self.pestanas.setCurrentIndex(PESTANAS.index(pestana))

    def mensaje(self, texto, error=False):
        self.barra_estado.setText(texto)
        estilo.rol(self.barra_estado, "aviso" if error else "tenue")

    def actualizar(self):
        self._contar()
        for tarjeta in self.tarjetas:
            tarjeta.actualizar()
        for datos in self.paginas.values():
            if hasattr(datos["widget"], "recargar"):
                datos["widget"].recargar()


# --- Panel acoplable de Maya ------------------------------------------------------------------

def ventana():
    v = _estado["ventana"]
    return v if sigue_vivo(v) else None


def restaurar():
    """Maya lo llama al crear (o recuperar) el panel: mete la ventana dentro."""
    from maya import OpenMayaUI as omui
    from mantitools.qt import shiboken
    puntero = omui.MQtUtil.getCurrentParent()
    padre = shiboken.wrapInstance(int(puntero), QtWidgets.QWidget)
    v = ventana()
    if v is None:
        v = VentanaCentro()
        _estado["ventana"] = v
    padre.layout().addWidget(v)
    v.ir_a(_estado["pestana"])


def mostrar(pestana="herramientas"):
    from maya import cmds
    _estado["pestana"] = pestana
    if cmds.workspaceControl(CONTROL, exists=True):
        cmds.workspaceControl(CONTROL, edit=True, restore=True, visible=True)
        v = ventana()
        if v is None:
            cmds.deleteUI(CONTROL)
        else:
            v.actualizar()
            v.ir_a(pestana)
            return v
    cmds.workspaceControl(CONTROL, label="MantiTools", retain=False, floating=True, initialWidth=760,
                          initialHeight=600, minimumWidth=460,
                          uiScript="import mantitools.centro as c\nc.restaurar()",
                          closeCommand="import mantitools.centro as c\nc.al_cerrar()")
    v = ventana()
    if v is not None:
        v.ir_a(pestana)
    return v


def al_cerrar():
    _estado["ventana"] = None


def cerrar():
    try:
        from maya import cmds
    except ImportError:
        return
    v = ventana()
    if cmds.workspaceControl(CONTROL, exists=True):
        cmds.deleteUI(CONTROL)
    if v is not None:
        destruir(v)
    _estado["ventana"] = None


def actualizar():
    v = ventana()
    if v is not None:
        v.actualizar()


def reabrir():
    """Cierra y vuelve a abrir la ventana (tras cambiar el idioma), en la misma pestaña."""
    v = ventana()
    if v is None:
        return
    pestana = PESTANAS[v.pestanas.currentIndex()]
    cerrar()
    mostrar(pestana)
