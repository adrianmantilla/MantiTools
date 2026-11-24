"""Juegos de texturas por especie (sin Maya).

Cada juego vive en ``<plugin>/texturas/<juego>/<resolución>/`` con una imagen
por canal::

    corteza_color   corteza_normal   corteza_rugosidad
    hoja_color      hoja_normal      hoja_rugosidad   hoja_translucidez

Formatos: .png, .jpg, .tif o .exr. Si falta la resolución pedida se usa la más
cercana que haya (a igual distancia, la menor). Un árbol con material «clay», o con un juego que no existe,
se queda en clay.

Estilos: además del realista, un juego puede traer ``<juego>/cartoon/<resolución>/`` y
``<juego>/estilizado/<resolución>/`` con los mismos canales. Si falta el estilo pedido
(o un canal de ese estilo), se usa el realista.

Además de la carpeta del plugin se pueden añadir otras (``CARPETAS_EXTRA``), como la de
materiales propios de la biblioteca del alumno. Si un juego está en varias, gana la primera.

La corteza es repetible: su UV da una vuelta entera de textura por cada
«escala_textura» cm. La hoja ocupa toda la imagen: u a lo ancho (0,5 es el
nervio) y v a lo largo, del tallo (0) a la punta (1).
"""

import os

CLAY = "clay"
RESOLUCIONES = ("512", "1k", "2k", "4k")
RESOLUCION_POR_DEFECTO = "1k"
PARTES = ("corteza", "hoja")
CANALES = ("color", "normal", "rugosidad", "translucidez")
ESTILOS = ("realista", "cartoon", "estilizado")
ESTILO_POR_DEFECTO = "realista"
CARPETAS_EXTRA = []  # otras carpetas con juegos (p. ej. <biblioteca>/materiales)
_EXTENSIONES = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".exr")


def carpeta_texturas():
    """<raíz del plugin>/texturas (junto a scripts/ y plug-ins/)."""
    aqui = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(aqui, "..", "..", "texturas"))


def carpetas():
    """Carpetas donde se buscan juegos, por orden: la del plugin y las extra."""
    resultado = [carpeta_texturas()]
    for c in CARPETAS_EXTRA:
        if c and os.path.normpath(c) not in resultado:
            resultado.append(os.path.normpath(c))
    return resultado


def _juegos_en(carpeta):
    if not os.path.isdir(carpeta):
        return []
    return [d for d in os.listdir(carpeta)
            if not d.startswith(".") and os.path.isdir(os.path.join(carpeta, d))]


def juegos(carpeta=None):
    if carpeta:
        return sorted(_juegos_en(carpeta))
    vistos = set()
    for c in carpetas():
        vistos.update(_juegos_en(c))
    return sorted(vistos)


def carpeta_de(juego, carpeta=None):
    """Carpeta que contiene ``juego`` (o None)."""
    for c in ([carpeta] if carpeta else carpetas()):
        if juego and os.path.isdir(os.path.join(c, juego)):
            return c
    return None


def existe(juego, carpeta=None):
    return bool(juego) and juego != CLAY and juego in juegos(carpeta)


def _orden_resoluciones(resolucion):
    i = RESOLUCIONES.index(resolucion) if resolucion in RESOLUCIONES else RESOLUCIONES.index(RESOLUCION_POR_DEFECTO)
    # A igual distancia, la más pequeña: pesa menos en los ordenadores del aula.
    return sorted(RESOLUCIONES, key=lambda r: (abs(RESOLUCIONES.index(r) - i), RESOLUCIONES.index(r)))


def ruta(juego, parte, canal, resolucion=RESOLUCION_POR_DEFECTO, carpeta=None, estilo=ESTILO_POR_DEFECTO):
    """Imagen de ``parte``/``canal`` del juego en ``estilo``, o None si no hay.

    Si el estilo no trae ese canal, se usa el del realista.
    """
    carpeta = carpeta_de(juego, carpeta)
    if not carpeta:
        return None
    bases = [os.path.join(carpeta, juego)]
    if estilo and estilo != ESTILO_POR_DEFECTO:
        bases.insert(0, os.path.join(carpeta, juego, estilo))
    for base_juego in bases:
        for res in _orden_resoluciones(resolucion):
            base = os.path.join(base_juego, res, "{}_{}".format(parte, canal))
            for ext in _EXTENSIONES:
                if os.path.isfile(base + ext):
                    return base + ext
    return None


def canales(juego, parte, resolucion=RESOLUCION_POR_DEFECTO, carpeta=None, estilo=ESTILO_POR_DEFECTO):
    """{canal: ruta} con los canales que existen."""
    resultado = {}
    for canal in CANALES:
        r = ruta(juego, parte, canal, resolucion, carpeta, estilo)
        if r:
            resultado[canal] = r
    return resultado


def estilos(juego, carpeta=None):
    """Estilos que trae el juego (siempre el realista)."""
    carpeta = carpeta_de(juego, carpeta)
    return [e for e in ESTILOS if e == ESTILO_POR_DEFECTO
            or (carpeta and os.path.isdir(os.path.join(carpeta, juego, e)))]
