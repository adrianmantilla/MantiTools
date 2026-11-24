"""Menú de Árboles en la barra de Maya, bienvenida y comprobación de la instalación."""

import os
import platform

from maya import cmds

import arboles
from arboles import ajustes as aj
from arboles.i18n import t

MENU = "ArbolesMenu"


def carpeta_preferencias():
    return os.path.join(cmds.internalVar(userAppDir=True), "arboles")


def cargar_ajustes():
    ajustes = aj.Ajustes(carpeta_preferencias())
    from arboles import materiales_propios
    materiales_propios.registrar(ajustes.carpeta_biblioteca)  # sus materiales propios
    return ajustes


# --- Biblioteca -------------------------------------------------------------

def _elegir_carpeta(inicio):
    elegida = cmds.fileDialog2(fileMode=3, caption=t("elegir_carpeta_titulo"),
                               startingDirectory=inicio, okCaption=t("boton_aceptar"))
    return elegida[0] if elegida else None


def _fijar(ajustes, ruta):
    try:
        ruta = ajustes.fijar_biblioteca(ruta)
    except OSError as error:
        cmds.warning(t("carpeta_error", ruta=ruta, error=error))
        return None
    print(t("carpeta_lista", ruta=ruta))
    return ruta


def bienvenida(forzar=False):
    """Pregunta la carpeta de la biblioteca la primera vez (o siempre si ``forzar``)."""
    ajustes = cargar_ajustes()
    if not forzar and not ajustes.primer_uso():
        return ajustes.carpeta_biblioteca
    propuesta = ajustes.carpeta_biblioteca or aj.biblioteca_por_defecto()
    usar, elegir = t("boton_usar"), t("boton_elegir")
    respuesta = cmds.confirmDialog(
        title=t("bienvenida_titulo"), message=t("bienvenida_texto", ruta=propuesta),
        button=[usar, elegir], defaultButton=usar, cancelButton=usar, dismissString=usar)
    if respuesta == elegir:
        elegida = _elegir_carpeta(os.path.dirname(propuesta))
        if elegida:
            propuesta = elegida
        elif not ajustes.primer_uso():
            return ajustes.carpeta_biblioteca
    return _fijar(ajustes, propuesta)


def carpeta_biblioteca():
    """Carpeta de la biblioteca; si aún no hay, da la bienvenida."""
    return cargar_ajustes().carpeta_biblioteca or bienvenida()


# --- Comprobar --------------------------------------------------------------

def comprobar(mostrar=True):
    """Devuelve (todo_bien, líneas) y, si ``mostrar``, las enseña en un diálogo."""
    lineas, bien = [t("comprobar_version", version=arboles.__version__)], True

    version = cmds.about(version=True)
    sistema = "{} {}".format(platform.system(), platform.release())
    if any(v in version for v in ("2026", "2027")):
        lineas.append(t("comprobar_maya", version=version, sistema=sistema))
    else:
        lineas.append(t("comprobar_maya_aviso", version=version))
        bien = False

    try:
        if not cmds.pluginInfo("mtoa", query=True, loaded=True):
            cmds.loadPlugin("mtoa", quiet=True)
        lineas.append(t("comprobar_arnold_ok", version=cmds.pluginInfo("mtoa", query=True, version=True)))
    except RuntimeError:
        lineas.append(t("comprobar_arnold_aviso"))
        bien = False

    ruta = cargar_ajustes().carpeta_biblioteca
    if not ruta:
        lineas.append(t("comprobar_carpeta_sin"))
        bien = False
    elif aj.se_puede_escribir(ruta):
        lineas.append(t("comprobar_carpeta_ok", ruta=ruta))
    else:
        lineas.append(t("comprobar_carpeta_aviso", ruta=ruta))
        bien = False

    lineas.append("")
    lineas.append(t("comprobar_ok") if bien else t("comprobar_avisos"))
    for linea in lineas:
        print("Árboles | " + linea)
    if mostrar:
        cmds.confirmDialog(title=t("comprobar_titulo"), message="\n".join(lineas),
                           button=[t("boton_aceptar")])
    return bien, lineas


# --- Menú -------------------------------------------------------------------

def _proximamente(clave_funcion):
    cmds.confirmDialog(title=t("menu_titulo"),
                       message=t("proximamente", funcion=t(clave_funcion)),
                       button=[t("boton_aceptar")])


def _crear_materiales():
    from arboles import materiales
    creados = materiales.crear_todos()
    print(t("materiales_listos", nombres=", ".join(sorted(creados))))


def convertir_a_openpbr():
    """Convierte a OpenPBR los materiales de Árboles de escenas viejas y dice cuántos."""
    from arboles import materiales, openpbr
    if not openpbr.disponible():
        cmds.warning(t("openpbr_no_disponible"))
        return []
    hechos = materiales.convertir_a_openpbr()
    print(t("openpbr_convertidos", n=len(hechos)))
    return hechos


