"""Menú de GrassEditor en la barra de Maya y comprobación de la instalación."""

import platform

from maya import cmds

import grasseditor
from grasseditor import pack
from grasseditor.i18n import t

MENU = "GrassEditorMenu"


def comprobar(mostrar=True):
    """Devuelve (todo_bien, líneas) y, si ``mostrar``, las enseña en un diálogo."""
    lineas, bien = [t("comprobar_version", version=grasseditor.__version__)], True
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
    nodo = "grassEditorCapa" in (cmds.allNodeTypes() or [])
    lineas.append(t("comprobar_nodo_ok") if nodo else t("comprobar_nodo_aviso"))
    bien = bien and nodo
    lineas.append("")
    lineas.append(t("comprobar_ok") if bien else t("comprobar_avisos"))
    for linea in lineas:
        print("GrassEditor | " + linea)
    if mostrar:
        cmds.confirmDialog(title=t("comprobar_titulo"), message="\n".join(lineas), button=[t("boton_aceptar")])
    return bien, lineas


def _ventana():
    from grasseditor import ventana
    return ventana.mostrar()


def _nueva_capa(zona="objeto"):
    from grasseditor import escena
    suelo, caras = escena.suelo_de_seleccion()
    if not suelo:
        cmds.warning(t("error_sin_malla"))
        return None
    capa = escena.crear_capa(suelo, caras, zona=zona)
    print("GrassEditor | " + t("capa_creada", capa=capa, suelo=suelo.split("|")[-1]))
    from grasseditor import ventana
    ventana.refrescar_si_abierta()
    return capa


def _ejemplo():
    from grasseditor import ejemplos
    ejemplos.jardin_con_loma()
    from grasseditor import ventana
    ventana.mostrar()


def _vista_render(activo):
    from grasseditor import escena
    escena.fijar_render(bool(activo))
    print("GrassEditor | " + t("vista_render_si" if activo else "vista_render_no"))


def _analizar():
    from grasseditor import ventana
    ventana.mostrar()._analizar()


def _acerca():
    cmds.confirmDialog(title=t("menu_acerca"), message=t("acerca_texto", version=grasseditor.__version__),
                       button=[t("boton_aceptar")])


def crear_menu():
    pack.crear_menu(MENU, t("menu_titulo"))
    cmds.menuItem(label=t("menu_ventana"), command=lambda *_: _ventana())
    cmds.menuItem(divider=True)
    cmds.menuItem(label=t("menu_nueva_capa"), command=lambda *_: _nueva_capa())
    cmds.menuItem(label=t("menu_nueva_pincel"), command=lambda *_: _nueva_capa("pincel"))
    cmds.menuItem(label=t("menu_ejemplo"), command=lambda *_: _ejemplo())
    cmds.menuItem(divider=True)
    cmds.menuItem(label=t("menu_vista_render"), checkBox=False, command=lambda activo, *_: _vista_render(activo))
    cmds.menuItem(label=t("menu_analizar"), command=lambda *_: _analizar())
    cmds.menuItem(divider=True)
    cmds.menuItem(label=t("menu_comprobar"), command=lambda *_: comprobar())
    cmds.menuItem(label=t("menu_acerca"), command=lambda *_: _acerca())
    return MENU


def quitar_menu():
    pack.quitar_menu(MENU)


def iniciar():
    """Lo llama el plugin al cargarse."""
    if cmds.about(batch=True):
        return
    crear_menu()
