"""Un «maya» falso para las pruebas sin Maya.

``cmds`` responde a cualquier orden con un valor neutro y apunta las llamadas;
las carpetas de usuario van a una carpeta temporal. Basta para importar el pack y
las herramientas incluidas, y para probar la lógica del menú y del estante.
"""

import os
import sys
import tempfile
import types

CARPETA = tempfile.mkdtemp(prefix="mantitools_prueba_")


class Cmds(types.ModuleType):
    def __init__(self):
        super(Cmds, self).__init__("maya.cmds")
        self.llamadas = []
        self.menus = {}       # nombre -> [elementos]
        self.estantes = {}    # nombre -> [botones]
        self.botones = {}     # botón -> opciones con que se creó
        self.opciones = {}
        self.plugins = set()

    # --- lo que las pruebas miran
    def about(self, **k):
        if k.get("batch"):
            return False
        if k.get("version"):
            return "2026"
        return ""

    def internalVar(self, **k):
        sub = {"userAppDir": "app", "userPrefDir": "prefs", "userScriptDir": "scripts",
               "userShelfDir": "shelves"}
        for clave, carpeta in sub.items():
            if k.get(clave):
                ruta = os.path.join(CARPETA, carpeta)
                os.makedirs(ruta, exist_ok=True)
                return ruta + "/"
        return CARPETA + "/"

    def optionVar(self, **k):
        if "exists" in k:
            return k["exists"] in self.opciones
        if "query" in k or "q" in k:
            return self.opciones.get(k.get("query") or k.get("q"), 0)
        for tipo in ("intValue", "stringValue", "floatValue", "iv", "sv", "fv"):
            if tipo in k:
                nombre, valor = k[tipo]
                self.opciones[nombre] = valor
        if "remove" in k:
            self.opciones.pop(k["remove"], None)
        return None

    def menu(self, nombre=None, **k):
        if k.get("exists"):
            return nombre in self.menus
        if k.get("query") and k.get("itemArray"):
            return list(self.menus.get(nombre, []))
        if nombre is None:
            nombre = "menu{}".format(len(self.menus))
        self.menus[nombre] = []
        self._actual = nombre
        return nombre

    def menuItem(self, nombre=None, **k):
        if k.get("exists"):
            return any(nombre in v for v in self.menus.values()) or nombre in self.menus
        padre = k.get("parent") or getattr(self, "_actual", None)
        if nombre is None:
            nombre = "item{}".format(sum(len(v) for v in self.menus.values()))
        if padre in self.menus:
            lista = self.menus[padre]
            if "insertAfter" in k:
                despues = k["insertAfter"]
                pos = lista.index(despues) + 1 if despues in lista else 0
                lista.insert(pos, nombre)
            else:
                lista.append(nombre)
        if k.get("subMenu"):
            self.menus[nombre] = []
            self._actual = nombre
        return nombre

    def setParent(self, *a, **k):
        if k.get("menu") and a and a[0] in self.menus:
            self._actual = a[0]

    def deleteUI(self, nombre, **k):
        self.menus.pop(nombre, None)
        for lista in self.menus.values():
            if nombre in lista:
                lista.remove(nombre)
        self.estantes.pop(nombre, None)
        for lista in self.estantes.values():
            if nombre in lista:
                lista.remove(nombre)

    def shelfLayout(self, nombre=None, **k):
        if k.get("exists"):
            return nombre in self.estantes
        if k.get("query") and k.get("childArray"):
            return list(self.estantes.get(nombre, []))
        return nombre

    def shelfButton(self, boton=None, **k):
        if k.get("query"):
            datos = self.botones.get(boton, {})
            return datos.get("label") if k.get("label") else datos.get("image", "")
        padre = k["parent"]
        nombre = "boton{}".format(sum(len(v) for v in self.estantes.values()))
        self.estantes.setdefault(padre, []).append(nombre)
        self.llamadas.append(("shelfButton", k))
        self.botones[nombre] = k
        return nombre

    def pluginInfo(self, nombre=None, **k):
        if k.get("query") and k.get("loaded"):
            return nombre in self.plugins
        return None

    def loadPlugin(self, ruta, **k):
        self.plugins.add(os.path.splitext(os.path.basename(ruta))[0])
        return [ruta]

    def unloadPlugin(self, nombre, **k):
        self.plugins.discard(nombre)

    def evalDeferred(self, orden=None, **k):
        if callable(orden):
            orden()

    def __getattr__(self, nombre):
        if nombre.startswith("__"):
            raise AttributeError(nombre)

        def orden(*a, **k):
            self.llamadas.append((nombre, a, k))
            if k.get("exists"):
                return False
            return None
        return orden


class Mel(types.ModuleType):
    def __init__(self):
        super(Mel, self).__init__("maya.mel")
        self.ordenes = []

    def eval(self, texto):
        self.ordenes.append(texto)
        if "addNewShelfTab" in texto:
            nombre = texto.split('"')[1]
            sys.modules["maya.cmds"].estantes.setdefault(nombre, [])
        return ""


class Vacio(types.ModuleType):
    def __getattr__(self, nombre):
        if nombre.startswith("__"):
            raise AttributeError(nombre)
        return Vacio(self.__name__ + "." + nombre)

    def __call__(self, *a, **k):
        return None


def instalar():
    """Pone el maya falso en ``sys.modules``. Devuelve (cmds, mel)."""
    cmds, mel = Cmds(), Mel()
    maya = types.ModuleType("maya")
    maya.cmds, maya.mel = cmds, mel
    maya.__path__ = []
    sys.modules["maya"] = maya
    sys.modules["maya.cmds"] = cmds
    sys.modules["maya.mel"] = mel
    for nombre in ("maya.OpenMayaUI", "maya.OpenMaya", "maya.api", "maya.api.OpenMaya", "maya.api.OpenMayaUI",
                   "maya.utils", "maya.app", "maya.app.general", "maya.app.general.mayaMixin"):
        modulo = Vacio(nombre)
        modulo.__path__ = []
        sys.modules[nombre] = modulo
        padre, _, hijo = nombre.rpartition(".")
        setattr(sys.modules[padre], hijo, modulo)

    class MayaQWidgetDockableMixin(object):
        def show(self, *a, **k):
            super(MayaQWidgetDockableMixin, self).show()

    sys.modules["maya.app.general.mayaMixin"].MayaQWidgetDockableMixin = MayaQWidgetDockableMixin
    return cmds, mel


def quitar():
    for nombre in list(sys.modules):
        if nombre == "maya" or nombre.startswith("maya."):
            del sys.modules[nombre]
