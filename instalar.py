"""Instalador de MantiTools.

Arrastra este archivo desde el explorador de archivos hasta el visor de Maya.

- Escribe «mantitools.mod» en tu carpeta de módulos de Maya. Un solo archivo
  da a Maya MantiTools y las herramientas que trae (carpeta ``incluidas``).
- Si tenías alguna herramienta instalada por separado (``radial.mod``,
  ``materials.mod``…), la aparta sin borrarla: renombra su .mod a
  «.mod.mantitools» y quita su carga automática. Sus ajustes valen igual.
- Copia el complemento de Substance 3D Painter de Materials.
- Carga MantiTools, lo marca para que se cargue siempre y crea el estante.

Para desinstalar, arrastra otra vez este archivo y elige «Desinstalar»: quita
el .mod, el estante y el complemento de Painter, y devuelve las herramientas
sueltas que hubiera apartado.

No muevas la carpeta del pack después de instalar; si lo haces, vuelve a
arrastrar este archivo.
"""

import os
import shutil
import sys

PLUGIN = "mantitools_plugin"
NOMBRE_MOD = "mantitools.mod"
SUFIJO_APARTADO = ".mantitools"
# Nombres de .mod que dejaron los instaladores sueltos (incluidos los nombres antiguos).
MODS_SUELTOS = {
    "trepadora": ("trepadora.mod",),
    "arboles": ("arboles.mod",),
    "radial": ("radial.mod",),
    "muro": ("muro.mod",),
    "materials": ("materials.mod", "muestrario.mod"),
    "grasseditor": ("grasseditor.mod", "pradera.mod"),
    "simplesave": ("simplesave.mod",),
}
PLUGINS_ANTIGUOS = ("muestrario_plugin", "pradera_plugin")


def raiz():
    return os.path.dirname(os.path.abspath(__file__))


def version(carpeta, paquete):
    ruta = os.path.join(carpeta, "scripts", paquete, "__init__.py")
    try:
        with open(ruta, encoding="utf-8") as f:
            for linea in f:
                if linea.startswith("__version__"):
                    return linea.split("=")[1].strip().strip("\"'")
    except OSError:
        pass
    return "0.0.0"


def incluidas(base=None):
    """[(id, carpeta)] de las herramientas que trae el pack, en orden."""
    base = base or raiz()
    carpeta = os.path.join(base, "incluidas")
    orden = ("trepadora", "arboles", "radial", "muro", "materials", "grasseditor", "simplesave")
    return [(i, os.path.join(carpeta, i)) for i in orden
            if os.path.isdir(os.path.join(carpeta, i, "scripts", i))]


def ruta_para_mod(ruta, carpeta_modulos):
    """La ruta que se escribe en el .mod.

    Maya puede leer mal el .mod si la ruta lleva tildes o eñes (p. ej. un usuario
    «José» en Windows). En ese caso, si la ruta relativa a la carpeta del .mod no
    las lleva, se usa esa.
    """
    if ruta.isascii():
        return ruta.replace("\\", "/")
    try:
        relativa = os.path.relpath(ruta, carpeta_modulos)
    except ValueError:  # otra unidad en Windows
        return ruta.replace("\\", "/")
    return (relativa if relativa.isascii() else ruta).replace("\\", "/")


def contenido_mod(base, carpeta_modulos):
    """Un bloque por módulo: MantiTools y cada herramienta incluida, cada una con su carpeta."""
    bloques = ["+ MantiTools {} {}\nscripts: scripts\nplug-ins: plug-ins\nicons: icons\n".format(
        version(base, "mantitools"), ruta_para_mod(base, carpeta_modulos))]
    for ident, carpeta in incluidas(base):
        lineas = ["+ MantiTools_{} {} {}".format(ident, version(carpeta, ident), ruta_para_mod(carpeta, carpeta_modulos)),
                  "scripts: scripts", "plug-ins: plug-ins"]
        for iconos in ("icons", "iconos"):
            if os.path.isdir(os.path.join(carpeta, iconos)):
                lineas.append("icons: " + iconos)
                break
        bloques.append("\n".join(lineas) + "\n")
    return "\n".join(bloques)


def apartar_sueltas(carpeta_modulos):
    """Renombra los .mod de herramientas sueltas. Devuelve [(id, ruta_nueva)]."""
    apartadas = []
    for ident, nombres in MODS_SUELTOS.items():
        for nombre in nombres:
            ruta = os.path.join(carpeta_modulos, nombre)
            if os.path.isfile(ruta):
                nueva = ruta + SUFIJO_APARTADO
                if os.path.exists(nueva):
                    os.remove(nueva)
                os.rename(ruta, nueva)
                apartadas.append((ident, nueva))
    return apartadas


