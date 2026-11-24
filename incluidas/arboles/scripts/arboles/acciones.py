"""Acciones con deshacer: cada cambio del editor es un paso de Ctrl+Z.

``ejecutar(hacer, deshacer)`` guarda las dos funciones y llama al comando
«arbolesAccion» del plugin, que las ejecuta y las mete en la cola de deshacer
de Maya. Las funciones no deben usar cmds (solo la API), porque se llaman
también desde el deshacer.

Sin el plugin cargado (por ejemplo en las pruebas) se ejecuta ``hacer`` sin
deshacer.
"""

import itertools

_pendientes = {}
_contador = itertools.count(1)


def tomar(id_):
    return _pendientes.pop(id_)


def hay_comando():
    try:
        from maya import cmds
        return hasattr(cmds, "arbolesAccion")
    except ImportError:
        return False


def ejecutar(hacer, deshacer, nombre="Arboles"):
    if not hay_comando():
        hacer()
        return False
    from maya import cmds
    id_ = "{}_{}".format(nombre, next(_contador))
    _pendientes[id_] = (hacer, deshacer)
    cmds.arbolesAccion(id_)
    return True
