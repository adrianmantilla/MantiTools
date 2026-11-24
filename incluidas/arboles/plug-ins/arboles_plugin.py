"""Plugin de Maya para Árboles.

Aparece en el Plug-in Manager como «arboles_plugin». Al cargarlo crea el menú
Árboles en la barra de Maya y registra el comando «arbolesAccion», que da
deshacer (Ctrl+Z) a los cambios del editor; al descargarlo los quita. El instalador lo marca
para que se cargue solo cada vez que se abre Maya.
"""

import maya.api.OpenMaya as om
from maya import cmds


def maya_useNewAPI():
    pass


class ComandoAccion(om.MPxCommand):
    """arbolesAccion <id>: ejecuta una acción de arboles.acciones con deshacer."""

    NOMBRE = "arbolesAccion"

    def __init__(self):
        om.MPxCommand.__init__(self)
        self.hacer = self.deshacer = None

    @staticmethod
    def crear():
        return ComandoAccion()

    @staticmethod
    def sintaxis():
        s = om.MSyntax()
        s.addArg(om.MSyntax.kString)
        return s

    def doIt(self, argumentos):
        from arboles import acciones
        datos = om.MArgDatabase(self.syntax(), argumentos)
        self.hacer, self.deshacer = acciones.tomar(datos.commandArgumentString(0))
        self.hacer()

    def redoIt(self):
        self.hacer()

    def undoIt(self):
        self.deshacer()

    def isUndoable(self):
        return True


def initializePlugin(objeto):
    import arboles
    plugin = om.MFnPlugin(objeto, "Árboles", arboles.__version__, "Any")
    plugin.registerCommand(ComandoAccion.NOMBRE, ComandoAccion.crear, ComandoAccion.sintaxis)
    try:
        from arboles import interfaz_maya
        cmds.evalDeferred(interfaz_maya.iniciar, lowestPriority=True)
    except Exception as error:
        cmds.warning("Árboles no se pudo cargar: {}".format(error))
    return plugin


def uninitializePlugin(objeto):
    om.MFnPlugin(objeto).deregisterCommand(ComandoAccion.NOMBRE)
    try:
        from arboles import interfaz_maya
        interfaz_maya.quitar_menu()
    except Exception:
        pass
