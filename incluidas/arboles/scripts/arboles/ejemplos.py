"""Plantillas de inicio del editor: árboles ya montados para no empezar de cero.

Todo lo que crean se puede editar después. «vacio» es solo un tronco.
"""

from arboles import especies
from arboles.arbol import Arbol

_DORADO = 137.5


def vacio():
    arbol = Arbol("arbol_nuevo")
    arbol.anadir_tronco(altura=400, grosor=18, curvatura=0.1)
    return arbol


def copa_redonda():
    arbol = Arbol("copa_redonda")
    tronco = arbol.anadir_tronco(altura=520, grosor=22, estrechamiento=0.3, inclinacion=4,
                                 curvatura=0.12, raices=0.45, irregularidad=0.3, nudos=3)
    principales = 7
    for i in range(principales):
        f = i / float(principales - 1)
        rama = arbol.anadir_rama(tronco, posicion=0.42 + 0.5 * f, giro=(i * _DORADO) % 360,
                                 angulo=68 - 28 * f, longitud=330 - 170 * f, caida=0.25,
                                 curvatura=0.25, grosor=0.55 - 0.15 * f, nudos=1,
                                 follaje="hoja_ancha", densidad=0.35, zona=0.35)
        for j in range(2):
            arbol.anadir_rama(rama, posicion=0.45 + 0.3 * j, giro=90 + 180 * j + 25 * i,
                              angulo=45, longitud=(150 - 60 * f) * (1.0 - 0.25 * j), caida=0.25,
                              curvatura=0.15, grosor=0.65, nudos=0, irregularidad=0.1,
                              follaje="hoja_ancha", densidad=0.7, zona=0.8)
    return arbol


def columnar():
    arbol = Arbol("columnar")
    tronco = arbol.anadir_tronco(altura=750, grosor=20, estrechamiento=0.2, curvatura=0.05,
                                 raices=0.3, irregularidad=0.2, nudos=2)
    ramas = 12
    for i in range(ramas):
        f = i / float(ramas - 1)
        arbol.anadir_rama(tronco, posicion=0.18 + 0.78 * f, giro=(i * _DORADO) % 360,
                          angulo=22 + 8 * (1 - f), longitud=230 - 130 * f, caida=0.05,
                          curvatura=0.35, grosor=0.35, follaje="hoja_fina", densidad=0.8,
                          zona=0.85, hacia_arriba=0.7)
    return arbol


def lloron():
    arbol = Arbol("lloron")
    tronco = arbol.anadir_tronco(altura=450, grosor=26, estrechamiento=0.4, inclinacion=6,
                                 curvatura=0.2, raices=0.6, irregularidad=0.4, nudos=4)
    principales = 6
    for i in range(principales):
        f = i / float(principales - 1)
        rama = arbol.anadir_rama(tronco, posicion=0.6 + 0.35 * f, giro=(i * _DORADO) % 360,
                                 angulo=55 - 15 * f, longitud=300 - 80 * f, caida=0.3,
                                 curvatura=0.45, grosor=0.5, follaje="ninguno")
        for j in range(2):
            arbol.anadir_rama(rama, posicion=0.4 + 0.35 * j, giro=(j * _DORADO + 40 * i) % 360,
                              angulo=40, longitud=340 - 60 * j, caida=1.0, curvatura=0.0,
                              grosor=0.5, estrechamiento=0.15, follaje="hoja_fina",
                              densidad=0.8, zona=0.85, hacia_arriba=0.0)
    return arbol


def arbusto():
    arbol = Arbol("arbusto")
    tronco = arbol.anadir_tronco(altura=60, grosor=9, estrechamiento=0.6, curvatura=0.0,
                                 raices=0.2, irregularidad=0.3, nudos=0)
    tallos = 9
    for i in range(tallos):
        arbol.anadir_rama(tronco, posicion=0.5 + 0.5 * (i % 3) / 2.0, giro=(i * _DORADO) % 360,
                          angulo=25 + 30 * ((i * 7) % 3) / 2.0, longitud=110 + 25 * ((i * 5) % 4),
                          caida=0.2, curvatura=0.3, grosor=0.55, follaje="hoja_ancha",
                          densidad=0.9, zona=0.8, tamano_hoja=0.8, hacia_arriba=0.5)
    return arbol


