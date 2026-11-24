"""«Usar como hoja»: lee de la escena la malla que ha hecho el alumno (necesita Maya).

La malla puede estar en cualquier postura: follaje.normalizar_hoja toma su lado más
largo como largo de la hoja y el extremo más bajo de ese lado como el tallo. Lo más
cómodo es modelarla de pie, con el tallo abajo. Sus UV se conservan si todas las caras
las tienen; si no, se proyectan de frente.
"""

import maya.api.OpenMaya as om
from maya import cmds

from arboles import follaje


def malla_seleccionada(excluir=None):
    """Forma (mesh) de lo seleccionado que no esté dentro de ``excluir`` (el árbol del editor)."""
    for nodo in cmds.ls(selection=True, long=True) or []:
        formas = [nodo] if cmds.nodeType(nodo) == "mesh" else (
            cmds.listRelatives(nodo, shapes=True, fullPath=True, noIntermediate=True) or [])
        for forma in formas:
            if cmds.nodeType(forma) != "mesh":
                continue
            if excluir and (forma + "|").startswith(cmds.ls(excluir, long=True)[0] + "|"):
                continue
            return forma
    return None


def _trocear(conteos, indices):
    caras, i = [], 0
    for n in conteos:
        caras.append(list(indices[i:i + n]))
        i += n
    return caras


def leer_hoja(forma):
    """Datos normalizados de la hoja (ver follaje.normalizar_hoja) a partir de una forma de Maya."""
    lista = om.MSelectionList()
    lista.add(forma)
    fn = om.MFnMesh(lista.getDagPath(0))
    vertices = [(p.x, p.y, p.z) for p in fn.getPoints(om.MSpace.kWorld)]
    conteos, indices = fn.getVertices()
    caras = _trocear(conteos, indices)
    uvs = uv_caras = None
    us, vs = fn.getUVs()
    if len(us):
        uv_conteos, uv_ids = fn.getAssignedUVs()
        if list(uv_conteos) == list(conteos):  # todas las caras con UV
            uvs = list(zip(us, vs))
            uv_caras = _trocear(conteos, uv_ids)
    return follaje.normalizar_hoja(vertices, caras, uvs, uv_caras)
