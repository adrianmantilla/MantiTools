"""Materiales propios del alumno: sus imágenes de corteza y de hoja como juego de texturas.

Se guardan en la biblioteca, en ``<biblioteca>/materiales/propio_<nombre>/1k/``, con los
mismos nombres que los juegos de serie (``corteza_color.jpg``…). Así viajan con la
biblioteca y el plugin los trata igual que una especie (ver texturas.py).

La corteza se copia tal cual: debe ser repetible. La hoja es una sola imagen (la hoja
de pie, el tallo abajo y la punta arriba, el nervio en el centro); el plugin la repite
en un atlas 2x2 con cuatro tonos algo distintos, como los de serie. Para eso usa Qt,
que viene con Maya; sin Qt (pruebas fuera de Maya) la copia tal cual.

No depende de Maya.
"""

import os
import re
import shutil
import unicodedata

from arboles import texturas as tx

PREFIJO = "propio_"
SUBCARPETA = "materiales"
RESOLUCION = "1k"
LADO_HOJA = 512  # cada cuadro del atlas de la hoja
# Tonos de las cuatro variantes de hoja (multiplican el color): igual, más oscura, más amarilla, más fría
TONOS = ((1.0, 1.0, 1.0), (0.86, 0.9, 0.86), (1.05, 1.0, 0.82), (0.92, 0.98, 1.02))
NOMBRE_VISIBLE = "nombre.txt"


def carpeta(carpeta_biblioteca):
    return os.path.join(carpeta_biblioteca, SUBCARPETA)


def registrar(carpeta_biblioteca):
    """Añade los materiales de esa biblioteca a los juegos que ve el plugin."""
    tx.CARPETAS_EXTRA[:] = [carpeta(carpeta_biblioteca)] if carpeta_biblioteca else []


def es_propio(juego):
    return bool(juego) and juego.startswith(PREFIJO)


def nombre_juego(nombre):
    limpio = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode("ascii").lower()
    limpio = re.sub(r"[^a-z0-9]+", "_", limpio).strip("_")
    return PREFIJO + (limpio or "material")


def nombre_visible(juego):
    """El nombre que escribió el alumno (o el del juego sin el prefijo)."""
    base = tx.carpeta_de(juego)
    if base:
        ruta = os.path.join(base, juego, NOMBRE_VISIBLE)
        if os.path.isfile(ruta):
            with open(ruta, encoding="utf-8") as f:
                texto = f.read().strip()
            if texto:
                return texto
    return juego[len(PREFIJO):] if es_propio(juego) else juego


def lista(carpeta_biblioteca):
    return [j for j in tx.juegos(carpeta(carpeta_biblioteca)) if es_propio(j)]


def _extension(ruta):
    ext = os.path.splitext(ruta)[1].lower()
    if ext not in tx._EXTENSIONES:
        raise ValueError(ruta)
    return ".jpg" if ext == ".jpeg" else ext


def atlas_hoja(origen, destino, tenir):
    """Atlas 2x2 de la hoja con Qt; sin Qt, copia la imagen tal cual. Devuelve la ruta."""
    try:
        from PySide6 import QtCore, QtGui
    except ImportError:
        try:
            from PySide2 import QtCore, QtGui
        except ImportError:
            shutil.copyfile(origen, destino)
            return destino
    imagen = QtGui.QImage(origen)
    if imagen.isNull():
        # Qt no la sabe leer (p. ej. un .exr): se copia tal cual y la hoja usa la imagen entera
        shutil.copyfile(origen, destino)
        return destino
    cuadro = imagen.convertToFormat(QtGui.QImage.Format_RGB32).scaled(
        LADO_HOJA, LADO_HOJA, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
    atlas = QtGui.QImage(LADO_HOJA * 2, LADO_HOJA * 2, QtGui.QImage.Format_RGB32)
    pintor = QtGui.QPainter(atlas)
    for i, tono in enumerate(TONOS):
        x, y = (i % 2) * LADO_HOJA, (i // 2) * LADO_HOJA
        pintor.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
        pintor.drawImage(x, y, cuadro)
        if tenir and tono != (1.0, 1.0, 1.0):
            # Multiplicar por un color claro oscurece/tiñe; lo que pasa de 1 se aproxima con 255
            color = QtGui.QColor(*[min(255, int(255 * c)) for c in tono])
            pintor.setCompositionMode(QtGui.QPainter.CompositionMode_Multiply)
            pintor.fillRect(x, y, LADO_HOJA, LADO_HOJA, color)
    pintor.end()
    destino = os.path.splitext(destino)[0] + ".jpg"
    if not atlas.save(destino, None, 92):
        raise IOError(destino)
    return destino


def crear(carpeta_biblioteca, nombre, imagenes):
    """Crea (o rehace) el material propio ``nombre`` con ``imagenes``.

    ``imagenes`` es {(parte, canal): ruta}; hace falta al menos el color de la corteza o
    el de la hoja. Devuelve el nombre del juego (``propio_…``) para el «Material» del árbol.
    """
    if not any(canal == "color" and ruta for (parte, canal), ruta in imagenes.items()):
        raise ValueError("falta el color")
    juego = nombre_juego(nombre)
    destino = os.path.join(carpeta(carpeta_biblioteca), juego, RESOLUCION)
    if os.path.isdir(destino):
        shutil.rmtree(destino)
    os.makedirs(destino)
    for (parte, canal), ruta in sorted(imagenes.items()):
        if not ruta:
            continue
        if parte not in tx.PARTES or canal not in tx.CANALES:
            raise ValueError((parte, canal))
        salida = os.path.join(destino, "{}_{}{}".format(parte, canal, _extension(ruta)))
        if parte == "hoja":
            salida = atlas_hoja(ruta, salida, tenir=canal in ("color", "translucidez"))
        else:
            shutil.copyfile(ruta, salida)
    with open(os.path.join(carpeta(carpeta_biblioteca), juego, NOMBRE_VISIBLE), "w", encoding="utf-8") as f:
        f.write(nombre.strip())
    return juego
