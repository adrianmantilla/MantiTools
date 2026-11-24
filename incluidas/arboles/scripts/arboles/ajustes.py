"""Ajustes del usuario: dónde está la biblioteca y si ya se dio la bienvenida.

Se guardan en un JSON dentro de la carpeta de preferencias de Maya del usuario
(``<maya>/arboles/ajustes.json``). Este módulo no depende de Maya para poder
probarlo fuera; la ruta de preferencias se la pasa quien lo usa.
"""

import json
import os
import sys

NOMBRE_CARPETA_BIBLIOTECA = "Arboles"
SUBCARPETAS_BIBLIOTECA = ("arboles", "miniaturas", "ramas", "materiales", "hojas")
_ARCHIVO = "ajustes.json"


def carpeta_documentos():
    """Carpeta Documentos del usuario en Windows y macOS.

    En Windows no se usa ``~``: Maya cambia HOME a la carpeta Documentos, y
    además Documentos puede estar redirigida (OneDrive), así que se pregunta
    al sistema.
    """
    if sys.platform.startswith("win"):
        try:
            import ctypes
            from ctypes import wintypes

            buffer = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            # CSIDL_PERSONAL = 5 (Mis documentos)
            if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buffer) == 0 and buffer.value:
                return buffer.value
        except Exception:
            pass
        perfil = os.environ.get("USERPROFILE")
        if perfil:
            return os.path.join(perfil, "Documents")
    return os.path.join(os.path.expanduser("~"), "Documents")


def biblioteca_por_defecto():
    return os.path.join(carpeta_documentos(), NOMBRE_CARPETA_BIBLIOTECA)


class Ajustes(object):
    """Lee y escribe los ajustes en ``carpeta_preferencias``."""

    def __init__(self, carpeta_preferencias):
        self.carpeta = carpeta_preferencias
        self.ruta = os.path.join(carpeta_preferencias, _ARCHIVO)
        self.datos = self._leer()

    def _leer(self):
        try:
            with open(self.ruta, encoding="utf-8") as f:
                datos = json.load(f)
            return datos if isinstance(datos, dict) else {}
        except (OSError, ValueError):
            return {}

    def guardar(self):
        os.makedirs(self.carpeta, exist_ok=True)
        temporal = self.ruta + ".tmp"
        with open(temporal, "w", encoding="utf-8") as f:
            json.dump(self.datos, f, ensure_ascii=False, indent=2)
        os.replace(temporal, self.ruta)

    @property
    def carpeta_biblioteca(self):
        return self.datos.get("carpeta_biblioteca")

    @property
    def resolucion_texturas(self):
        from arboles.texturas import RESOLUCION_POR_DEFECTO, RESOLUCIONES
        r = self.datos.get("resolucion_texturas")
        return r if r in RESOLUCIONES else RESOLUCION_POR_DEFECTO

    def fijar_resolucion_texturas(self, resolucion):
        from arboles.texturas import RESOLUCIONES
        if resolucion not in RESOLUCIONES:
            raise ValueError(resolucion)
        self.datos["resolucion_texturas"] = resolucion
        self.guardar()

    @property
    def estilo_texturas(self):
        from arboles.texturas import ESTILO_POR_DEFECTO, ESTILOS
        e = self.datos.get("estilo_texturas")
        return e if e in ESTILOS else ESTILO_POR_DEFECTO

    def fijar_estilo_texturas(self, estilo):
        from arboles.texturas import ESTILOS
        if estilo not in ESTILOS:
            raise ValueError(estilo)
        self.datos["estilo_texturas"] = estilo
        self.guardar()

    def primer_uso(self):
        return not self.carpeta_biblioteca

    def fijar_biblioteca(self, ruta):
        """Crea la carpeta (y sus subcarpetas) y la guarda como biblioteca."""
        ruta = os.path.normpath(os.path.expanduser(ruta))
        preparar_biblioteca(ruta)
        self.datos["carpeta_biblioteca"] = ruta
        self.guardar()
        from arboles import materiales_propios
        materiales_propios.registrar(ruta)  # sus materiales propios, ya desde ahora
        return ruta


def preparar_biblioteca(ruta):
    for sub in SUBCARPETAS_BIBLIOTECA:
        os.makedirs(os.path.join(ruta, sub), exist_ok=True)
    return ruta


def se_puede_escribir(ruta):
    if not ruta or not os.path.isdir(ruta):
        return False
    prueba = os.path.join(ruta, ".arboles_prueba")
    try:
        with open(prueba, "w") as f:
            f.write("ok")
        os.remove(prueba)
        return True
    except OSError:
        return False
