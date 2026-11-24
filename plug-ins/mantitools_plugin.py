"""Plugin de Maya para MantiTools.

Aparece en el Plug-in Manager como «mantitools_plugin». Al cargarlo carga las
herramientas activas del pack (cada una es su propio plugin), crea el menú
MantiTools y, si falta, el estante MantiTools. Al descargarlo lo quita todo.
"""

import maya.api.OpenMaya as om
from maya import cmds


def maya_useNewAPI():
    pass


def initializePlugin(objeto):
    import mantitools
    plugin = om.MFnPlugin(objeto, "MantiTools", mantitools.__version__, "Any")
    try:
        from mantitools import carga
        cmds.evalDeferred(carga.iniciar, lowestPriority=True)
    except Exception as error:
        cmds.warning("MantiTools no se pudo cargar: {}".format(error))
    return plugin


def uninitializePlugin(objeto):
    try:
        from mantitools import carga
        carga.detener()
    except Exception as error:
        cmds.warning("MantiTools no se descargó del todo: {}".format(error))
