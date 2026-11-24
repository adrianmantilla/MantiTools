"""Diálogo «Material propio»: el alumno elige sus imágenes de corteza y de hoja (Qt)."""

import os

try:
    from PySide6 import QtWidgets
except ImportError:  # Maya anterior a 2025
    from PySide2 import QtWidgets

from arboles import estilo, materiales_propios
from arboles.i18n import t

# (parte, canal) en el orden del diálogo
CAMPOS = (("corteza", "color"), ("corteza", "normal"), ("corteza", "rugosidad"),
          ("hoja", "color"), ("hoja", "normal"))
_FILTRO = "Imágenes (*.png *.jpg *.jpeg *.tif *.tiff *.exr)"


class DialogoMaterialPropio(QtWidgets.QDialog):
    def __init__(self, padre, carpeta_biblioteca):
        super(DialogoMaterialPropio, self).__init__(padre)
        self.carpeta_biblioteca = carpeta_biblioteca
        self.juego = None
        self.setWindowTitle(t("material_propio_titulo"))
        estilo.aplicar(self, "ArbolesMaterialPropio")
        capa = QtWidgets.QVBoxLayout(self)
        explicacion = QtWidgets.QLabel(t("material_propio_explicacion"))
        explicacion.setWordWrap(True)
        capa.addWidget(explicacion)
        formulario = estilo.formulario()
        self.nombre = QtWidgets.QLineEdit()
        formulario.addRow(t("material_propio_nombre_campo"), self.nombre)
        self.rutas = {}
        for parte, canal in CAMPOS:
            fila = QtWidgets.QHBoxLayout()
            campo = QtWidgets.QLineEdit()
            campo.setPlaceholderText(t("material_propio_opcional") if canal != "color" else "")
            boton = QtWidgets.QPushButton(t("material_propio_elegir"))
            boton.clicked.connect(lambda *_, c=campo: self._elegir(c))
            fila.addWidget(campo, 1)
            fila.addWidget(boton)
            formulario.addRow(t("material_propio_{}_{}".format(parte, canal)), fila)
            self.rutas[(parte, canal)] = campo
        capa.addLayout(formulario)
        botones = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        estilo.primario(botones.button(QtWidgets.QDialogButtonBox.Ok)).setText(t("material_propio_crear"))
        botones.button(QtWidgets.QDialogButtonBox.Cancel).setText(t("boton_cancelar"))
        botones.accepted.connect(self._crear)
        botones.rejected.connect(self.reject)
        capa.addWidget(botones)
        self.resize(560, self.sizeHint().height())

    def _elegir(self, campo):
        inicio = os.path.dirname(campo.text()) if campo.text() else os.path.expanduser("~")
        ruta, _ = QtWidgets.QFileDialog.getOpenFileName(self, t("material_propio_elegir"), inicio, _FILTRO)
        if ruta:
            campo.setText(ruta)
            if not self.nombre.text().strip():
                self.nombre.setText(os.path.splitext(os.path.basename(ruta))[0])

    def _aviso(self, texto):
        QtWidgets.QMessageBox.warning(self, t("material_propio_titulo"), texto)

    def _crear(self):
        nombre = self.nombre.text().strip()
        imagenes = {clave: campo.text().strip() for clave, campo in self.rutas.items() if campo.text().strip()}
        if not nombre:
            return self._aviso(t("material_propio_falta_nombre"))
        if not any(canal == "color" for (_, canal) in imagenes):
            return self._aviso(t("material_propio_falta_color"))
        for ruta in imagenes.values():
            if not os.path.isfile(ruta):
                return self._aviso(t("material_propio_no_existe", ruta=ruta))
        try:
            self.juego = materiales_propios.crear(self.carpeta_biblioteca, nombre, imagenes)
        except (ValueError, IOError, OSError) as error:
            return self._aviso(t("material_propio_error", error=error))
        materiales_propios.registrar(self.carpeta_biblioteca)
        self.accept()


def pedir(padre, carpeta_biblioteca):
    """Abre el diálogo; devuelve el juego creado (``propio_…``) o None si se cancela."""
    if not carpeta_biblioteca:
        return None
    dialogo = DialogoMaterialPropio(padre, carpeta_biblioteca)
    return dialogo.juego if dialogo.exec_() else None
