"""Variantes de un árbol para plantar copias que no sean todas iguales (sin Maya).

La variante 0 es el árbol tal cual. Las demás cambian un poco cada rama (giro,
ángulo, largo, caída y curvatura) y la inclinación del tronco, siempre igual
para el mismo árbol y el mismo número de variante: son reproducibles. Al
plantar, cada variante tiene su propio maestro, y las copias siguen siendo
instancias ligadas: si se cambia el árbol original, cambian todas sus variantes.
"""

import random
import zlib

from arboles import modulos as mod

MAXIMO = 4  # variantes distintas como mucho (y maestros por nivel)

# parámetro: (variación, «suma» o «producto»)
_RAMA = {
    "giro": (30.0, "suma"),
    "angulo": (0.12, "producto"),
    "longitud": (0.12, "producto"),
    "caida": (0.08, "suma"),
    "curvatura": (0.1, "suma"),
}
_TRONCO = {
    "inclinacion": (3.0, "suma"),
    "curvatura": (0.06, "suma"),
}


def _semilla(arbol, numero):
    return zlib.crc32("{}|{}".format(arbol.nombre, numero).encode("utf-8")) & 0xFFFFFFFF


def variante(arbol, numero):
    """Copia de ``arbol`` con la forma de la variante ``numero`` (0 = el original)."""
    copia = arbol.copiar()
    if not numero:
        return copia
    azar = random.Random(_semilla(arbol, numero))
    for m in copia.modulos.values():  # en orden de creación: siempre el mismo reparto
        cambios = _TRONCO if m.tipo == mod.TRONCO else _RAMA
        for nombre, (cuanto, modo) in cambios.items():
            r = azar.uniform(-1.0, 1.0)
            valor = m.valores[nombre]
            if nombre == "giro":
                valor = (valor + r * cuanto) % 360.0
            elif modo == "suma":
                valor = valor + r * cuanto
            else:
                valor = valor * (1.0 + r * cuanto)
            m.fijar(nombre, valor)
    return copia


def sorteo(variantes, azar=random):
    """Número de variante al azar entre 0 y ``variantes`` - 1."""
    return azar.randrange(max(1, min(MAXIMO, int(variantes))))


def escala_e_inclinacion(tamano, inclinacion, azar=random):
    """(escala, giro en X, giro en Z) al azar: ``tamano`` en tanto por uno (0.2 = ±20 %) e
    ``inclinacion`` en grados como mucho, hacia cualquier lado."""
    escala = 1.0 + azar.uniform(-1.0, 1.0) * max(0.0, tamano)
    return escala, azar.uniform(-1.0, 1.0) * inclinacion, azar.uniform(-1.0, 1.0) * inclinacion
