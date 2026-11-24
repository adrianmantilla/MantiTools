"""Follaje: grupos de hojas prefabricados y dónde se cuelgan de cada rama.

Los grupos de hojas son piezas fijas que trae el plugin, modeladas aquí en
código para no depender de archivos externos. En Maya las hojas de cada rama
son una sola malla (todas sus copias del grupo juntas): así se borran y
rehacen sin problemas al editar, y plantar el árbol entero como instancia
(fase 3) es lo que ahorra memoria en el jardín.
El eje Y del grupo apunta hacia fuera de la rama; el origen es donde se
engancha. Tamaño de referencia: unos 55 cm.
"""

import math
import random

from arboles import vectores as v
from arboles.modulos import Malla

# tipo: (hojas, largo de hoja, ancho, largo del tallito, apertura en grados, curvatura de la hoja,
#        redondez del contorno (más bajo = más redonda), disposición, forma)
# disposición «espiral»: hojas alrededor del tallito; «plano»: a los dos lados, como una pluma.
# forma: «ovalada», «lanceolada» (estrecha y en punta), «triangular» (ancha abajo y en punta),
#        «lobulada» (tres lóbulos por lado, como el roble), «palmeada» (ancha, con lóbulos en punta,
#        como el arce) o «aguja» (tira fina y plana: pocas caras).
TIPOS = {
    "hoja_ancha": (12, 15.0, 9.5, 42.0, 60.0, 0.35, 0.7, "espiral", "ovalada"),      # haya
    "hoja_roble": (11, 17.0, 10.5, 42.0, 60.0, 0.3, 0.6, "espiral", "lobulada"),     # roble
    "hoja_fina": (14, 17.0, 3.2, 44.0, 45.0, 0.5, 0.7, "espiral", "lanceolada"),     # sauce, olivo
    "hoja_redonda": (16, 8.5, 8.0, 40.0, 65.0, 0.25, 0.4, "espiral", "triangular"),  # abedul, álamo
    "hoja_grande": (6, 30.0, 17.0, 30.0, 55.0, 0.4, 0.6, "espiral", "ovalada"),      # magnolio, catalpa
    "hoja_palmeada": (7, 20.0, 19.0, 34.0, 58.0, 0.3, 0.5, "espiral", "palmeada"),   # arce, plátano de sombra
    "hoja_castano": (7, 26.0, 8.0, 34.0, 55.0, 0.35, 0.7, "espiral", "lanceolada"),  # castaño
    "hoja_pequena": (18, 6.5, 3.8, 34.0, 62.0, 0.15, 0.6, "espiral", "ovalada"),     # encina, boj
    "plumosa": (18, 13.0, 3.5, 48.0, 75.0, 0.2, 0.8, "plano", "lanceolada"),         # acacia, fresno
    "escama": (40, 8.0, 2.6, 46.0, 34.0, 0.05, 0.9, "plano", "aguja"),               # ciprés, tuya
    "aguja": (36, 12.0, 1.4, 20.0, 70.0, 0.1, 0.7, "espiral", "aguja"),              # pinos en general
    "pinocha": (34, 15.0, 1.6, 9.0, 82.0, 0.18, 0.7, "espiral", "aguja"),            # pino piñonero: borla
    "aguja_corta": (44, 8.0, 1.5, 44.0, 62.0, 0.12, 0.8, "espiral", "aguja"),        # abeto: escobilla
    "foliolo": (24, 46.0, 3.4, 30.0, 68.0, 0.3, 0.7, "pluma", "foliolo"),            # palmera: tramo de hoja
    "flor": (30, 3.6, 3.3, 12.0, 80.0, 0.0, 0.3, "flores", "petalo"),               # almendro, cerezo: seis flores
}
# «pluma»: los grupos se encadenan a lo largo de la rama (el nervio de la hoja de palmera), con
# foliolos a los dos lados; cada grupo mide lo mismo que la separación entre grupos.
# Agujas, foliolos y pétalos son tiras estrechas: dos columnas y la mitad de filas.
_TIRAS = ("aguja", "foliolo", "petalo")

