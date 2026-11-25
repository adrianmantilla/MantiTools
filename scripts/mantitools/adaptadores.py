"""Las páginas de Ajustes: qué controles tiene cada herramienta y dónde lee y escribe cada uno.

Cada página es una fachada sobre los ajustes que ya tiene la herramienta (su
``ajustes.json`` o sus optionVar): no hay archivo de ajustes nuevo ni migración.
Al escribir se llama a la misma función que usa la herramienta, para que el
cambio se vea al momento (Radial cambia de forma, Árboles cambia sus texturas…).

Los controles se describen como datos (``Control``) y la ventana central los
dibuja; así las páginas se pueden probar sin Maya con un adaptador falso.
"""

import importlib
import os

from mantitools import clase as cl
from mantitools import herramientas as hr
from mantitools.i18n import t


class Control(object):
    """Un control de una página.

    ``tipo``: ``opciones`` (lista de (valor, texto)), ``casilla``, ``entero``, ``decimal``,
    ``carpeta``, ``archivo``, ``texto``, ``boton`` (``clave`` es la orden) o ``info`` (solo texto).
    """

    def __init__(self, tipo, clave, texto, opciones=None, minimo=None, maximo=None, sufijo="", ayuda=""):
        self.tipo = tipo
        self.clave = clave
        self.texto = texto
        self.opciones = opciones or []
        self.minimo = minimo
        self.maximo = maximo
        self.sufijo = sufijo
        self.ayuda = ayuda

    def __repr__(self):
        return "Control({}, {})".format(self.tipo, self.clave)


class Pagina(object):
    """Página de una herramienta. Las subclases dan ``secciones`` y saben leer y escribir."""

    ident = ""
    rehacer_menu = False  # tras escribir, rehacer el submenú (si tiene casillas o radios con ese valor)

    def __init__(self, clase=None):
        self.clase = clase or cl.Clase()

    @property
    def ficha(self):
        return hr.ficha(self.ident)

    def secciones(self):
        """[(título, [Control, ...]), ...]"""
        return []

    def leer(self, clave):
        raise NotImplementedError

    def escribir(self, clave, valor):
        raise NotImplementedError

    def boton(self, clave):
        pass

    def bloqueada(self, clave):
        return self.clase.bloqueada(self.ident, clave)

    def aplicar_fijadas(self):
        """Escribe lo que fija el profesor en ``mantitools_clase.json``. Devuelve las claves escritas."""
        escritas = []
        for clave, valor in self.clase.fijadas(self.ident).items():
            try:
                if self.leer(clave) != valor:
                    self.escribir(clave, valor)
                escritas.append(clave)
            except Exception:
                continue
        return escritas

    def _modulo(self, nombre):
        return importlib.import_module(nombre)


# --- Trepadora -----------------------------------------------------------------------------------

class PaginaTrepadora(Pagina):
    ident = "trepadora"

    def secciones(self):
        from trepadora import texturas
        return [
            (t("sec_texturas"), [
                Control("opciones", "resolucion", t("aj_resolucion"),
                        [(r, t("res_" + r)) for r in texturas.RESOLUCIONES], ayuda=t("aj_trepadora_res_ayuda")),
            ]),
            (t("sec_preajustes"), [
                Control("info", "carpeta_preajustes", t("aj_carpeta_preajustes")),
                Control("boton", "abrir_preajustes", t("boton_abrir_carpeta")),
            ]),
        ]

    def _carpeta(self):
        from maya import cmds
        from trepadora import ajustes
        return ajustes.carpeta_usuario(cmds.internalVar(userAppDir=True))

    def leer(self, clave):
        if clave == "resolucion":
            from trepadora import texturas
            return texturas.resolucion_actual()
        if clave == "carpeta_preajustes":
            return self._carpeta()
        raise KeyError(clave)

    def escribir(self, clave, valor):
        if clave == "resolucion":
            from trepadora import texturas
            texturas.recordar_resolucion(valor)
            ventana = getattr(self._modulo("trepadora.ui.ventana"), "_ventana", None)
            if ventana is not None and hasattr(ventana, "usar_resolucion"):
                ventana.usar_resolucion(valor)

    def boton(self, clave):
        if clave == "abrir_preajustes":
            carpeta = self._carpeta()
            os.makedirs(carpeta, exist_ok=True)
            abrir_en_explorador(carpeta)