def conifera():
    """Cono de pisos de ramas casi horizontales, más cortas hacia arriba, como un abeto."""
    arbol = Arbol("conifera")
    tronco = arbol.anadir_tronco(altura=800, grosor=21, estrechamiento=0.12, curvatura=0.03,
                                 raices=0.35, irregularidad=0.25, nudos=0)
    pisos, por_piso = 8, 4
    for p in range(pisos):
        f = p / float(pisos - 1)
        for k in range(por_piso):
            arbol.anadir_rama(tronco, posicion=0.14 + 0.82 * f, giro=(k * 360.0 / por_piso + p * 31.0) % 360,
                              angulo=80 - 25 * f, longitud=280 - 230 * f, caida=0.35 * (1 - f),
                              curvatura=0.1, grosor=0.3, estrechamiento=0.1, nudos=0, irregularidad=0.05,
                              follaje="aguja", densidad=0.6, zona=0.9, tamano_hoja=2.8, hacia_arriba=0.2)
    return arbol


def abedul():
    """Tronco fino y alto, ramas que suben y puntas colgantes de hoja pequeña y redonda."""
    arbol = Arbol("abedul")
    tronco = arbol.anadir_tronco(altura=620, grosor=14, estrechamiento=0.25, inclinacion=5,
                                 curvatura=0.18, raices=0.2, irregularidad=0.15, nudos=4)
    principales = 8
    for i in range(principales):
        f = i / float(principales - 1)
        rama = arbol.anadir_rama(tronco, posicion=0.38 + 0.55 * f, giro=(i * _DORADO) % 360,
                                 angulo=40 - 10 * f, longitud=240 - 110 * f, caida=0.15,
                                 curvatura=0.3, grosor=0.45, nudos=1, follaje="hoja_redonda",
                                 densidad=0.4, zona=0.4)
        arbol.anadir_rama(rama, posicion=0.6, giro=(90 + 60 * i) % 360, angulo=35,
                          longitud=150 - 50 * f, caida=0.7, curvatura=0.0, grosor=0.6,
                          estrechamiento=0.15, nudos=0, follaje="hoja_redonda", densidad=0.75,
                          zona=0.85, hacia_arriba=0.2)
    return arbol


# Frondosidad: cuánto follaje lleva la plantilla. «normal» es la plantilla tal cual.
FRONDOSIDADES = ("clara", "normal", "frondosa")
_FRONDOSIDAD = {
    # densidad, tamaño de hoja, zona con hojas (multiplicadores), ramitas extra
    "clara": (0.5, 0.9, 0.8, False),
    "normal": (1.0, 1.0, 1.0, False),
    "frondosa": (1.45, 1.2, 1.15, True),
}


def con_frondosidad(arbol, frondosidad="normal"):
    """Ajusta el follaje de una plantilla; la frondosa añade una ramita con hojas a cada rama final."""
    densidad, tamano, zona, ramitas = _FRONDOSIDAD[frondosidad]
    hojas = [m for m in list(arbol.modulos.values())
             if m.tipo == "rama" and m.valores.get("follaje", "ninguno") != "ninguno"]
    for m in hojas:
        m.fijar("densidad", m.valores["densidad"] * densidad)
        m.fijar("tamano_hoja", m.valores["tamano_hoja"] * tamano)
        m.fijar("zona", m.valores["zona"] * zona)
    if ramitas and len(hojas) <= 24:  # los árboles ya muy ramificados solo ganan densidad
        for i, m in enumerate(hojas):
            if arbol.hijos(m.id):
                continue
            v = m.valores
            arbol.anadir_rama(m, posicion=0.55, giro=(i * _DORADO + 70) % 360, angulo=40,
                              longitud=max(25.0, v["longitud"] * 0.4), caida=v["caida"],
                              curvatura=v["curvatura"], grosor=0.55, nudos=0, irregularidad=0.1,
                              follaje=v["follaje"], densidad=v["densidad"], zona=0.9,
                              tamano_hoja=v["tamano_hoja"] * 0.9, hacia_arriba=v["hacia_arriba"])
    if frondosidad != "normal":
        arbol.nombre = "{}_{}".format(arbol.nombre, frondosidad)
    return arbol


def crear(plantilla, frondosidad="normal"):
    receta = PLANTILLAS.get(plantilla) or SENCILLAS[plantilla]
    return con_frondosidad(receta(), frondosidad)


# Plantillas del editor: solo tronco y las especies realistas. Las funciones sencillas de arriba
# (copa_redonda, columnar…) se quedan para las pruebas y como ejemplo de receta a mano.
PLANTILLAS = dict([("vacio", vacio)] + list(especies.ESPECIES.items()))
EJEMPLOS = PLANTILLAS
# Las plantillas sencillas de las primeras versiones (siguen funcionando por su nombre)
SENCILLAS = {
    "copa_redonda": copa_redonda,
    "columnar": columnar,
    "lloron": lloron,
    "arbusto_sencillo": arbusto,
    "conifera": conifera,
    "abedul_sencillo": abedul,
}
