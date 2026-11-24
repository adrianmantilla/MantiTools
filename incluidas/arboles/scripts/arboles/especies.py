"""Árboles de ejemplo realistas, por especie.

Cada especie se describe con su tronco y una receta por nivel de ramas
(principales, secundarias, ramitas). El generador reparte las ramas con
pequeñas variaciones (siempre las mismas: la semilla es fija), así que el
resultado es un árbol normal del editor: todo se puede tocar después.

Lo que da realismo con pocos triángulos:
- tres niveles de ramas, cada uno más corto, fino y caído que el anterior;
- la silueta de la copa sale del largo de las ramas según dónde nacen (perfil);
- las hojas se concentran en las ramitas finales, no en las ramas gruesas;
- nada es perfecto: ángulos, largos, giros y posiciones varían un poco.
"""

import math
import random

from arboles.arbol import Arbol

_DORADO = 137.5


def _perfil(nombre, p):
    """Largo relativo de una rama según dónde nace (p de 0 a 1 en la zona con ramas)."""
    if nombre == "conico":       # abeto: largas abajo, cortas arriba
        return 1.0 - 0.85 * p
    if nombre == "redondo":      # roble, haya: más largas en el centro de la copa
        return 0.55 + 0.45 * math.sin(math.pi * (0.25 + 0.75 * p))
    if nombre == "parasol":      # pino piñonero: todo arriba y abierto
        return 0.75 + 0.25 * p
    if nombre == "ovalado":      # abedul, sauce
        return 0.6 + 0.4 * math.sin(math.pi * (0.1 + 0.8 * p))
    if nombre == "columna":      # columna estrecha
        return 1.0 - 0.6 * p * p
    if nombre == "huso":         # ciprés: más ancho por debajo de la mitad y en punta arriba
        return 0.2 + 0.8 * math.sin(math.pi * (0.12 + 0.88 * p))
    return 1.0