# --- Árboles -------------------------------------------------------------------------------------

class PaginaArboles(Pagina):
    ident = "arboles"
    rehacer_menu = True

    def secciones(self):
        from arboles import texturas
        return [
            (t("sec_biblioteca"), [
                Control("carpeta", "carpeta_biblioteca", t("aj_carpeta_biblioteca"), ayuda=t("aj_biblioteca_ayuda")),
            ]),
            (t("sec_texturas"), [
                Control("opciones", "resolucion_texturas", t("aj_resolucion"),
                        [(r, t("res_" + r)) for r in texturas.RESOLUCIONES]),
                Control("opciones", "estilo_texturas", t("aj_estilo"),
                        [(e, t("estilo_" + e)) for e in texturas.ESTILOS]),
            ]),
        ]

    def _m(self):
        return self._modulo("arboles.interfaz_maya")

    def leer(self, clave):
        ajustes = self._m().cargar_ajustes()
        return getattr(ajustes, clave) or ""

    def escribir(self, clave, valor):
        m = self._m()
        if clave == "carpeta_biblioteca":
            if valor:
                m.cargar_ajustes().fijar_biblioteca(valor)
        elif clave == "resolucion_texturas":
            m._resolucion(valor)
        elif clave == "estilo_texturas":
            m._estilo(valor)


# --- Radial --------------------------------------------------------------------------------------

class PaginaRadial(Pagina):
    ident = "radial"
    rehacer_menu = True

    def secciones(self):
        return [
            (t("sec_menu"), [
                Control("opciones", "forma", t("aj_forma"), [("radial", t("forma_radial")),
                                                            ("pill", t("forma_pill_h")),
                                                            ("pill_vertical", t("forma_pill_v"))]),
                Control("casilla", "automatico", t("aj_automatico"), ayuda=t("aj_automatico_ayuda")),
                Control("casilla", "buscador", t("aj_buscador")),
                Control("casilla", "aprendizaje", t("aj_aprendizaje"), ayuda=t("aj_aprendizaje_ayuda")),
            ]),
            (t("sec_doble_tab"), [
                Control("entero", "ventana_ms", t("aj_ventana_ms"), minimo=150, maximo=400, sufijo=" ms",
                        ayuda=t("aj_ventana_ms_ayuda")),
            ]),
            (t("sec_mas"), [
                Control("boton", "ajustes_vivo", t("boton_radial_vivo"), ayuda=t("aj_radial_vivo_ayuda")),
                Control("boton", "configurar", t("boton_radial_configurar")),
            ]),
        ]

    def _m(self):
        return self._modulo("radial.interfaz_maya")

    def leer(self, clave):
        a = self._m().ajustes()
        if clave == "forma":
            return "pill_vertical" if a.forma == "pill" and a.pill_vertical else a.forma
        return getattr(a, clave)

    def escribir(self, clave, valor):
        m = self._m()
        if clave == "forma":
            m.cambiar_forma("pill" if valor.startswith("pill") else "radial", valor == "pill_vertical")
        elif clave == "ventana_ms":
            m._velocidad_cambiada(int(valor))
        elif clave == "buscador":
            m.cambiar_buscador(bool(valor))
        elif clave in ("automatico", "aprendizaje", "carpeta_clase"):
            m.cambiar_opcion(clave, valor)

    def bloqueada(self, clave):
        fijadas = getattr(self._m().ajustes(), "fijadas", {}) or {}
        if clave == "forma":
            return bool({"forma", "pill_vertical"} & set(fijadas))
        return clave in fijadas or super(PaginaRadial, self).bloqueada(clave)

    def boton(self, clave):
        m = self._m()
        if clave == "ajustes_vivo":
            m.abrir_ajustes()
        elif clave == "configurar":
            m.abrir_configurador()


# --- Muro ----------------------------------------------------------------------------------------