# --- hojas propias del alumno ----------------------------------------------------------
# Un tipo «propia:<nombre>» usa una malla hecha por el alumno («Usar como hoja» en el editor),
# repetida en espiral como la hoja ancha. La malla se guarda normalizada: el tallo en el
# origen, la hoja a lo largo de +Y con largo 1, el ancho en X y el grosor en Z. Cada receta
# que la usa lleva una copia (Arbol.a_dict), así el árbol funciona en cualquier ordenador.
PROPIA = "propia:"
HOJAS_PROPIAS = {}
MAXIMO_TRIANGULOS_HOJA = 400  # por hoja: un grupo lleva 10 y un árbol cientos de grupos
_TIPO_PROPIA = (10, 15.0, 15.0, 40.0, 60.0, 0.0, 0.7, "espiral", "propia")


def es_propia(tipo):
    return isinstance(tipo, str) and tipo.startswith(PROPIA)


def datos_tipo(tipo):
    return _TIPO_PROPIA if es_propia(tipo) else TIPOS[tipo]


def normalizar_hoja(vertices, caras, uvs=None, uv_caras=None):
    """Datos de una hoja propia a partir de una malla en cualquier postura.

    ``caras``: listas de índices de vértice; ``uvs``/``uv_caras``: sus UV por esquina (opcional).
    El lado más largo de la malla es el largo de la hoja y su extremo más bajo es el tallo;
    el siguiente es el ancho. Si no hay UV, se proyectan de frente.
    """
    if not vertices or not caras:
        raise ValueError("la malla está vacía")
    triangulos = sum(len(c) - 2 for c in caras)
    if triangulos > MAXIMO_TRIANGULOS_HOJA:
        raise ValueError("la hoja tiene {} triángulos (como mucho {})".format(triangulos, MAXIMO_TRIANGULOS_HOJA))
    minimo = [min(p[i] for p in vertices) for i in range(3)]
    maximo = [max(p[i] for p in vertices) for i in range(3)]
    medidas = [maximo[i] - minimo[i] for i in range(3)]
    largo_eje, ancho_eje, grosor_eje = sorted(range(3), key=lambda i: -medidas[i])
    largo = medidas[largo_eje]
    if largo <= 1e-9:
        raise ValueError("la malla no tiene tamaño")
    centro = [(maximo[i] + minimo[i]) / 2.0 for i in range(3)]
    # Al cambiar los ejes de sitio la hoja podría quedar del revés: se corrige con el grosor.
    signo = 1.0 if (largo_eje - ancho_eje) % 3 == 1 else -1.0
    puntos = [((p[ancho_eje] - centro[ancho_eje]) / largo, (p[largo_eje] - minimo[largo_eje]) / largo,
               signo * (p[grosor_eje] - centro[grosor_eje]) / largo) for p in vertices]
    if not uvs or not uv_caras:
        uvs = [(x + 0.5, y) for x, y, _ in puntos]
        uv_caras = [list(c) for c in caras]
    uvs = [(min(1.0, max(0.0, u)), min(1.0, max(0.0, w))) for u, w in uvs]
    return {"vertices": [list(p) for p in puntos], "caras": [list(c) for c in caras],
            "uvs": [list(u) for u in uvs], "uv_caras": [list(c) for c in uv_caras]}


def registrar_hoja(nombre, datos):
    """Deja disponible la hoja propia ``nombre`` (tipo «propia:<nombre>»)."""
    HOJAS_PROPIAS[nombre] = datos
    for clave in [c for c in _CACHE if c[0] == PROPIA + nombre]:
        del _CACHE[clave]
    return PROPIA + nombre


