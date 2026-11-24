"""Generador de matas: de un tipo de hierba a mallas listas para instanciar.

Cada tipo da ``VARIANTES`` matas distintas (otra semilla y un tono algo
distinto) y cada mata tres niveles de detalle:

* 0 · completa: todas las briznas con todos sus segmentos (cerca de la cámara).
* 1 · simple: la mitad de briznas, más anchas, con la mitad de segmentos.
* 2 · tarjeta: dos tarjetas cruzadas con tres puntas cada una (6 triángulos).

Las mallas son triángulos sueltos (una cara por triángulo) con UVs (u a lo
ancho, v de la raíz a la punta) y un color por vértice que ya lleva el
degradado de la raíz a la punta. El material de Arnold lee ese color, así no
hace falta ninguna textura. La mata nace en el origen y crece hacia +Y.

Python puro: se prueba sin Maya.
"""

import math
import random

from grasseditor.tipos import NIVELES, VARIANTES

TRIANGULOS_TARJETA = 18


class Malla(object):
    def __init__(self):
        self.vertices = []
        self.colores = []
        self.uvs = []
        self.indices = []   # de tres en tres

    @property
    def conteos(self):
        return [3] * (len(self.indices) // 3)

    @property
    def triangulos(self):
        return len(self.indices) // 3

    def vertice(self, p, color, uv):
        self.vertices.append((float(p[0]), float(p[1]), float(p[2])))
        self.colores.append(tuple(min(1.0, max(0.0, c)) for c in color))
        self.uvs.append((float(uv[0]), float(uv[1])))
        return len(self.vertices) - 1

    def triangulo(self, a, b, c):
        self.indices.extend((a, b, c))

    def caja(self):
        xs, ys, zs = zip(*self.vertices) if self.vertices else ((0,), (0,), (0,))
        return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def _mezcla(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def _tono(color, factor, calido):
    """Aclara u oscurece ``color`` y lo mueve un poco hacia el amarillo (calido > 0)."""
    r, g, b = color
    return (r * factor * (1 + calido), g * factor * (1 + calido * 0.4), b * factor * (1 - calido))


def tono_variante(variante):
    """(factor de brillo, calidez) de cada variante: seis tonos repartidos."""
    paso = variante - (VARIANTES - 1) / 2.0
    return 1.0 + paso * 0.05, ((variante * 37) % 5 - 2) * 0.025


def _brizna(malla, base, azimut, inclinacion, curvatura, altura, anchura, segmentos, raiz, punta,
            girar_cara=0.0):
    """Una brizna: tira de quads que se estrecha y acaba en punta. Devuelve la posición de la punta.

    ``inclinacion`` (radianes) es lo que se separa de la vertical al nacer; la
    curvatura la va doblando más hacia fuera según sube.
    """
    dx, dz = math.cos(azimut), math.sin(azimut)
    # Eje lateral de la brizna (para su anchura), horizontal y perpendicular a la dirección.
    lx, lz = math.cos(azimut + math.pi / 2 + girar_cara), math.sin(azimut + math.pi / 2 + girar_cara)
    paso = altura / segmentos
    x, y, z = base
    angulo = inclinacion
    puntos = [(x, y, z)]
    for _ in range(segmentos):
        h = math.sin(angulo) * paso
        x, y, z = x + dx * h, y + math.cos(angulo) * paso, z + dz * h
        puntos.append((x, y, z))
        angulo = min(math.radians(88), angulo + curvatura * math.radians(70) / segmentos)
    filas = []
    for i, p in enumerate(puntos[:-1]):
        t = i / float(segmentos)
        media = anchura * 0.5 * (1.0 - t ** 1.4 * 0.85)
        color = _mezcla(raiz, punta, t ** 0.8)
        izq = malla.vertice((p[0] - lx * media, p[1], p[2] - lz * media), color, (0.0, t))
        der = malla.vertice((p[0] + lx * media, p[1], p[2] + lz * media), color, (1.0, t))
        filas.append((izq, der))
    pico = malla.vertice(puntos[-1], punta, (0.5, 1.0))
    for (a, b), (c, d) in zip(filas, filas[1:]):
        malla.triangulo(a, b, d)
        malla.triangulo(a, d, c)
    a, b = filas[-1]
    malla.triangulo(a, b, pico)
    return puntos[-1], (dx, dz)


def _flor(malla, centro, radio, color_petalo, color_centro, rnd, copa=0.0):
    """Disco de 8 pétalos (8 triángulos) mirando hacia arriba; con ``copa`` se cierra como una amapola."""
    giro = rnd.uniform(0, math.pi)
    medio = malla.vertice((centro[0], centro[1] - radio * copa * 0.3, centro[2]), color_centro, (0.5, 0.5))
    anillo = []
    for i in range(8):
        a = giro + i * math.pi / 4
        r = radio * (1.0 if i % 2 == 0 else 0.8)
        anillo.append(malla.vertice((centro[0] + math.cos(a) * r, centro[1] + radio * copa,
                                     centro[2] + math.sin(a) * r), color_petalo,
                                    (0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a))))
    for i in range(8):
        malla.triangulo(medio, anillo[(i + 1) % 8], anillo[i])
    return 8


def _espiga(malla, centro, direccion, largo, ancho, color, rnd):
    """Espiga: dos rombos cruzados a lo largo de la punta del tallo (4 triángulos)."""
    dx, dz = direccion
    arriba = (centro[0] + dx * largo * 0.25, centro[1] + largo, centro[2] + dz * largo * 0.25)
    medio_y = centro[1] + largo * 0.45
    giro = rnd.uniform(0, math.pi)
    oscuro = _tono(color, 0.8, 0.0)
    for k in range(2):
        a = giro + k * math.pi / 2
        ox, oz = math.cos(a) * ancho * 0.5, math.sin(a) * ancho * 0.5
        mx, mz = centro[0] + dx * largo * 0.1, centro[2] + dz * largo * 0.1
        v0 = malla.vertice(centro, oscuro, (0.5, 0.0))
        v1 = malla.vertice((mx - ox, medio_y, mz - oz), color, (0.0, 0.5))
        v2 = malla.vertice((mx + ox, medio_y, mz + oz), color, (1.0, 0.5))
        v3 = malla.vertice(arriba, color, (0.5, 1.0))
        malla.triangulo(v0, v2, v1)
        malla.triangulo(v1, v2, v3)
    return 4


def _trebol(malla, centro, radio, color, rnd):
    """Tres hojitas redondas (4 triángulos cada una) a 120°, casi horizontales."""
    giro = rnd.uniform(0, 2 * math.pi)
    claro = _tono(color, 1.12, 0.0)
    for k in range(3):
        a = giro + k * 2 * math.pi / 3
        base = malla.vertice(centro, color, (0.5, 0.0))
        borde = []
        for j in range(5):
            b = a - math.radians(70) + j * math.radians(35)
            r = radio * (0.75 if j in (0, 4) else 1.0)
            borde.append(malla.vertice((centro[0] + math.cos(b) * r, centro[1] + radio * 0.15,
                                        centro[2] + math.sin(b) * r), claro, (j / 4.0, 1.0)))
        for j in range(4):
            malla.triangulo(base, borde[j + 1], borde[j])
    return 12


def mata(tipo, variante=0, nivel=0, semilla=0):
    """La malla de una mata de ``tipo`` (variante 0-5, nivel de detalle 0-2)."""
    if nivel >= 2:
        return tarjeta(tipo, variante)
    rnd = random.Random(_semilla(tipo.clave, variante, semilla))
    brillo, calido = tono_variante(variante)
    raiz = _tono(tipo.color_raiz, brillo, calido)
    punta = _tono(tipo.color_punta, brillo, calido)
    malla = Malla()
    briznas = tipo.briznas
    segmentos = tipo.segmentos
    anchura = tipo.anchura
    if nivel == 1:
        briznas = max(1, (briznas + 1) // 2)
        segmentos = max(1, segmentos // 2) if segmentos > 2 else segmentos
        anchura *= 1.4
    cabezas = min(tipo.cabezas, briznas) if tipo.cabeza else 0
    if nivel == 1 and tipo.cabeza:
        cabezas = max(1, (tipo.cabezas + 1) // 2) if tipo.cabeza != "trebol" else briznas
    altura = tipo.altura
    for i in range(briznas):
        r = tipo.radio * math.sqrt(rnd.random())
        a = rnd.uniform(0, 2 * math.pi)
        base = (math.cos(a) * r, 0.0, math.sin(a) * r)
        azimut = a + rnd.uniform(-0.6, 0.6)
        con_cabeza = i < cabezas
        alto = altura * rnd.uniform(0.7, 1.15)
        if con_cabeza and tipo.cabeza in ("flor", "espiga"):
            alto = altura * rnd.uniform(1.0, 1.2)   # el tallo sobresale
        incl = math.radians(tipo.abertura) * (r / tipo.radio if tipo.radio else 0.5) * rnd.uniform(0.6, 1.2)
        curv = tipo.curvatura * rnd.uniform(0.7, 1.3)
        if con_cabeza:
            curv *= 0.35
            incl *= 0.5
        sombra = rnd.uniform(0.92, 1.06)
        c_raiz = tuple(c * sombra for c in raiz)
        c_punta = tuple(c * sombra for c in punta)
        ancho = anchura * (0.5 if con_cabeza and tipo.cabeza != "trebol" else 1.0) * rnd.uniform(0.8, 1.2)
        segs = segmentos
        if tipo.cabeza == "trebol" and con_cabeza:
            alto = altura * rnd.uniform(0.5, 0.9)
        pico, direccion = _brizna(malla, base, azimut, incl, curv, alto, ancho, segs, c_raiz, c_punta,
                                  girar_cara=rnd.uniform(-0.3, 0.3))
        if not con_cabeza:
            continue
        if tipo.cabeza == "flor":
            amapola = tipo.color_cabeza2 and variante >= VARIANTES // 2
            petalo = tipo.color_cabeza2 if amapola else tipo.color_cabeza
            centro = (0.10, 0.08, 0.06) if amapola else (0.95, 0.75, 0.10)
            _flor(malla, pico, altura * 0.09, petalo, centro, rnd, copa=0.6 if amapola else 0.1)
        elif tipo.cabeza == "espiga":
            _espiga(malla, pico, direccion, altura * 0.22, altura * 0.05, _tono(tipo.color_cabeza, brillo, calido),
                    rnd)
        elif tipo.cabeza == "trebol":
            _trebol(malla, pico, max(0.8, altura * 0.16), _tono(tipo.color_cabeza, brillo, calido), rnd)
    return malla


def tarjeta(tipo, variante=0):
    """Nivel lejano: dos tarjetas cruzadas con tres puntas dobladas cada una (18 triángulos).

    Cada punta tiene un codo a media altura que se inclina hacia fuera, para
    que de cerca no parezca un triángulo plano.
    """
    brillo, calido = tono_variante(variante)
    raiz = _tono(tipo.color_raiz, brillo, calido)
    punta = _tono(tipo.color_punta, brillo, calido)
    if tipo.cabeza in ("flor", "espiga"):
        punta = _mezcla(punta, tipo.color_cabeza2 if (tipo.cabeza == "flor" and tipo.color_cabeza2
                                                     and variante >= VARIANTES // 2) else tipo.color_cabeza,
                        0.35)
    medio_color = _mezcla(raiz, punta, 0.5)
    malla = Malla()
    ancho = max(tipo.radio * 2.0, tipo.altura * 0.35) * 1.1
    alto = tipo.altura
    giro = (variante * 0.61) % math.pi
    caida = 0.12 + 0.35 * tipo.curvatura          # cuánto se inclina la punta (en fracción de la altura)
    for k in range(2):
        a = giro + k * math.pi / 2
        ex, ez = math.cos(a), math.sin(a)          # a lo ancho de la tarjeta
        nx, nz = -ez, ex                           # perpendicular: hacia donde se dobla
        for j in range(3):
            u0, u1 = j / 3.0, (j + 1) / 3.0
            x0, x1 = (u0 - 0.5) * ancho, (u1 - 0.5) * ancho
            xm = (x0 + x1) / 2 + (j - 1) * ancho * 0.08
            h = alto * (1.0 if j == 1 else 0.82)
            lado = 1.0 if (j + k + variante) % 2 else -1.0
            dobla = lado * caida * h
            # codo a media altura: más estrecho y algo desplazado
            c0 = x0 + (xm - x0) * 0.45
            c1 = x1 + (xm - x1) * 0.45
            hc = h * 0.55
            dc = dobla * 0.3
            v0 = malla.vertice((ex * x0, 0.0, ez * x0), raiz, (u0, 0.0))
            v1 = malla.vertice((ex * x1, 0.0, ez * x1), raiz, (u1, 0.0))
            v2 = malla.vertice((ex * c0 + nx * dc, hc, ez * c0 + nz * dc), medio_color, (u0 + (u1 - u0) * 0.22, 0.55))
            v3 = malla.vertice((ex * c1 + nx * dc, hc, ez * c1 + nz * dc), medio_color, (u1 - (u1 - u0) * 0.22, 0.55))
            v4 = malla.vertice((ex * xm + nx * dobla, h * 0.95, ez * xm + nz * dobla), punta, ((u0 + u1) / 2, 1.0))
            malla.triangulo(v0, v1, v3)
            malla.triangulo(v0, v3, v2)
            malla.triangulo(v2, v3, v4)
    return malla


def _semilla(clave, variante, semilla):
    # hash() de Python cambia entre sesiones con las cadenas: se usa uno propio y estable.
    h = 2166136261
    for ch in "{}|{}|{}".format(clave, variante, semilla):
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return h


def triangulos_por_nivel(tipo):
    """[completa, simple, tarjeta]: triángulos de una mata (media de las variantes)."""
    resultado = []
    for nivel in range(NIVELES):
        total = sum(mata(tipo, v, nivel).triangulos for v in range(VARIANTES))
        resultado.append(int(round(total / float(VARIANTES))))
    return resultado
