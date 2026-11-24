"""El complemento de Substance 3D Painter de Materials: dónde va y cómo se copia. No depende de Maya.

Painter carga los complementos de ``<Documentos>/Adobe/Adobe Substance 3D Painter/python/plugins``.
En Windows «Documentos» puede estar en otro sitio (OneDrive, una unidad de red…): se le
pregunta a Windows dónde está. Si aun así no es la carpeta buena, se puede indicar a mano
en Ajustes → Materials (se guarda en los ajustes de MantiTools).
"""

import os
import shutil
import sys

NOMBRE = "materials_painter.py"
NOMBRES_ANTIGUOS = ("muestrario_painter.py",)


def _documentos_windows():
    """La carpeta Documentos de verdad (SHGetKnownFolderPath), o None."""
    try:
        import ctypes
        from ctypes import wintypes

        class GUID(ctypes.Structure):
            _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD), ("Data3", wintypes.WORD),
                        ("Data4", ctypes.c_ubyte * 8)]

        # FOLDERID_Documents {FDD39AD0-238F-46AF-ADB4-6C85480369C7}
        guid = GUID(0xFDD39AD0, 0x238F, 0x46AF, (ctypes.c_ubyte * 8)(0xAD, 0xB4, 0x6C, 0x85, 0x48, 0x03, 0x69, 0xC7))
        ruta = ctypes.c_wchar_p()
        if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(ruta)) != 0:
            return None
        try:
            return ruta.value
        finally:
            ctypes.windll.ole32.CoTaskMemFree(ruta)
    except Exception:
        return None


def carpeta_documentos():
    if sys.platform.startswith("win"):
        ruta = _documentos_windows()
        if ruta and os.path.isdir(ruta):
            return ruta
    return os.path.join(os.path.expanduser("~"), "Documents")


def carpeta_por_defecto():
    return os.path.join(carpeta_documentos(), "Adobe", "Adobe Substance 3D Painter", "python", "plugins")


def carpeta(elegida=""):
    """La carpeta de complementos que se usa: la elegida a mano o la de por defecto."""
    return elegida or carpeta_por_defecto()


def origen(raiz):
    """El complemento que trae el pack (dentro de la copia de Materials), o None."""
    ruta = os.path.join(raiz, "incluidas", "materials", "painter", NOMBRE)
    return ruta if os.path.isfile(ruta) else None


def instalado(destino):
    return os.path.isfile(os.path.join(destino, NOMBRE))


def copiar(raiz, destino):
    """Copia el complemento a ``destino`` (la crea si falta). Devuelve la ruta. OSError si no puede."""
    fuente = origen(raiz)
    if fuente is None:
        raise OSError("el pack no trae {}".format(NOMBRE))
    os.makedirs(destino, exist_ok=True)
    final = os.path.join(destino, NOMBRE)
    shutil.copy2(fuente, final)
    return final


def quitar(destino):
    """Borra el complemento (y los de nombres antiguos) de ``destino``. Devuelve las rutas borradas."""
    borradas = []
    for nombre in (NOMBRE,) + NOMBRES_ANTIGUOS:
        ruta = os.path.join(destino, nombre)
        if os.path.isfile(ruta):
            os.remove(ruta)
            borradas.append(ruta)
    return borradas
