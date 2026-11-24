"""Instalador de MantiTools.

Arrastra este archivo desde el explorador de archivos hasta el visor de Maya.

- Escribe «mantitools.mod» en tu carpeta de módulos de Maya. Un solo archivo
  da a Maya MantiTools y las herramientas que trae (carpeta ``incluidas``).
- Si tenías alguna herramienta instalada por separado (``radial.mod``,
  ``materials.mod``…), la aparta sin borrarla: mueve su .mod a la carpeta
  «mantitools_apartadas», junto a «modules», y quita su carga automática. Sus ajustes valen igual.
- Copia el complemento de Substance 3D Painter de Materials a su carpeta de
  complementos (se puede cambiar en Ajustes → Materials).
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
    orden = ("trepadora", "arboles", "radial", "muro", "materials", "lightmanager", "grasseditor", "simplesave")
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


def carpeta_apartadas(carpeta_modulos):
    """Dónde se guardan los .mod sueltos: junto a «modules», no dentro.

    Maya lee como módulo cualquier archivo de la carpeta modules, tenga la extensión
    que tenga, así que renombrarlos no basta: hay que sacarlos de ahí.
    """
    return os.path.join(os.path.dirname(os.path.normpath(carpeta_modulos)), "mantitools_apartadas")


def apartar_sueltas(carpeta_modulos):
    """Saca de la carpeta de módulos los .mod de herramientas sueltas. Devuelve [(id, ruta_nueva)].

    También recoge los que una versión anterior del instalador dejó renombrados a «.mod.mantitools».
    """
    apartadas = []
    destino = carpeta_apartadas(carpeta_modulos)
    for ident, nombres in MODS_SUELTOS.items():
        for nombre in nombres:
            for candidato in (nombre, nombre + SUFIJO_APARTADO):
                ruta = os.path.join(carpeta_modulos, candidato)
                if not os.path.isfile(ruta):
                    continue
                os.makedirs(destino, exist_ok=True)
                nueva = os.path.join(destino, nombre)
                if os.path.exists(nueva):
                    os.remove(nueva)
                shutil.move(ruta, nueva)
                apartadas.append((ident, nueva))
    return apartadas


def devolver_sueltas(rutas, carpeta_modulos=None):
    """Deshace ``apartar_sueltas``: vuelve a poner cada .mod en la carpeta de módulos. Devuelve las rutas devueltas."""
    devueltas = []
    for ruta in rutas:
        if not os.path.isfile(ruta):
            continue
        if ruta.endswith(SUFIJO_APARTADO):  # instalaciones antiguas: renombrado dentro de modules
            original = ruta[:-len(SUFIJO_APARTADO)]
        else:
            modulos = carpeta_modulos or os.path.join(os.path.dirname(os.path.dirname(ruta)), "modules")
            original = os.path.join(modulos, os.path.basename(ruta))
        if not os.path.exists(original):
            shutil.move(ruta, original)
            devueltas.append(original)
    return devueltas


def instalar_en_painter(base, elegida=""):
    """Copia el complemento de Painter de Materials. Devuelve la ruta o None."""
    from mantitools import painter
    try:
        return painter.copiar(base, painter.carpeta(elegida))
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
    _olvidar_codigo_viejo(base)
    from mantitools import carga, estante
    from mantitools.i18n import t
    ruta_painter = instalar_en_painter(base, carga.ajustes()["carpeta_painter"])
    if ruta_painter:
        print("MantiTools | complemento de Painter copiado en " + ruta_painter)
    if apartadas:
        previas = carga.ajustes()["sueltas_desactivadas"]
        nuevas = {r for _, r in apartadas}
        movidas = {os.path.join(carpeta_modulos, os.path.basename(r)) + SUFIJO_APARTADO for r in nuevas}
        carga.ajustes()["sueltas_desactivadas"] = sorted((set(previas) - movidas) | nuevas)
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
    estante.crear(forzar=True, seleccionar=True, ruta_completa=True)
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
    devueltas = devolver_sueltas(carga.ajustes()["sueltas_desactivadas"], _carpeta_modulos())
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
    if not any(os.path.basename(r).startswith(("materials", "muestrario")) for r in devueltas):
        from mantitools import painter  # sin Materials suelto, el complemento ya no lo usa nadie
        painter.quitar(painter.carpeta(carga.ajustes()["carpeta_painter"]))
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
