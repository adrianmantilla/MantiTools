"""«Comprobar instalación»: un informe de todo el pack, para pegarlo en un correo al profesor."""

import os
import platform

import mantitools
from mantitools import herramientas as hr
from mantitools.i18n import t

# Funciones de comprobación propias de cada herramienta: (módulo, función, argumento para no abrir diálogo).
PROPIAS = {
    "arboles": ("arboles.interfaz_maya", "comprobar", {"mostrar": False}),
    "radial": ("radial.interfaz_maya", "comprobar", {"mostrar_dialogo": False}),
    "grasseditor": ("grasseditor.interfaz_maya", "comprobar", {"mostrar": False}),
}


def sueltas_activas(carpeta_modulos, mods=None):
    """[(id, ruta)] de .mod sueltos que siguen activos junto al pack. No depende de Maya."""
    mods = mods or {
        "trepadora": ("trepadora.mod",), "arboles": ("arboles.mod",), "radial": ("radial.mod",),
        "muro": ("muro.mod",), "materials": ("materials.mod", "muestrario.mod"),
        "grasseditor": ("grasseditor.mod", "pradera.mod"), "simplesave": ("simplesave.mod",),
    }
    encontradas = []
    for ident, nombres in mods.items():
        for nombre in nombres:
            # Maya lee cualquier archivo de «modules»: también los «.mod.mantitools» de instalaciones antiguas.
            for candidato in (nombre, nombre + ".mantitools"):
                ruta = os.path.join(carpeta_modulos, candidato)
                if os.path.isfile(ruta):
                    encontradas.append((ident, ruta))
    return encontradas


def informe():
    """(todo_bien, líneas)."""
    import importlib
    from maya import cmds
    from mantitools import carga
    bien = True
    version_maya = cmds.about(version=True)
    lineas = [t("informe_pack", version=mantitools.__version__),
              t("informe_maya", version=version_maya, sistema="{} {}".format(platform.system(), platform.release())),
              t("informe_carpeta", carpeta=carga.RAIZ), ""]
    if not any(v in version_maya for v in ("2026", "2027")):
        lineas.append("! " + t("informe_maya_aviso"))
        bien = False
    for ficha in hr.FICHAS:
        if not carga.activa(ficha.id):
            lineas.append("- {}: {}".format(ficha.nombre, t("informe_desactivada")))
            continue
        if not carga.disponible(ficha.id):
            lineas.append("! {}: {}".format(ficha.nombre, t("informe_no_incluida")))
            bien = False
            continue
        if not carga.cargada(ficha.id):
            lineas.append("! {}: {} {}".format(ficha.nombre, t("informe_no_cargada"), carga.fallo(ficha.id)))
            bien = False
            continue
        try:
            version = importlib.import_module(ficha.paquete).__version__
            origen = os.path.dirname(importlib.import_module(ficha.paquete).__file__)
        except Exception:
            version, origen = "?", ""
        dentro = os.path.normpath(origen).startswith(os.path.normpath(carga.carpeta_incluida(ficha.id)))
        if dentro:
            lineas.append("✓ {} {}".format(ficha.nombre, version))
        else:
            lineas.append("! {} {}: {}".format(ficha.nombre, version, t("informe_otra_copia", ruta=origen)))
            bien = False
        if ficha.id in PROPIAS:
            modulo, funcion, argumentos = PROPIAS[ficha.id]
            try:
                propio_bien, propias = getattr(importlib.import_module(modulo), funcion)(**argumentos)
                if not propio_bien:
                    lineas.append("! {}: {}".format(ficha.nombre, t("informe_propia_avisos")))
                for linea in propias:
                    if linea:
                        lineas.append("    " + linea)
                bien = bien and propio_bien
            except Exception as error:
                lineas.append("    " + t("informe_propia_error", error=error))
    carpeta_modulos = os.path.join(cmds.internalVar(userAppDir=True), "modules")
    sueltas = sueltas_activas(carpeta_modulos)
    if sueltas:
        lineas.append("")
        for ident, ruta in sueltas:
            lineas.append("! " + t("informe_suelta", herramienta=hr.ficha(ident).nombre, ruta=ruta))
        bien = False
    clase = carga.clase()
    lineas.append("")
    if clase.raiz:
        lineas.append(t("informe_clase", carpeta=clase.raiz))
        if clase.error:
            lineas.append("! " + clase.error)
            bien = False
    lineas.append("")
    lineas.append(t("comprobar_ok") if bien else t("comprobar_avisos"))
    for linea in lineas:
        print("MantiTools | " + linea)
    return bien, lineas


def mostrar():
    from mantitools import centro
    v = centro.mostrar("ayuda")
    if v is not None:
        v._comprobar()
    return v