def _arbol_ejemplo():
    from arboles import construir_maya, ejemplos
    construir_maya.preparar()
    grupo = construir_maya.crear(ejemplos.copa_redonda())
    cmds.select(grupo)
    print(t("ejemplo_creado", grupo=grupo, triangulos=construir_maya.triangulos(grupo)))
    return grupo


def _generar(nivel):
    from arboles import construir_maya
    grupos = construir_maya.grupos_seleccionados()
    if not grupos:
        cmds.warning(t("generar_sin_seleccion"))
        return
    for grupo in grupos:
        antes = construir_maya.triangulos(grupo)
        construir_maya.generar(grupo, nivel)
        print(t("generado", grupo=grupo, nivel=t("nivel_" + nivel), antes=antes,
                despues=construir_maya.triangulos(grupo)))
    cmds.select(grupos)


def _cuadros(activo):
    from arboles import construir_maya
    construir_maya.textura_cuadros(bool(activo))
    if activo:
        print(t("cuadros_activos"))


def _resolucion(resolucion):
    from arboles import materiales
    ajustes = cargar_ajustes()
    ajustes.fijar_resolucion_texturas(resolucion)
    cambiadas = materiales.cambiar_texturas(resolucion, ajustes.estilo_texturas)
    print(t("resolucion_cambiada", resolucion=t("resolucion_" + resolucion), texturas=cambiadas))


def _estilo(estilo):
    from arboles import materiales
    ajustes = cargar_ajustes()
    ajustes.fijar_estilo_texturas(estilo)
    cambiadas = materiales.cambiar_texturas(ajustes.resolucion_texturas, estilo)
    print(t("estilo_cambiado", estilo=t("estilo_" + estilo), texturas=cambiadas))


def _editor():
    from arboles import editor_ui
    carpeta_biblioteca()  # la primera vez pregunta dónde guardar
    return editor_ui.mostrar()


def _plantar():
    from arboles import plantar_ui
    carpeta_biblioteca()
    return plantar_ui.mostrar()


def _acerca():
    cmds.confirmDialog(title=t("menu_acerca"), message=t("acerca_texto", version=arboles.__version__),
                       button=[t("boton_aceptar")])


def crear_menu():
    from arboles import pack
    pack.crear_menu(MENU, t("menu_titulo"))
    cmds.menuItem(label=t("menu_editor"), command=lambda *_: _editor())
    cmds.menuItem(label=t("menu_biblioteca"), command=lambda *_: _plantar())
    cmds.menuItem(label=t("menu_modulos"), subMenu=True, tearOff=True)
    cmds.menuItem(label=t("menu_ejemplo"), command=lambda *_: _arbol_ejemplo())
    cmds.menuItem(divider=True)
    for nivel in ("alto", "medio", "bajo"):
        cmds.menuItem(label=t("menu_generar", nivel=t("nivel_" + nivel)),
                      command=lambda *_, n=nivel: _generar(n))
    cmds.menuItem(label=t("menu_denso"), command=lambda *_: _generar("denso"))
    cmds.menuItem(divider=True)
    cmds.menuItem(label=t("menu_cuadros"), checkBox=False,
                  command=lambda activo, *_: _cuadros(activo))
    cmds.setParent("..", menu=True)
    cmds.menuItem(divider=True)
    cmds.menuItem(label=t("menu_resolucion"), subMenu=True)
    from arboles.texturas import RESOLUCIONES
    actual = cargar_ajustes().resolucion_texturas
    cmds.radioMenuItemCollection()
    for resolucion in RESOLUCIONES:
        cmds.menuItem(label=t("resolucion_" + resolucion), radioButton=(resolucion == actual),
                      command=lambda *_, r=resolucion: _resolucion(r))
    cmds.setParent("..", menu=True)
    cmds.menuItem(label=t("menu_estilo"), subMenu=True)
    from arboles.texturas import ESTILOS
    actual = cargar_ajustes().estilo_texturas
    cmds.radioMenuItemCollection()
    for estilo in ESTILOS:
        cmds.menuItem(label=t("estilo_" + estilo), radioButton=(estilo == actual),
                      command=lambda *_, e=estilo: _estilo(e))
    cmds.setParent("..", menu=True)
    cmds.menuItem(label=t("menu_carpeta"), command=lambda *_: bienvenida(forzar=True))
    cmds.menuItem(label=t("menu_materiales"), command=lambda *_: _crear_materiales())
    cmds.menuItem(label=t("menu_openpbr"), annotation=t("ayuda_menu_openpbr"),
                  command=lambda *_: convertir_a_openpbr())
    cmds.menuItem(divider=True)
    cmds.menuItem(label=t("menu_comprobar"), command=lambda *_: comprobar())
    cmds.menuItem(label=t("menu_acerca"), command=lambda *_: _acerca())
    return MENU


def quitar_menu():
    from arboles import pack
    pack.quitar_menu(MENU)


def iniciar():
    """Lo llama el plugin al cargarse."""
    if cmds.about(batch=True):
        return
    crear_menu()