def _ramificar(arbol, madre, largo_madre, niveles, azar, profundidad=0, desfase=0.0):
    if profundidad >= len(niveles):
        return
    r = niveles[profundidad]
    n = r["n"]
    if isinstance(n, tuple):
        n = azar.randint(*n)
    a, b = r["pos"]
    for i in range(n):
        f = (i + 0.5) / n if n > 1 else 0.5
        posicion = min(0.98, max(0.02, a + (b - a) * f + azar.uniform(-0.5, 0.5) * (b - a) / max(n, 1)))
        if r.get("giro") == "opuesto":
            giro = (desfase + 180.0 * i + 90.0 * (i // 2) + azar.uniform(-25, 25)) % 360
        elif r.get("giro") == "verticilo":
            por_piso = r.get("por_piso", 4)
            giro = (desfase + (i % por_piso) * 360.0 / por_piso + (i // por_piso) * 37.0 + azar.uniform(-15, 15)) % 360
            posicion = min(0.98, a + (b - a) * (i // por_piso) / max(1, (n - 1) // por_piso))
        else:
            giro = (desfase + i * _DORADO + azar.uniform(-20, 20)) % 360
        p = (posicion - a) / max(b - a, 1e-6)
        largo = largo_madre * r["largo"] * _perfil(r.get("perfil"), p) * azar.uniform(0.8, 1.15)
        valores = dict(
            posicion=posicion, giro=giro,
            angulo=r["angulo"] + r.get("angulo_punta", 0.0) * p + azar.uniform(-1, 1) * r.get("var_angulo", 8.0),
            longitud=max(12.0, largo),
            caida=min(1.0, max(0.0, r["caida"] + azar.uniform(-0.08, 0.08))),
            curvatura=r.get("curvatura", 0.0) + azar.uniform(-0.1, 0.1),
            grosor=r.get("grosor", 0.5), estrechamiento=r.get("estrechamiento", 0.25),
            irregularidad=r.get("irregularidad", 0.15), nudos=r.get("nudos", 0),
            torsion=azar.uniform(-1, 1) * r.get("torsion", 0.0),
            follaje=r.get("follaje", "ninguno"),
        )
        if valores["follaje"] != "ninguno":
            valores.update(densidad=r["densidad"], zona=r["zona"], tamano_hoja=r.get("tamano", 1.0),
                           hacia_arriba=r.get("hacia_arriba", 0.4))
        rama = arbol.anadir_rama(madre, **valores)
        tortuoso = r.get("tortuoso", 0.0)
        if tortuoso:  # ramas que cambian de rumbo, no arcos perfectos
            for indice, peso in ((0, 1.0), (1, 0.8), (2, 0.4)):
                d = [azar.uniform(-1, 1) for _ in range(3)]
                d[1] *= 0.6
                rama.fijar_control(indice, tuple(c * tortuoso * valores["longitud"] * peso for c in d))
        _ramificar(arbol, rama, valores["longitud"], niveles, azar, profundidad + 1, azar.uniform(0, 360))


def _especie(nombre, tronco, niveles, semilla):
    arbol = Arbol(nombre, material=nombre)  # texturas de su especie si están instaladas
    t = arbol.anadir_tronco(**tronco)
    _ramificar(arbol, t, tronco["altura"], niveles, random.Random(semilla))
    return arbol


def roble():
    """Tronco corto y grueso, ramas principales tortuosas y una copa ancha y redonda."""
    return _especie("roble", dict(altura=430, grosor=36, estrechamiento=0.35, inclinacion=5, curvatura=0.15,
                                  raices=0.7, irregularidad=0.55, nudos=5, torsion=25), [
        dict(n=6, pos=(0.4, 0.95), angulo=60, angulo_punta=-25, largo=1.0, perfil="redondo", caida=0.15,
             curvatura=0.15, grosor=0.62, irregularidad=0.45, nudos=2, torsion=40, var_angulo=12, tortuoso=0.12),
        dict(n=(3, 4), pos=(0.3, 0.92), angulo=50, largo=0.5, caida=0.3, curvatura=0.15, grosor=0.6,
             irregularidad=0.25, nudos=1, tortuoso=0.1, follaje="hoja_roble", densidad=0.9, zona=0.5, tamano=2.0),
        dict(n=(2, 3), pos=(0.4, 0.95), angulo=42, largo=0.5, caida=0.35, grosor=0.6, estrechamiento=0.3,
             follaje="hoja_roble", densidad=1.4, zona=0.95, tamano=2.0, hacia_arriba=0.45),
    ], 11)


def haya():
    """Tronco recto, liso y gris; copa alta y ovalada de ramas que suben y luego se abren."""
    return _especie("haya", dict(altura=720, grosor=27, estrechamiento=0.25, curvatura=0.05,
                                 raices=0.55, irregularidad=0.08, nudos=1), [
        dict(n=7, pos=(0.3, 0.95), angulo=38, angulo_punta=-15, largo=0.58, perfil="ovalado", caida=0.25,
             curvatura=0.2, grosor=0.5, irregularidad=0.08, tortuoso=0.08),
        dict(n=(3, 4), pos=(0.3, 0.95), angulo=50, largo=0.55, caida=0.45, curvatura=0.05, grosor=0.6,
             tortuoso=0.06, follaje="hoja_ancha", densidad=0.9, zona=0.5, tamano=1.8),
        dict(n=2, pos=(0.5, 0.95), angulo=45, largo=0.45, caida=0.5, grosor=0.6,
             follaje="hoja_ancha", densidad=1.3, zona=0.95, tamano=1.8, hacia_arriba=0.5),
    ], 23)


def pino_pinonero():
    """Tronco alto que se abre en brazos en forma de copa de vino, con una sombrilla plana y densa arriba."""
    return _especie("pino_pinonero", dict(altura=620, grosor=26, estrechamiento=0.45, inclinacion=4,
                                          curvatura=0.1, raices=0.4, irregularidad=0.35, nudos=2), [
        dict(n=6, pos=(0.8, 1.0), angulo=40, largo=0.6, caida=0.15, curvatura=0.1, grosor=0.68,
             estrechamiento=0.4, irregularidad=0.3, nudos=1, var_angulo=4, tortuoso=0.05),
        dict(n=(4, 5), pos=(0.4, 1.0), angulo=72, largo=0.55, caida=0.1, curvatura=0.0, grosor=0.6,
             var_angulo=6, tortuoso=0.05, follaje="pinocha", densidad=1.0, zona=0.3, tamano=1.9,
             hacia_arriba=0.6),
        dict(n=(3, 4), pos=(0.3, 1.0), angulo=60, largo=0.5, caida=0.25, curvatura=0.15, grosor=0.6,
             var_angulo=10, follaje="pinocha", densidad=1.5, zona=0.9, tamano=1.9, hacia_arriba=0.65),
    ], 37)


def abeto():
    """Pisos de ramas que bajan un poco y suben en la punta, cubiertas de ramilletes: un cono denso."""
    return _especie("abeto", dict(altura=900, grosor=22, estrechamiento=0.08, curvatura=0.02,
                                  raices=0.35, irregularidad=0.2), [
        dict(n=30, pos=(0.06, 0.97), giro="verticilo", por_piso=5, angulo=95, angulo_punta=-35, largo=0.4,
             perfil="conico", caida=0.3, curvatura=0.3, grosor=0.3, estrechamiento=0.1, var_angulo=5,
             follaje="aguja_corta", densidad=1.5, zona=0.95, tamano=2.3, hacia_arriba=0.15),
        dict(n=2, pos=(0.3, 0.9), giro="opuesto", angulo=55, largo=0.45, caida=0.2, grosor=0.5,
             follaje="aguja_corta", densidad=1.4, zona=0.95, tamano=2.1, hacia_arriba=0.1),
    ], 41)


def abedul():
    """Tronco fino y claro, ramas que suben y ramitas largas y colgantes."""
    return _especie("abedul", dict(altura=680, grosor=15, estrechamiento=0.22, inclinacion=4,
                                   curvatura=0.15, raices=0.2, irregularidad=0.15, nudos=5), [
        dict(n=9, pos=(0.3, 0.95), angulo=35, angulo_punta=-10, largo=0.4, perfil="ovalado", caida=0.15,
             curvatura=0.35, grosor=0.45, irregularidad=0.1, nudos=1, tortuoso=0.08),
        dict(n=(4, 5), pos=(0.25, 0.95), angulo=50, largo=0.7, caida=0.75, grosor=0.55, estrechamiento=0.2,
             follaje="hoja_redonda", densidad=1.1, zona=0.85, tamano=1.4, hacia_arriba=0.2),
    ], 53)


def sauce_lloron():
    """Tronco corto que se abre en brazos curvos; de ellos cuelgan cortinas de ramitas hasta casi el suelo."""
    return _especie("sauce_lloron", dict(altura=330, grosor=32, estrechamiento=0.45, inclinacion=7,
                                         curvatura=0.2, raices=0.6, irregularidad=0.5, nudos=4), [
        dict(n=6, pos=(0.5, 1.0), angulo=50, angulo_punta=-15, largo=1.0, perfil="ovalado", caida=0.25,
             curvatura=0.25, grosor=0.55, irregularidad=0.35, nudos=1, tortuoso=0.12, var_angulo=12),
        dict(n=(5, 6), pos=(0.3, 1.0), angulo=70, largo=1.2, caida=0.92, curvatura=-0.2, grosor=0.4,
             estrechamiento=0.12, tortuoso=0.05, var_angulo=14, follaje="hoja_fina", densidad=0.85, zona=0.9, tamano=1.0, hacia_arriba=0.0),
    ], 61)


def cipres():
    """Columna estrecha y densa: muchas ramas cortas que suben pegadas al tronco."""
    return _especie("cipres", dict(altura=950, grosor=18, estrechamiento=0.1, curvatura=0.03,
                                   raices=0.3, irregularidad=0.2), [
        dict(n=44, pos=(0.04, 0.98), angulo=32, largo=0.27, perfil="huso", caida=0.0, curvatura=0.3,
             grosor=0.35, estrechamiento=0.15, var_angulo=5, follaje="escama", densidad=2.0, zona=0.95,
             tamano=3.0, hacia_arriba=0.85),
    ], 71)


def olivo():
    """Tronco corto, retorcido y abierto en varios brazos; copa baja y redondeada de hoja fina."""
    return _especie("olivo", dict(altura=210, grosor=28, estrechamiento=0.6, inclinacion=12,
                                  curvatura=0.3, raices=0.8, irregularidad=0.8, nudos=6, torsion=90), [
        dict(n=4, pos=(0.75, 1.0), angulo=40, largo=1.4, perfil="redondo", caida=0.1, curvatura=0.3,
             grosor=0.7, estrechamiento=0.4, irregularidad=0.6, nudos=3, torsion=60, var_angulo=12, tortuoso=0.14),
        dict(n=(3, 4), pos=(0.35, 1.0), angulo=48, largo=0.55, caida=0.35, curvatura=0.1, grosor=0.55,
             irregularidad=0.3, tortuoso=0.1, follaje="hoja_fina", densidad=0.8, zona=0.5, tamano=1.1,
             hacia_arriba=0.55),
        dict(n=(2, 3), pos=(0.45, 1.0), angulo=40, largo=0.5, caida=0.45, grosor=0.6,
             follaje="hoja_fina", densidad=1.3, zona=0.95, tamano=1.1, hacia_arriba=0.55),
    ], 83)


def arbusto():
    """Muchos tallos finos que salen del suelo y se abren hacia fuera, cada uno ramificado, con hoja pequeña."""
    # El «tronco» es solo la cepa, a ras de suelo: lo que se ve son los tallos, abiertos desde abajo
    # (si salen juntos y gruesos, de lejos parecen un tronco).
    return _especie("arbusto", dict(altura=2, grosor=6, estrechamiento=0.5, raices=0.0,
                                    irregularidad=0.3), [
        dict(n=14, pos=(0.1, 1.0), angulo=44, angulo_punta=0, largo=60.0, caida=0.35, curvatura=-0.2,
             grosor=0.32, estrechamiento=0.35, irregularidad=0.2, var_angulo=16, tortuoso=0.12),
        dict(n=(3, 4), pos=(0.25, 1.0), angulo=45, largo=0.45, caida=0.3, grosor=0.6,
             follaje="hoja_redonda", densidad=1.2, zona=0.95, tamano=0.9, hacia_arriba=0.5),
    ], 97)


def encina():
    """Tronco corto y torcido, copa redonda, baja y muy densa de hoja pequeña y oscura."""
    return _especie("encina", dict(altura=240, grosor=30, estrechamiento=0.5, inclinacion=6, curvatura=0.2,
                                   raices=0.6, irregularidad=0.5, nudos=4, torsion=30), [
        dict(n=8, pos=(0.5, 1.0), angulo=66, angulo_punta=-30, largo=1.45, perfil="redondo", caida=0.05,
             curvatura=0.25, grosor=0.65, irregularidad=0.4, nudos=2, torsion=30, var_angulo=12, tortuoso=0.12),
        dict(n=(4, 5), pos=(0.2, 1.0), angulo=50, largo=0.42, caida=0.08, curvatura=0.15, grosor=0.6,
             tortuoso=0.08, follaje="hoja_pequena", densidad=0.9, zona=0.9, tamano=2.2, hacia_arriba=0.3),
        dict(n=(2, 3), pos=(0.4, 1.0), angulo=45, largo=0.45, caida=0.1, grosor=0.6,
             follaje="hoja_pequena", densidad=1.1, zona=1.0, tamano=2.2, hacia_arriba=0.3),
    ], 101)


def platano():
    """Plátano de sombra: tronco recto y alto que se abre en una copa ancha de hoja grande palmeada."""
    return _especie("platano", dict(altura=520, grosor=30, estrechamiento=0.3, curvatura=0.05,
                                    raices=0.5, irregularidad=0.2, nudos=2), [
        dict(n=6, pos=(0.45, 1.0), angulo=45, angulo_punta=-15, largo=0.95, perfil="redondo", caida=0.2,
             curvatura=0.15, grosor=0.6, irregularidad=0.2, tortuoso=0.08, var_angulo=10),
        dict(n=(3, 4), pos=(0.3, 0.95), angulo=50, largo=0.5, caida=0.35, curvatura=0.1, grosor=0.6,
             tortuoso=0.06, follaje="hoja_palmeada", densidad=0.8, zona=0.5, tamano=2.0, hacia_arriba=0.45),
        dict(n=2, pos=(0.5, 0.95), angulo=45, largo=0.45, caida=0.4, grosor=0.6,
             follaje="hoja_palmeada", densidad=1.2, zona=0.95, tamano=2.0, hacia_arriba=0.45),
    ], 103)


def chopo():
    """Columna alta y esbelta de ramas que suben pegadas al tronco, con hoja redonda."""
    return _especie("chopo", dict(altura=1250, grosor=24, estrechamiento=0.15, curvatura=0.04,
                                  raices=0.4, irregularidad=0.2, nudos=2), [
        dict(n=26, pos=(0.12, 0.97), angulo=24, largo=0.2, perfil="huso", caida=0.05, curvatura=0.3,
             grosor=0.35, estrechamiento=0.15, var_angulo=6, tortuoso=0.05),
        dict(n=(2, 3), pos=(0.3, 1.0), angulo=40, largo=0.5, caida=0.3, grosor=0.6,
             follaje="hoja_redonda", densidad=1.3, zona=0.9, tamano=1.3, hacia_arriba=0.4),
    ], 107)


def castano():
    """Tronco grueso y retorcido, copa enorme y redonda de hoja larga."""
    return _especie("castano", dict(altura=380, grosor=42, estrechamiento=0.4, inclinacion=4, curvatura=0.12,
                                    raices=0.7, irregularidad=0.5, nudos=4, torsion=60), [
        dict(n=6, pos=(0.45, 1.0), angulo=50, angulo_punta=-20, largo=1.15, perfil="redondo", caida=0.15,
             curvatura=0.15, grosor=0.62, irregularidad=0.4, nudos=2, torsion=40, var_angulo=10, tortuoso=0.1),
        dict(n=(3, 4), pos=(0.3, 0.95), angulo=48, largo=0.5, caida=0.3, curvatura=0.1, grosor=0.6,
             tortuoso=0.08, follaje="hoja_castano", densidad=0.8, zona=0.5, tamano=1.8, hacia_arriba=0.4),
        dict(n=2, pos=(0.45, 0.95), angulo=45, largo=0.45, caida=0.35, grosor=0.6,
             follaje="hoja_castano", densidad=1.2, zona=0.95, tamano=1.8, hacia_arriba=0.4),
    ], 109)


def arce():
    """Tronco recto, copa ovalada y regular de hoja palmeada."""
    return _especie("arce", dict(altura=430, grosor=22, estrechamiento=0.3, curvatura=0.06,
                                 raices=0.4, irregularidad=0.2, nudos=2), [
        dict(n=7, pos=(0.4, 0.97), angulo=40, angulo_punta=-12, largo=0.75, perfil="ovalado", caida=0.15,
             curvatura=0.2, grosor=0.55, irregularidad=0.15, tortuoso=0.07, var_angulo=10),
        dict(n=(3, 4), pos=(0.3, 0.95), angulo=48, largo=0.5, caida=0.3, grosor=0.6, tortuoso=0.06,
             follaje="hoja_palmeada", densidad=0.9, zona=0.5, tamano=1.5, hacia_arriba=0.45),
        dict(n=2, pos=(0.45, 0.95), angulo=45, largo=0.45, caida=0.35, grosor=0.6,
             follaje="hoja_palmeada", densidad=1.3, zona=0.95, tamano=1.5, hacia_arriba=0.45),
    ], 113)


def arce_otono():
    """El arce con las texturas de otoño."""
    arbol = arce()
    arbol.nombre = arbol.material = "arce_otono"
    return arbol


def alcornoque():
    """Como la encina, pero con el tronco grueso de corcho y la copa algo más abierta."""
    return _especie("alcornoque", dict(altura=270, grosor=40, estrechamiento=0.45, inclinacion=7, curvatura=0.2,
                                       raices=0.7, irregularidad=0.6, nudos=5, torsion=35), [
        dict(n=6, pos=(0.55, 1.0), angulo=55, angulo_punta=-18, largo=1.1, perfil="redondo", caida=0.12,
             curvatura=0.2, grosor=0.68, irregularidad=0.5, nudos=2, torsion=30, var_angulo=12, tortuoso=0.14),
        dict(n=(3, 4), pos=(0.3, 1.0), angulo=50, largo=0.5, caida=0.25, curvatura=0.1, grosor=0.6,
             tortuoso=0.08, follaje="hoja_pequena", densidad=1.1, zona=0.8, tamano=1.5, hacia_arriba=0.5),
        dict(n=(2, 3), pos=(0.4, 1.0), angulo=45, largo=0.5, caida=0.3, grosor=0.6,
             follaje="hoja_pequena", densidad=1.6, zona=0.95, tamano=1.5, hacia_arriba=0.5),
    ], 127)


def arbol_seco():
    """Árbol muerto: tronco torcido y ramas nudosas que se quiebran en ángulos, sin una hoja."""
    return _especie("arbol_seco", dict(altura=400, grosor=30, estrechamiento=0.45, inclinacion=8, curvatura=0.2,
                                       raices=0.7, irregularidad=0.7, nudos=7, torsion=50), [
        dict(n=6, pos=(0.4, 1.0), angulo=45, angulo_punta=-18, largo=0.8, perfil="redondo", caida=0.05,
             curvatura=0.1, grosor=0.62, irregularidad=0.5, nudos=3, torsion=40, var_angulo=14, tortuoso=0.11),
        dict(n=(2, 3), pos=(0.3, 0.95), angulo=48, largo=0.5, caida=0.05, grosor=0.55, irregularidad=0.3,
             nudos=1, var_angulo=14, tortuoso=0.09),
        dict(n=(2, 3), pos=(0.4, 0.95), angulo=42, largo=0.42, caida=0.08, grosor=0.55, var_angulo=16,
             tortuoso=0.08),
    ], 131)


def almendro():
    """Almendro en flor: tronco corto y torcido, copa abierta en vaso de ramitas finas cubiertas de flores."""
    return _especie("almendro", dict(altura=150, grosor=17, estrechamiento=0.45, inclinacion=8, curvatura=0.2,
                                     raices=0.5, irregularidad=0.5, nudos=3, torsion=40), [
        dict(n=4, pos=(0.7, 1.0), angulo=38, largo=1.9, caida=0.1, curvatura=0.15, grosor=0.62,
             irregularidad=0.35, nudos=1, torsion=30, var_angulo=10, tortuoso=0.12),
        dict(n=(3, 4), pos=(0.3, 0.95), angulo=42, largo=0.5, caida=0.15, curvatura=0.1, grosor=0.55,
             tortuoso=0.1, follaje="flor", densidad=1.3, zona=0.75, tamano=1.1, hacia_arriba=0.6),
        dict(n=(3, 4), pos=(0.3, 1.0), angulo=40, largo=0.45, caida=0.2, grosor=0.55,
             follaje="flor", densidad=1.35, zona=0.95, tamano=1.1, hacia_arriba=0.6),
    ], 137)


def palmera():
    """Palmera: tronco alto, recto y sin ramas, con un penacho de hojas largas y arqueadas llenas de foliolos."""
    return _especie("palmera", dict(altura=800, grosor=26, estrechamiento=0.08, inclinacion=5, curvatura=0.1,
                                    raices=0.3, irregularidad=0.12), [
        dict(n=18, pos=(0.94, 1.0), angulo=105, angulo_punta=-85, largo=0.4, caida=0.45, curvatura=0.3,
             grosor=0.22, estrechamiento=0.15, irregularidad=0.05, var_angulo=8,
             follaje="foliolo", densidad=1.0, zona=0.85, tamano=1.0, hacia_arriba=0.0),
    ], 139)


ESPECIES = {
    "roble": roble,
    "haya": haya,
    "pino_pinonero": pino_pinonero,
    "abeto": abeto,
    "abedul": abedul,
    "sauce_lloron": sauce_lloron,
    "cipres": cipres,
    "olivo": olivo,
    "arbusto": arbusto,
    "encina": encina,
    "platano": platano,
    "chopo": chopo,
    "castano": castano,
    "arce": arce,
    "arce_otono": arce_otono,
    "alcornoque": alcornoque,
    "arbol_seco": arbol_seco,
    "almendro": almendro,
    "palmera": palmera,
}