class PaginaMuro(Pagina):
    ident = "muro"
    rehacer_menu = True

    def secciones(self):
        from muro.dialogo_plano import UNIDADES
        return [
            (t("sec_tablero"), [
                Control("casilla", "abrir_con_escena", t("aj_abrir_con_escena"), ayuda=t("aj_abrir_con_escena_ayuda")),
                Control("entero", "opacidad_fantasma", t("aj_opacidad_fantasma"), minimo=5, maximo=100, sufijo=" %"),
            ]),
            (t("sec_plano"), [
                Control("opciones", "unidad_altura", t("aj_unidad"), [(u, u) for u in UNIDADES]),
                Control("decimal", "altura_plano", t("aj_altura_plano"), minimo=0.01, maximo=10000.0),
            ]),
        ]

    def _a(self):
        return self._modulo("muro.interfaz_maya").ajustes()

    def leer(self, clave):
        valor = self._a()[clave]
        if clave == "opacidad_fantasma":
            return int(round(float(valor) * 100))
        return valor

    def escribir(self, clave, valor):
        if clave == "opacidad_fantasma":
            valor = max(0.05, min(1.0, float(valor) / 100.0))
        self._a()[clave] = valor


# --- Materials -----------------------------------------------------------------------------------

class PaginaMaterials(Pagina):
    ident = "materials"

    def secciones(self):
        return [
            (t("sec_destino"), [
                Control("opciones", "destino", t("aj_destino"), [("render", t("destino_render")),
                                                                 ("juego", t("destino_juego"))]),
                Control("opciones", "motor_juego", t("aj_motor"), [("unreal", "Unreal Engine"), ("unity", "Unity"),
                                                                   ("gltf", "glTF / Godot / web")]),
                Control("opciones", "resolucion", t("aj_resolucion_painter"),
                        [(r, str(r)) for r in (512, 1024, 2048, 4096)]),
            ]),
            (t("sec_painter"), [
                Control("archivo", "ruta_painter", t("aj_ruta_painter"), ayuda=t("aj_ruta_painter_ayuda")),
                Control("casilla", "sincronizar", t("aj_sincronizar")),
                Control("casilla", "abrir_painter", t("aj_abrir_painter")),
            ]),
            (t("sec_complemento_painter"), [
                Control("carpeta", "carpeta_complemento", t("aj_carpeta_complemento"),
                        ayuda=t("aj_carpeta_complemento_ayuda")),
                Control("info", "estado_complemento", ""),
                Control("boton", "instalar_complemento", t("aj_instalar_complemento")),
            ]),
            (t("sec_nota"), [Control("info", "nota_materials", t("aj_materials_nota"))]),
        ]

    def _a(self):
        return self._modulo("materials.interfaz_maya").ajustes()

    # La carpeta del complemento de Painter es de MantiTools (la usa su instalador), no de Materials.
    def _carpeta_complemento(self):
        from mantitools import carga, painter
        return painter.carpeta(carga.ajustes()["carpeta_painter"])

    def leer(self, clave):
        from mantitools import painter
        if clave == "nota_materials":
            return ""
        if clave == "carpeta_complemento":
            return self._carpeta_complemento()
        if clave == "estado_complemento":
            carpeta = self._carpeta_complemento()
            return t("complemento_instalado" if painter.instalado(carpeta) else "complemento_no_instalado")
        return self._a()[clave]

    def escribir(self, clave, valor):
        if clave == "carpeta_complemento":
            from mantitools import carga, painter
            valor = os.path.normpath(valor) if valor else ""
            elegida = "" if not valor or valor == os.path.normpath(painter.carpeta_por_defecto()) else valor
            if elegida == carga.ajustes()["carpeta_painter"]:
                return
            anterior = self._carpeta_complemento()
            carga.ajustes()["carpeta_painter"] = elegida
            if painter.instalado(anterior):  # se mueve: que no queden dos copias
                painter.copiar(carga.RAIZ, self._carpeta_complemento())
                painter.quitar(anterior)
            return
        self._a()[clave] = valor

    def boton(self, clave):
        if clave == "instalar_complemento":
            from mantitools import carga, painter
            ruta = painter.copiar(carga.RAIZ, self._carpeta_complemento())
            return t("complemento_copiado", ruta=ruta)


# --- GrassEditor ---------------------------------------------------------------------------------

class PaginaGrassEditor(Pagina):
    ident = "grasseditor"

    def secciones(self):
        from grasseditor import tipos
        return [
            (t("sec_render"), [
                Control("casilla", "render_automatico", t("aj_render_automatico"),
                        ayuda=t("aj_render_automatico_ayuda")),
            ]),
            (t("sec_capa_nueva"), [
                Control("opciones", "tipo_inicial", t("aj_tipo_inicial"),
                        [(clave, self._nombre_tipo(clave)) for clave in tipos.SERIE]),
                Control("entero", "densidad_inicial", t("aj_densidad_inicial"), minimo=10, maximo=300, sufijo=" %"),
            ]),
        ]

    def _nombre_tipo(self, clave):
        try:
            from grasseditor.i18n import t as tg
            texto = tg("tipo_" + clave)
            return texto if texto != "tipo_" + clave else clave
        except Exception:
            return clave

    def _p(self):
        return self._modulo("grasseditor.preferencias")

    def leer(self, clave):
        return self._p().leer(clave)

    def escribir(self, clave, valor):
        self._p().escribir(clave, valor)


