"""Prueba de MantiTools dentro de Maya (herramienta de desarrollo).

Desde la terminal, con el mayapy de cada versión (sin interfaz)::

    /Applications/Autodesk/maya2027/Maya.app/Contents/bin/mayapy herramientas/prueba_maya.py
    "C:\\Program Files\\Autodesk\\Maya2027\\bin\\mayapy.exe" herramientas\\prueba_maya.py

Sin interfaz no toca tus preferencias: usa una carpeta de Maya temporal. Comprueba
que el plugin del pack carga cada herramienta desde ``incluidas/``, que cada orden
del estante importa su módulo, que cada ajuste de la ventana central se lee y se
escribe, y el informe de «Comprobar instalación».

También se puede ejecutar desde el Script Editor con Maya abierto (y MantiTools
instalado)::

    exec(open("/ruta/a/mantitools/herramientas/prueba_maya.py").read())

Entonces comprueba además el menú con sus submenús, el estante y la ventana central.
Termina con «RESULTADO: OK» o con la lista de fallos.
"""

import importlib
import os
import sys
import tempfile
import traceback

try:
    RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:  # exec() desde el Script Editor
    RAIZ = os.environ.get("MANTITOOLS_RAIZ", os.getcwd())

fallos = []


def comprobar(condicion, texto):
    print(("  ok    " if condicion else "  FALLO ") + texto, flush=True)
    if not condicion:
        fallos.append(texto)


def preparar_rutas():
    """Lo que haría el .mod: los scripts del pack y de cada herramienta incluida."""
    carpetas = [os.path.join(RAIZ, "scripts")]
    incluidas = os.path.join(RAIZ, "incluidas")
    for ident in sorted(os.listdir(incluidas)):
        carpetas.append(os.path.join(incluidas, ident, "scripts"))
    for carpeta in carpetas:
        if carpeta not in sys.path:
            sys.path.insert(0, carpeta)


def probar_carga(cmds):
    print("\n== Carga")
    from mantitools import carga
    from mantitools import herramientas as hr
    cmds.loadPlugin(os.path.join(RAIZ, "plug-ins", "mantitools_plugin.py"), quiet=True)
    comprobar(cmds.pluginInfo("mantitools_plugin", query=True, loaded=True), "mantitools_plugin cargado")
    if not carga._estado["iniciado"]:
        carga.iniciar()
    for ficha in hr.FICHAS:
        cargada = carga.cargada(ficha.id)
        comprobar(cargada, "{} cargada {}".format(ficha.nombre, carga.fallo(ficha.id)))
        if cargada:
            paquete = importlib.import_module(ficha.paquete)
            dentro = os.path.normpath(paquete.__file__).startswith(os.path.normpath(carga.carpeta_incluida(ficha.id)))
            comprobar(dentro, "{} viene del pack ({})".format(ficha.nombre, os.path.dirname(paquete.__file__)))


def probar_ordenes():
    print("\n== Órdenes del estante")
    from mantitools import herramientas as hr
    for ficha in hr.FICHAS:
        for accion in ficha.acciones:
            modulo = accion.codigo.split()[1]
            funcion = accion.codigo.split("_m.")[1].split("(")[0]
            try:
                existe = callable(getattr(importlib.import_module(modulo), funcion, None))
            except Exception as error:
                existe = False
                print("        " + repr(error))
            comprobar(existe, "{} · {} → {}.{}".format(ficha.nombre, accion.clave, modulo, funcion))


def probar_ajustes():
    print("\n== Ajustes de la ventana central")
    from mantitools import adaptadores as ad
    from mantitools import herramientas as hr
    for ficha in hr.FICHAS:
        pagina = ad.pagina(ficha.id, None)
        for _, controles in pagina.secciones():
            for control in controles:
                if control.tipo in ("boton", "info"):
                    continue
                try:
                    valor = pagina.leer(control.clave)
                    pagina.escribir(control.clave, valor)
                    bien = pagina.leer(control.clave) == valor
                except Exception:
                    traceback.print_exc()
                    bien = False
                comprobar(bien, "{} · {}".format(ficha.nombre, control.clave))


def probar_informe():
    print("\n== Comprobar instalación")
    from mantitools import comprobar as cp
    bien, lineas = cp.informe()
    comprobar(bool(lineas), "el informe tiene líneas")
    if not bien:
        print("        (el informe avisa de algo; mira las líneas con «!»)")


def probar_interfaz(cmds):
    print("\n== Menú, estante y ventana")
    from mantitools import centro, estante, menu
    from mantitools import herramientas as hr
    menu.construir()
    elementos = cmds.menu(menu.MENU, query=True, itemArray=True) or []
    for ficha in hr.FICHAS:
        comprobar(ficha.menu in elementos, "submenú {} dentro de MantiTools".format(ficha.nombre))
        comprobar(not cmds.menu(ficha.menu, exists=True) or ficha.menu in elementos,
                  "{} no queda arriba en la barra".format(ficha.nombre))
    estante.crear(forzar=True)
    botones = cmds.shelfLayout(estante.ESTANTE, query=True, childArray=True) or []
    comprobar(len(botones) == len(hr.FICHAS) + 1, "estante con {} botones".format(len(botones)))
    v = centro.mostrar("herramientas")
    comprobar(v is not None, "ventana central abierta")
    for pestana in centro.PESTANAS:
        centro.mostrar(pestana)
    comprobar(True, "pestañas recorridas")


def main():
    preparar_rutas()
    try:
        from maya import cmds
        if not hasattr(cmds, "about"):  # mayapy: «maya» se importa, pero sin standalone no hay órdenes
            raise ImportError("maya.standalone sin iniciar")
        interfaz = not cmds.about(batch=True)
        propio = False
    except ImportError:
        os.environ["MAYA_APP_DIR"] = tempfile.mkdtemp(prefix="mantitools_maya_")
        import maya.standalone
        maya.standalone.initialize(name="python")
        from maya import cmds
        interfaz, propio = False, True
    print("MantiTools: prueba en Maya {} ({})".format(cmds.about(version=True),
                                                       "con interfaz" if interfaz else "sin interfaz"))
    for paso in (lambda: probar_carga(cmds), probar_ordenes, probar_ajustes, probar_informe):
        try:
            paso()
        except Exception:
            traceback.print_exc()
            fallos.append("excepción en {}".format(getattr(paso, "__name__", "paso")))
    if interfaz:
        try:
            probar_interfaz(cmds)
        except Exception:
            traceback.print_exc()
            fallos.append("excepción en la interfaz")
    print("\nRESULTADO: " + ("OK" if not fallos else "{} fallos:\n- ".format(len(fallos)) + "\n- ".join(fallos)))
    if propio:
        import maya.standalone
        maya.standalone.uninitialize()
        sys.exit(0 if not fallos else 1)  # solo con mayapy: en el Script Editor cerraría Maya
    return not fallos


if __name__ == "__main__":
    main()