def devolver_sueltas(rutas):
    """Deshace ``apartar_sueltas``. Devuelve las rutas devueltas."""
    devueltas = []
    for ruta in rutas:
        if ruta.endswith(SUFIJO_APARTADO) and os.path.isfile(ruta):
            original = ruta[:-len(SUFIJO_APARTADO)]
            if not os.path.exists(original):
                os.rename(ruta, original)
                devueltas.append(original)
    return devueltas


def carpeta_plugins_painter():
    return os.path.join(os.path.expanduser("~"), "Documents", "Adobe", "Adobe Substance 3D Painter", "python",
                        "plugins")


def instalar_en_painter(base):
    """Copia el complemento de Painter de Materials. Devuelve la ruta o None."""
    origen = os.path.join(base, "incluidas", "materials", "painter", "materials_painter.py")
    if not os.path.isfile(origen):
        return None
    destino = carpeta_plugins_painter()
    try:
        os.makedirs(destino, exist_ok=True)
        shutil.copy2(origen, os.path.join(destino, "materials_painter.py"))
        return os.path.join(destino, "materials_painter.py")
    except OSError as error:
        print("MantiTools | no se pudo copiar el complemento de Painter: {}".format(error))
        return None


# --- En Maya ------------------------------------------------------------------------------------

def _carpeta_modulos():
    from maya import cmds
    return os.path.join(cmds.internalVar(userAppDir=True), "modules")


def _paquetes(base):
    return ["mantitools"] + [i for i, _ in incluidas(base)]


def _olvidar_codigo_viejo(base):
    """Para instalar sin reiniciar Maya: se descarga lo que hubiera y se lee el código nuevo."""
    from maya import cmds
    for nombre in (PLUGIN,) + tuple(p + "_plugin" for p in _paquetes(base)[1:]) + PLUGINS_ANTIGUOS:
        try:
            if cmds.pluginInfo(nombre, query=True, loaded=True):
                cmds.flushUndo()
                cmds.unloadPlugin(nombre, force=True)
            if cmds.pluginInfo(nombre, query=True, registered=True):
                cmds.pluginInfo(nombre, edit=True, autoload=False)
        except RuntimeError:
            pass
    paquetes = _paquetes(base)
    carpetas = [os.path.join(base, "scripts")] + [os.path.join(c, "scripts") for _, c in incluidas(base)]
    normales = {os.path.normpath(c) for c in carpetas}
    # Fuera de sys.path las copias sueltas de las mismas herramientas.
    sys.path[:] = [p for p in sys.path if os.path.normpath(p) in normales
                   or not any(os.path.isfile(os.path.join(p, q, "__init__.py")) for q in paquetes)]
    for carpeta in reversed(carpetas):
        if carpeta not in sys.path:
            sys.path.insert(0, carpeta)
    for nombre in list(sys.modules):
        if nombre.split(".")[0] in paquetes:
            del sys.modules[nombre]


def _iconos_en_sesion(base):
    """Maya lee las carpetas de iconos del .mod al arrancar: para que el estante se vea ya, se añaden ahora."""
    carpetas = [os.path.join(base, "icons")]
    for _, carpeta in incluidas(base):
        for nombre in ("icons", "iconos"):
            if os.path.isdir(os.path.join(carpeta, nombre)):
                carpetas.append(os.path.join(carpeta, nombre))
                break
    sufijo = "/%B" if sys.platform.startswith("linux") else ""
    actuales = os.environ.get("XBMLANGPATH", "").split(os.pathsep)
    nuevas = [c + sufijo for c in carpetas if c + sufijo not in actuales]
    os.environ["XBMLANGPATH"] = os.pathsep.join(nuevas + [a for a in actuales if a])