# --- SimpleSave ----------------------------------------------------------------------------------

class PaginaSimpleSave(Pagina):
    ident = "simplesave"

    def secciones(self):
        return [
            (t("sec_autoguardado"), [
                Control("casilla", "autoguardado", t("aj_autoguardado")),
                Control("entero", "minutos", t("aj_minutos"), minimo=1, maximo=120, sufijo=" min"),
                Control("entero", "copias", t("aj_copias"), minimo=1, maximo=50),
                Control("casilla", "pausa_reproduccion", t("aj_pausa_reproduccion")),
            ]),
            (t("sec_versiones"), [
                Control("texto", "plantilla", t("aj_plantilla"), ayuda=t("aj_plantilla_ayuda")),
                Control("opciones", "formato", t("aj_formato"), [("ma", ".ma"), ("mb", ".mb")]),
                Control("casilla", "miniaturas", t("aj_miniaturas")),
            ]),
            (t("sec_copia"), [
                Control("casilla", "copia_activada", t("aj_copia_activada")),
                Control("carpeta", "copia_carpeta", t("aj_copia_carpeta"), ayuda=t("aj_copia_carpeta_ayuda")),
            ]),
        ]

    def _a(self):
        return self._modulo("simplesave.interfaz_maya").ajustes()

    def leer(self, clave):
        return self._a()[clave]

    def escribir(self, clave, valor):
        self._a()[clave] = valor
        m = self._modulo("simplesave.interfaz_maya")
        refrescar = getattr(m, "_refrescar", None)
        if callable(refrescar):
            try:
                refrescar()
            except Exception:
                pass

    def bloqueada(self, clave):
        a = self._a()
        try:
            if a.bloqueado(clave):  # lo fija el simplesave.json del profesor en el proyecto
                return True
        except Exception:
            pass
        return super(PaginaSimpleSave, self).bloqueada(clave)


# --- LightManager --------------------------------------------------------------------------------

class PaginaLightManager(Pagina):
    ident = "lightmanager"

    def secciones(self):
        try:
            from lightmanager.sol import CIUDADES
            ciudades = [(c[0], c[1]) for c in CIUDADES]
        except ImportError:
            ciudades = [("madrid", "Madrid")]
        agrupar = [("papel", t("aj_lm_agrupar_papel")), ("zona", t("aj_lm_agrupar_zona")),
                   ("tipo", t("aj_lm_agrupar_tipo")), ("grupo", t("aj_lm_agrupar_grupo"))]
        return [
            (t("sec_lm_panel"), [
                Control("opciones", "modo", t("aj_lm_modo"),
                        [("auto", t("aj_lm_modo_auto")), ("estudio", t("aj_lm_modo_estudio")),
                         ("escena", t("aj_lm_modo_escena"))], ayuda=t("aj_lm_modo_ayuda")),
                Control("opciones", "agrupar_estudio", t("aj_lm_agrupar_estudio"), agrupar),
                Control("opciones", "agrupar_escena", t("aj_lm_agrupar_escena"), agrupar),
                Control("casilla", "ver_arnold", t("aj_lm_ver_arnold")),
            ]),
            (t("sec_lm_bibliotecas"), [
                Control("carpeta", "carpeta_hdri", t("aj_lm_carpeta_hdri"), ayuda=t("aj_lm_carpeta_vacia")),
                Control("carpeta", "carpeta_esquemas", t("aj_lm_carpeta_esquemas"), ayuda=t("aj_lm_carpeta_vacia")),
                Control("carpeta", "carpeta_ies", t("aj_lm_carpeta_ies")),
            ]),
            (t("sec_lm_sol"), [
                Control("opciones", "ciudad", t("aj_lm_ciudad"), ciudades),
                Control("decimal", "norte", t("aj_lm_norte"), minimo=-180, maximo=180, sufijo="°",
                        ayuda=t("aj_lm_norte_ayuda")),
                Control("casilla", "practicas_auto", t("aj_lm_practicas_auto")),
                Control("entero", "repetir_cantidad", t("aj_lm_repetir"), minimo=1, maximo=50),
            ]),
        ]

    def _m(self):
        return self._modulo("lightmanager.interfaz_maya")

    def leer(self, clave):
        return self._m().ajustes()[clave]

    def escribir(self, clave, valor):
        self._m().ajustes()[clave] = valor
        recargar = getattr(self._m(), "recargar_ajustes", None)
        if callable(recargar):
            try:
                recargar()
            except Exception:
                pass


