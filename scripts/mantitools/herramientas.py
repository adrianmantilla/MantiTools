"""Las fichas de las herramientas del pack. No depende de Maya.

Cada ficha dice cómo se llama la herramienta, su color, su plugin, cómo se crea
su menú y qué órdenes tiene. El menú, el estante, la ventana central y la
comprobación de la instalación se construyen a partir de estas fichas: para
añadir una herramienta nueva al pack basta con añadir su ficha (y copiarla en
``incluidas/`` con ``herramientas/sincronizar.py``).

Las órdenes son código Python corto que se ejecuta con ``acciones.ejecutar``; lo
que devuelve la llamada queda en ``_r``. La orden ``openpbr`` (convertir los
materiales de escenas viejas a OpenPBR) la usa además ``acciones.convertir_a_openpbr``.
"""

from collections import namedtuple

Accion = namedtuple("Accion", "clave codigo")


class Ficha(object):
    def __init__(self, ident, nombre, color, paquete, plugin, menu, crear_menu, acciones, principal,
                 repositorio):
        self.id = ident
        self.nombre = nombre
        self.color = color
        self.paquete = paquete
        self.plugin = plugin
        self.menu = menu
        self.crear_menu = crear_menu
        self.acciones = list(acciones)
        self.principal = principal
        self.repositorio = repositorio

    def accion(self, clave):
        for a in self.acciones:
            if a.clave == clave:
                return a
        raise KeyError("{}: no hay ninguna orden «{}»".format(self.id, clave))

    @property
    def secundarias(self):
        return [a for a in self.acciones if a.clave != self.principal]

    @property
    def icono(self):
        return "mantitools_{}.png".format(self.id)

    def texto(self, clave):
        """Clave de i18n de una orden: ``accion_<herramienta>_<orden>``."""
        return "accion_{}_{}".format(self.id, clave)

    def __repr__(self):
        return "Ficha({})".format(self.id)


def _ordenes(modulo, **llamadas):
    return [Accion(clave, "import {m} as _m\n_r = _m.{f}".format(m=modulo, f=llamada))
            for clave, llamada in llamadas.items()]


FICHAS = [
    Ficha("muro", "Muro", "#e8c04f", "muro", "muro_plugin", "MuroMenu",
          "muro.interfaz_maya:_crear_menu",
          _ordenes("muro.interfaz_maya", abrir="mostrar()", nuevo="nuevo()", importar="importar()",
                   capturar="capturar()", fantasma="fantasma()"),
          "abrir", "adrianmantilla/muro"),
    Ficha("arboles", "Árboles", "#b07a48", "arboles", "arboles_plugin", "ArbolesMenu",
          "arboles.interfaz_maya:crear_menu",
          _ordenes("arboles.interfaz_maya", editor="_editor()", biblioteca="_plantar()",
                   ejemplo="_arbol_ejemplo()", materiales="_crear_materiales()",
                   openpbr="convertir_a_openpbr()", comprobar="comprobar()"),
          "editor", "adrianmantilla/arboles"),
    Ficha("trepadora", "Trepadora", "#3fae8c", "trepadora", "trepadora_plugin", "trepadoraMenu",
          "trepadora.menu:crear",
          _ordenes("trepadora.menu", abrir="abrir()", escena_sencilla="escena_de_prueba('sencilla')",
                   escena_ruina="escena_de_prueba('ruina')", exportar="exportar_seleccion()",
                   exportar_ligeras="exportar_seleccion(ligeras=True)",
                   openpbr="convertir_a_openpbr()"),
          "abrir", "adrianmantilla/trepadora"),
    Ficha("grasseditor", "GrassEditor", "#a8cf5a", "grasseditor", "grasseditor_plugin", "GrassEditorMenu",
          "grasseditor.interfaz_maya:crear_menu",
          _ordenes("grasseditor.interfaz_maya", ventana="_ventana()", nueva_capa="_nueva_capa()",
                   nueva_pincel="_nueva_capa('pincel')", ejemplo="_ejemplo()", analizar="_analizar()"),
          "ventana", "adrianmantilla/grasseditor"),
    Ficha("materials", "Materials", "#e0685a", "materials", "materials_plugin", "MaterialsMenu",
          "materials.interfaz_maya:_crear_menu",
          _ordenes("materials.interfaz_maya", abrir="mostrar()", asignar="asignar()",
                   cuentagotas="cuentagotas()", enviar="enviar_a_painter()"),
          "abrir", "adrianmantilla/materials"),
    Ficha("lightmanager", "LightManager", "#f2913d", "lightmanager", "lightmanager_plugin", "LightManagerMenu",
          "lightmanager.interfaz_maya:_crear_menu",
          _ordenes("lightmanager.interfaz_maya", abrir="mostrar()", tres_puntos="tres_puntos()",
                   comprobar="comprobar()", quitar_solos="quitar_solos()"),
          "abrir", "adrianmantilla/lightmanager"),
    Ficha("renderdesk", "RenderDesk", "#6c8ebf", "renderdesk", "renderdesk_plugin", "RenderDeskMenu",
          "renderdesk.interfaz_maya:_crear_menu",
          _ordenes("renderdesk.interfaz_maya", abrir="mostrar()", modo_render="alternar_modo_render()",
                   probar="probar()", instantanea="instantanea()"),
          "abrir", "adrianmantilla/renderdesk"),
    Ficha("simplesave", "SimpleSave", "#e88fb8", "simplesave", "simplesave_plugin", "SimpleSaveMenu",
          "simplesave.interfaz_maya:_crear_menu",
          _ordenes("simplesave.interfaz_maya", guardar="guardar_version()", versiones="mostrar()",
                   recuperar="recuperar()", comparar="comparar()"),
          "guardar", "adrianmantilla/simplesave"),
    Ficha("radial", "Radial", "#a58bd6", "radial", "radial_plugin", "RadialMenu",
          "radial.interfaz_maya:crear_menu",
          _ordenes("radial.interfaz_maya", alternar="alternar()", configurar="abrir_configurador()",
                   ajustes="abrir_ajustes()", centrar="volver_a_centrar()"),
          "alternar", "adrianmantilla/radial"),
]

ORDEN = tuple(f.id for f in FICHAS)

# Grupos del estante, en el orden en que se trabaja una escena; entre grupo y grupo va un
# separador. El menú, las tarjetas y Ajustes siguen el mismo orden (el de FICHAS).
GRUPOS = (
    ("empezar", ("muro",)),
    ("construir", ("arboles", "trepadora", "grasseditor")),
    ("look", ("materials", "lightmanager", "renderdesk")),
    ("a_mano", ("simplesave", "radial")),
)


def grupo(ident):
    for nombre, ids in GRUPOS:
        if ident in ids:
            return nombre
    return None
ACENTO = "#4a9bd1"


def ficha(ident):
    for f in FICHAS:
        if f.id == ident:
            return f
    raise KeyError(ident)


def separar(ruta):
    """``"paquete.modulo:funcion"`` -> (``"paquete.modulo"``, ``"funcion"``)."""
    modulo, _, funcion = ruta.partition(":")
    return modulo, funcion