def instalar():
    from maya import cmds
    base = raiz()
    if not os.path.isdir(os.path.join(base, "scripts", "mantitools")):
        raise RuntimeError("No encuentro MantiTools junto a instalar.py (busqué en {}).".format(base))
    print("MantiTools | instalando desde " + base)
    carpeta_modulos = _carpeta_modulos()
    os.makedirs(carpeta_modulos, exist_ok=True)
    ruta_mod = os.path.join(carpeta_modulos, NOMBRE_MOD)
    with open(ruta_mod, "w", encoding="utf-8") as f:
        f.write(contenido_mod(base, carpeta_modulos))
    print("MantiTools | módulo escrito en " + ruta_mod)
    apartadas = apartar_sueltas(carpeta_modulos)
    for ident, ruta in apartadas:
        print("MantiTools | herramienta suelta apartada: " + ruta)
    ruta_painter = instalar_en_painter(base)
    if ruta_painter:
        print("MantiTools | complemento de Painter copiado en " + ruta_painter)

    _olvidar_codigo_viejo(base)
    _iconos_en_sesion(base)
    from mantitools import carga, estante
    from mantitools.i18n import t
    if apartadas:
        previas = carga.ajustes()["sueltas_desactivadas"]
        carga.ajustes()["sueltas_desactivadas"] = sorted(set(previas) | {r for _, r in apartadas})
    cmds.loadPlugin(os.path.join(base, "plug-ins", PLUGIN + ".py"))
    cmds.pluginInfo(PLUGIN, edit=True, autoload=True)
    if cmds.about(batch=True):
        carga.iniciar()
        return ruta_mod
    # El plugin termina de arrancar con evalDeferred: el estante y la ventana van después.
    cmds.evalDeferred(lambda: _despues_de_instalar(apartadas, ruta_painter), lowestPriority=True)
    try:
        cmds.savePrefs(general=True, plugins=True)
    except RuntimeError:
        pass
    return ruta_mod


def _despues_de_instalar(apartadas, ruta_painter):
    from maya import cmds
    from mantitools import centro, estante, herramientas
    from mantitools.i18n import t
    estante.crear(forzar=True, seleccionar=True)
    texto = t("instalado_texto")
    if apartadas:
        nombres = sorted({herramientas.ficha(i).nombre for i, _ in apartadas})
        texto += "\n\n" + t("instalado_sueltas", herramientas=", ".join(nombres))
    if ruta_painter:
        texto += "\n\n" + t("instalado_painter")
    cmds.confirmDialog(title="MantiTools", message=texto, button=[t("boton_aceptar")])
    centro.mostrar("herramientas")


def desinstalar():
    from maya import cmds
    base = raiz()
    _olvidar_codigo_viejo(base)
    from mantitools import carga, estante
    devueltas = devolver_sueltas(carga.ajustes()["sueltas_desactivadas"])
    carga.ajustes()["sueltas_desactivadas"] = []
    try:
        if cmds.pluginInfo(PLUGIN, query=True, registered=True):
            cmds.pluginInfo(PLUGIN, edit=True, autoload=False)
    except RuntimeError:
        pass
    estante.quitar()
    ruta_mod = os.path.join(_carpeta_modulos(), NOMBRE_MOD)
    if os.path.exists(ruta_mod):
        os.remove(ruta_mod)
    painter = os.path.join(carpeta_plugins_painter(), "materials_painter.py")
    if os.path.isfile(painter) and not devueltas:
        os.remove(painter)
    try:
        cmds.savePrefs(general=True, plugins=True)
    except RuntimeError:
        pass
    return ruta_mod, devueltas


def onMayaDroppedPythonFile(*_):
    """Maya llama a esta función al soltar el archivo en el visor."""
    from maya import cmds
    try:
        base = raiz()
        sys.path.insert(0, os.path.join(base, "scripts"))
        from mantitools.i18n import t
        ya = os.path.isfile(os.path.join(_carpeta_modulos(), NOMBRE_MOD))
        eleccion = t("boton_instalar")
        if ya:
            eleccion = cmds.confirmDialog(title="MantiTools", message=t("reinstalar_pregunta"),
                                          button=[t("boton_reinstalar"), t("boton_desinstalar"), t("boton_cancelar")],
                                          defaultButton=t("boton_reinstalar"), cancelButton=t("boton_cancelar"),
                                          dismissString=t("boton_cancelar"))
        if eleccion == t("boton_desinstalar"):
            ruta, devueltas = desinstalar()
            texto = t("desinstalado_texto", mod=ruta)
            if devueltas:
                texto += "\n\n" + t("desinstalado_sueltas")
            cmds.confirmDialog(title="MantiTools", message=texto, button=[t("boton_aceptar")])
        elif eleccion != t("boton_cancelar"):
            instalar()
    except Exception as error:
        cmds.confirmDialog(title="MantiTools", message="No se pudo instalar MantiTools: {}".format(error),
                           button=["OK"])
        raise
    finally:
        sys.modules.pop(__name__, None)