# --- RenderDesk ----------------------------------------------------------------------------------

class PaginaRenderDesk(Pagina):
    """Las preferencias de RenderDesk son optionVar (``renderDesk_<clave>``); se leen por sus servicios."""
    ident = "renderdesk"
    DEFECTOS = {"nivel": "sencillo", "nucleos": "menos2"}

    def secciones(self):
        return [
            (t("sec_rd_panel"), [
                Control("opciones", "nivel", t("aj_rd_nivel"),
                        [("sencillo", t("aj_rd_nivel_sencillo")), ("detalle", t("aj_rd_nivel_detalle")),
                         ("experto", t("aj_rd_nivel_experto"))], ayuda=t("aj_rd_nivel_ayuda")),
            ]),
            (t("sec_rd_final"), [
                Control("opciones", "nucleos", t("aj_rd_nucleos"),
                        [("menos2", t("aj_rd_nucleos_menos2")), ("todos", t("aj_rd_nucleos_todos")),
                         ("mitad", t("aj_rd_nucleos_mitad"))], ayuda=t("aj_rd_nucleos_ayuda")),
                Control("info", "historial", t("aj_rd_historial")),
            ]),
        ]

    def _m(self):
        return self._modulo("renderdesk.interfaz_maya")

    def leer(self, clave):
        if clave == "historial":
            return t("aj_rd_historial_ruta")
        return self._m().servicios().preferencia(clave, self.DEFECTOS[clave])

    def escribir(self, clave, valor):
        m = self._m()
        m.servicios().guardar_preferencia(clave, valor)
        panel = m.ventana()
        if panel is None:
            return
        try:
            if clave == "nivel":
                panel.poner_nivel(valor, guardar=False)
            elif clave == "nucleos":
                combo = panel.pestana_salida.combo_nucleos
                combo.setCurrentIndex(max(0, combo.findData(valor)))
        except Exception:
            pass


PAGINAS = {p.ident: p for p in (PaginaTrepadora, PaginaArboles, PaginaRadial, PaginaMuro, PaginaMaterials,
                               PaginaLightManager, PaginaRenderDesk, PaginaGrassEditor, PaginaSimpleSave)}


def pagina(ident, clase=None):
    return PAGINAS[ident](clase)


# --- Carpeta de clase ----------------------------------------------------------------------------

def aplicar_clase():
    """Pasa a Radial y Materials su subcarpeta de clase y escribe lo que fija el profesor.

    Se llama al arrancar (con las herramientas ya importables) y al cambiar la carpeta.
    """
    from mantitools import carga
    clase = carga.releer_clase()
    raiz = carga.ajustes()["carpeta_clase"]
    if clase.error:
        _avisar(t("aviso_clase", error=clase.error))
    for ident in hr.ORDEN:
        if not carga.cargada(ident):
            continue
        sub = cl.subcarpeta(raiz, ident)
        try:
            if ident == "radial":
                m = importlib.import_module("radial.interfaz_maya")
                if (m.ajustes().carpeta_clase or "") != sub:
                    m.cambiar_opcion("carpeta_clase", sub)
            elif ident == "materials":
                m = importlib.import_module("materials.interfaz_maya")
                if (m.ajustes()["carpeta_clase"] or "") != sub:
                    m.ajustes()["carpeta_clase"] = sub
            pagina(ident, clase).aplicar_fijadas()
        except Exception as error:
            _avisar(t("aviso_clase_herramienta", herramienta=hr.ficha(ident).nombre, error=error))


def _avisar(texto):
    try:
        from maya import cmds
        cmds.warning(texto)
    except ImportError:
        print(texto)


def abrir_en_explorador(carpeta):
    from mantitools.qt import QtCore, QtGui
    QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(carpeta))