def _hoja_propia(m, origen, eje, lado, largo, datos, cuadro):
    """Añade a ``m`` la hoja propia, del tallo en ``origen`` hacia ``eje`` (sin deformarla)."""
    cu, cv = (cuadro % 2) * 0.5, (cuadro // 2) * 0.5
    normal = v.unitario(v.cruz(eje, lado)) or v.perpendicular(eje)
    base, base_uv = len(m.vertices), len(m.us)
    for x, y, z in datos["vertices"]:
        m.vertices.append(v.suma(origen, v.suma(v.escala(eje, y * largo),
                                               v.suma(v.escala(lado, x * largo), v.escala(normal, z * largo)))))
    for u, w in datos["uvs"]:
        m.us.append(cu + u * 0.5)
        m.vs.append(cv + w * 0.5)
    for cara, uv_cara in zip(datos["caras"], datos["uv_caras"]):
        m.conteos.append(len(cara))
        m.conexiones += [base + i for i in cara]
        m.uv_ids += [base_uv + i for i in uv_cara]
# calidad: filas a lo largo de cada hoja (las agujas usan la mitad)
CALIDADES = {"alta": 6, "baja": 2}
_DORADO = math.radians(137.5)


def calidad_de_nivel(nivel):
    return "alta" if nivel in ("denso", "alto") else "baja"


def contorno(forma, t, redondez=0.7, filas=6):
    """Medio ancho relativo (0-1) de la hoja a la altura t (0 en el tallo, 1 en la punta)."""
    base = math.sin(math.pi * min(0.98, 0.08 + t * 0.92)) ** redondez
    if forma == "lanceolada":
        return base * (1.0 - 0.35 * t)
    if forma == "triangular":  # ancha cerca de la base y terminada en punta
        return math.sin(math.pi * min(0.97, 0.05 + 0.95 * t ** 0.75))
    if forma == "palmeada":  # ancha hacia la base, con lóbulos en punta y entrantes hondos
        ancho = math.sin(math.pi * min(0.97, 0.05 + 0.95 * t ** 0.6))
        k = int(round(t * filas))
        if filas >= 4 and 0 < k < filas:
            ancho *= 1.0 if k % 2 else 0.45
        return ancho
    if forma == "petalo":  # redondo, estrecho en la uña
        return math.sin(math.pi * min(0.97, 0.06 + 0.9 * t)) ** 0.4
    if forma == "foliolo":  # largo y estrecho, en punta
        return (1.0 - t ** 2) ** 0.5 * min(1.0, 0.4 + 3.0 * t)
    if forma == "lobulada" and filas >= 4:
        # Filas impares: lóbulo; pares: entrante. Tres lóbulos por lado con 6 filas.
        k = int(round(t * filas))
        return base * (1.0 if k % 2 else 0.55) if 0 < k < filas else base
    return base


def _hoja(m, origen, eje, lado, largo, ancho, curva, filas, redondez=0.7, cuadro=0, forma="ovalada"):
    """Añade a ``m`` una hoja doblada por el nervio, de ``origen`` hacia ``eje``.

    La textura de hoja lleva cuatro variantes de color en 2x2; ``cuadro`` (0-3) dice cuál usa.
    Las agujas son una tira plana (una cara por fila) y con la mitad de filas.
    """
    cu, cv = (cuadro % 2) * 0.5, (cuadro // 2) * 0.5
    columnas = (-1.0, 1.0) if forma in _TIRAS else (-1.0, 0.0, 1.0)
    if forma in _TIRAS:
        filas = max(1, filas // 2)
    n = len(columnas)
    normal = v.unitario(v.cruz(eje, lado)) or v.perpendicular(eje)
    base = len(m.vertices)
    base_uv = len(m.us)
    for k in range(filas + 1):
        t = k / float(filas)
        perfil = contorno(forma, t, redondez, filas)
        if forma == "aguja":
            perfil = 1.0 - 0.6 * t * t  # casi del mismo ancho hasta la punta
        centro = v.suma(origen, v.suma(v.escala(eje, largo * t), v.escala(normal, -curva * largo * t * t)))
        for x in columnas:
            pliegue = 0.12 * ancho * (1.0 - abs(x)) * perfil  # el nervio un poco levantado
            p = v.suma(centro, v.suma(v.escala(lado, x * ancho * 0.5 * perfil), v.escala(normal, pliegue)))
            m.vertices.append(p)
            m.us.append(cu + (x + 1.0) * 0.25)
            m.vs.append(cv + t * 0.5)
    for k in range(filas):
        for j in range(n - 1):
            a = base + k * n + j
            m.conteos.append(4)
            m.conexiones += [a, a + 1, a + 1 + n, a + n]
            u = base_uv + k * n + j
            m.uv_ids += [u, u + 1, u + 1 + n, u + n]


def prototipo(tipo, calidad="alta"):
    """Malla del grupo de hojas ``tipo`` en espacio local."""
    hojas, largo, ancho, tallo, apertura, curva, redondez, disposicion, forma = datos_tipo(tipo)
    if forma == "propia" and tipo[len(PROPIA):] not in HOJAS_PROPIAS:
        forma = "ovalada"  # la hoja no está en este ordenador: se ve una hoja normal en su lugar
    filas = CALIDADES[calidad]
    m = Malla("{}_{}".format(tipo, calidad))
    azar = random.Random(len(tipo) * 7919)
    apertura = math.radians(apertura)
    if disposicion == "flores":
        # Flores de cinco pétalos abiertas en un punto, repartidas alrededor del tallito y mirando afuera.
        flores = max(1, hojas // 5)
        for k in range(flores):
            t = (k + 0.6) / flores
            a = k * _DORADO + azar.uniform(-0.3, 0.3)
            radial = (math.cos(a), 0.0, math.sin(a))
            centro = v.suma((0.0, tallo * t, 0.0), v.escala(radial, largo * 0.5))
            cara = v.unitario(v.suma(v.escala(v.ARRIBA, 0.7), radial))
            base = v.unitario(v.cruz(cara, v.perpendicular(cara)))
            for j in range(5):
                direccion = v.rotar(base, cara, j * 2.0 * math.pi / 5.0 + k * 0.45)
                eje = v.unitario(v.suma(v.escala(direccion, math.sin(apertura)), v.escala(cara, math.cos(apertura))))
                lado = v.unitario(v.cruz(cara, direccion)) or v.perpendicular(eje)
                escala = 1.0 + azar.uniform(-0.1, 0.1)
                _hoja(m, centro, eje, lado, largo * escala, ancho * escala, curva, filas, redondez,
                      azar.randrange(4), forma)
        return m
    for i in range(hojas):
        t = 0.25 + 0.75 * i / max(1, hojas - 1)
        if disposicion == "pluma":
            t, inclinacion = (i // 2 + 0.5) / ((hojas + 1) // 2), apertura
        elif i == hojas - 1:
            t, inclinacion = 1.0, 0.15
        else:
            inclinacion = apertura * (1.0 - 0.3 * t)
        if disposicion == "pluma":
            radial = v.unitario((1.0 if i % 2 else -1.0, 0.0, azar.uniform(-0.15, 0.15)))
            escala = 1.0 + azar.uniform(-0.06, 0.06)
        elif disposicion == "plano":
            radial = (1.0 if i % 2 else -1.0, 0.0, azar.uniform(-0.12, 0.12))
            radial = v.unitario(radial)
            escala = 1.0 - 0.45 * t * t + azar.uniform(-0.05, 0.05)  # más cortas hacia la punta
        else:
            azimut = i * _DORADO
            radial = (math.cos(azimut), 0.0, math.sin(azimut))
            escala = 0.75 + 0.25 * t + azar.uniform(-0.08, 0.08)
        eje = v.unitario(v.suma(v.escala(v.ARRIBA, math.cos(inclinacion)), v.escala(radial, math.sin(inclinacion))))
        lado = v.unitario(v.cruz(v.ARRIBA, radial)) or (1.0, 0.0, 0.0)
        if disposicion in ("plano", "pluma"):
            lado = v.unitario(v.cruz((0.0, 0.0, 1.0), eje)) or lado  # la hoja tumbada en el plano
        if forma == "propia":
            _hoja_propia(m, (0.0, tallo * t, 0.0), eje, lado, largo * escala, HOJAS_PROPIAS[tipo[len(PROPIA):]],
                         azar.randrange(4))
            continue
        _hoja(m, (0.0, tallo * t, 0.0), eje, lado, largo * escala, ancho * escala, curva, filas, redondez,
              azar.randrange(4), forma)
    return m


_CACHE = {}


def prototipo_cache(tipo, calidad):
    clave = (tipo, calidad)
    if clave not in _CACHE:
        _CACHE[clave] = prototipo(tipo, calidad)
    return _CACHE[clave]


def combinar(tipo, nivel, matrices, nombre="hojas"):
    """Una malla con una copia del grupo ``tipo`` por cada matriz (filas, como Maya)."""
    base = prototipo_cache(tipo, calidad_de_nivel(nivel))
    m = Malla(nombre)
    nv, nuv = len(base.vertices), len(base.us)
    for k, a in enumerate(matrices):
        for x, y, z in base.vertices:
            m.vertices.append((x * a[0] + y * a[4] + z * a[8] + a[12],
                               x * a[1] + y * a[5] + z * a[9] + a[13],
                               x * a[2] + y * a[6] + z * a[10] + a[14]))
        m.us += base.us
        m.vs += base.vs
        m.conteos += base.conteos
        m.conexiones += [i + k * nv for i in base.conexiones]
        m.uv_ids += [i + k * nuv for i in base.uv_ids]
    return m


def triangulos_prototipo(tipo, nivel):
    return prototipo_cache(tipo, calidad_de_nivel(nivel)).triangulos


def colocar(modulo):
    """Matrices 4x4 (filas, como las de Maya) de los grupos de hojas de una rama.

    Necesita la guía calculada. Devuelve una lista vacía si la rama no lleva follaje.
    """
    val = modulo.valores
    tipo = val.get("follaje", "ninguno")
    guia = modulo.guia
    if tipo == "ninguno" or guia is None or val["densidad"] <= 0:
        return []
    azar = random.Random(modulo.semilla)
    tamano = val["tamano_hoja"]
    inicio = 1.0 - val["zona"]
    separacion = 30.0 * tamano / max(val["densidad"], 0.05)
    cantidad = max(0, int(round(guia.largo * val["zona"] / separacion)))  # 0: solo el de la punta
    pluma = datos_tipo(tipo)[7] == "pluma"
    if pluma:  # tramos seguidos a lo largo de la rama, sin el grupo extra de la punta
        cantidad = max(1, int(round(guia.largo * val["zona"] / separacion)))
    matrices = []
    for i in range(cantidad if pluma else cantidad + 1):
        punta = i == cantidad
        if pluma:
            s = inicio + val["zona"] * i / float(cantidad)
        else:
            s = 1.0 if punta else min(1.0, inicio + (i + azar.random() * 0.8) / cantidad * val["zona"])
        t, n, b = guia.marco(s)
        if pluma:
            eje = t
            sitio = guia.punto(s)
        elif punta:
            eje = t
            sitio = guia.punto(1.0)
        else:
            angulo = i * _DORADO + azar.uniform(-0.4, 0.4)
            radial = v.suma(v.escala(n, math.cos(angulo)), v.escala(b, math.sin(angulo)))
            sitio = v.suma(guia.punto(s), v.escala(radial, guia.radio(s, angulo) * 0.7))
            eje = v.unitario(v.suma(v.escala(radial, 0.8), v.escala(t, 0.6)))
        eje = v.unitario(v.suma(v.escala(eje, 1.0 - val["hacia_arriba"]),
                                v.escala(v.ARRIBA, val["hacia_arriba"]))) or eje
        x = v.unitario(v.cruz(eje, v.perpendicular(eje)))
        if datos_tipo(tipo)[7] in ("plano", "pluma"):
            # Ramilletes planos tumbados de cara al cielo, como crecen para coger luz.
            x = v.unitario(v.cruz(eje, v.ARRIBA)) or x
            x = v.rotar(x, eje, azar.uniform(-0.45, 0.45))
        else:
            x = v.rotar(x, eje, azar.uniform(0.0, 2.0 * math.pi))
        z = v.cruz(x, eje)
        e = tamano * azar.uniform(0.8, 1.2)
        if pluma:  # foliolos más cortos en la base y en la punta de la hoja
            f = (s - inicio) / max(val["zona"], 1e-6)
            e = tamano * (0.55 + 0.45 * math.sin(math.pi * min(1.0, 0.15 + 0.85 * f)))
            matrices.append((
                x[0] * e, x[1] * e, x[2] * e, 0.0,
                eje[0] * tamano, eje[1] * tamano, eje[2] * tamano, 0.0,
                (x[1] * eje[2] - x[2] * eje[1]) * e, (x[2] * eje[0] - x[0] * eje[2]) * e,
                (x[0] * eje[1] - x[1] * eje[0]) * e, 0.0,
                sitio[0], sitio[1], sitio[2], 1.0))
            continue
        matrices.append((
            x[0] * e, x[1] * e, x[2] * e, 0.0,
            eje[0] * e, eje[1] * e, eje[2] * e, 0.0,
            z[0] * e, z[1] * e, z[2] * e, 0.0,
            sitio[0], sitio[1], sitio[2], 1.0))
    return matrices
