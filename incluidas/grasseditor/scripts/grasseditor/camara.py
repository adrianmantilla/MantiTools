"""Paso final del reparto: qué matas salen en el visor y cuáles en el render.

En el render se aplican el recorte por cámara (se descartan las matas fuera
del encuadre, con un margen), el detalle por distancia (mata completa, simple
o tarjeta) y el aclarado a lo lejos (se quitan matas lejanas y se agrandan
las que quedan). En el visor se muestra solo un porcentaje de las matas, con
la forma elegida (cajas, tarjetas o matas).

La salida son listas listas para el instanciador de Maya: posición, giro en
grados (X, Y, Z), escala y el índice del prototipo:
``hueco_de_tipo * 18 + variante * 3 + nivel``.

Python puro: se prueba sin Maya.
"""

import math
from array import array

from grasseditor.tipos import NIVELES, PROTOTIPOS_POR_TIPO

CERCA_SIEMPRE = 150.0     # cm: lo que está junto a la cámara no se recorta (sombras, suelo a los pies)
COMO = ("cajas", "tarjetas", "matas")


class Camara(object):
    """Cámara de render a partir de su matriz de mundo (Maya, por filas) y su apertura."""

    def __init__(self, matriz, focal=35.0, apertura_h=1.417, aspecto=16.0 / 9.0):
        m = [float(v) for v in matriz]
        self.pos = (m[12], m[13], m[14])
        self.eje_x = _unit(m[0:3])
        self.eje_y = _unit(m[4:7])
        self.eje_z = _unit(m[8:11])           # la cámara mira hacia -Z
        self.tan_h = (apertura_h * 25.4 / 2.0) / max(1e-3, focal)
        self.tan_v = self.tan_h / max(1e-3, aspecto)

    @property
    def fov_h(self):
        return math.degrees(2 * math.atan(self.tan_h))

    def ve(self, x, y, z, margen_grados=5.0):
        dx, dy, dz = x - self.pos[0], y - self.pos[1], z - self.pos[2]
        prof = -(dx * self.eje_z[0] + dy * self.eje_z[1] + dz * self.eje_z[2])
        if prof <= 0:
            return False
        lx = dx * self.eje_x[0] + dy * self.eje_x[1] + dz * self.eje_x[2]
        ly = dx * self.eje_y[0] + dy * self.eje_y[1] + dz * self.eje_y[2]
        th = math.tan(min(89.0, math.degrees(math.atan(self.tan_h)) + margen_grados) * math.pi / 180)
        tv = math.tan(min(89.0, math.degrees(math.atan(self.tan_v)) + margen_grados) * math.pi / 180)
        return abs(lx) <= th * prof and abs(ly) <= tv * prof


def _unit(v):
    l = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / l for c in v)


class Opciones(object):
    """Ajustes de rendimiento de una capa (los de la pestaña Rendimiento)."""

    CAMPOS = ("recorte", "margen", "lejos", "lod", "cerca", "medio", "aclarar", "aclarar_cantidad",
              "visor_porcentaje", "visor_como")

    def __init__(self, recorte=True, margen=10.0, lejos=0.0, lod=True, cerca=800.0, medio=2000.0,
                 aclarar=True, aclarar_cantidad=0.5, visor_porcentaje=10.0, visor_como="tarjetas"):
        self.recorte = bool(recorte)
        self.margen = float(margen)                 # grados de más a cada lado del encuadre
        self.lejos = float(lejos)                   # cm; 0 = sin límite
        self.lod = bool(lod)
        self.cerca = float(cerca)                   # cm: hasta aquí, mata completa
        self.medio = max(self.cerca, float(medio))  # cm: hasta aquí, simple; después, tarjeta
        self.aclarar = bool(aclarar)
        self.aclarar_cantidad = min(0.9, max(0.0, float(aclarar_cantidad)))
        self.visor_porcentaje = min(100.0, max(0.1, float(visor_porcentaje)))
        self.visor_como = visor_como if visor_como in COMO else "tarjetas"

    def a_dict(self):
        return {c: getattr(self, c) for c in self.CAMPOS}

    @classmethod
    def desde_dict(cls, datos):
        datos = datos or {}
        return cls(**{c: datos[c] for c in cls.CAMPOS if c in datos})


class Salida(object):
    def __init__(self):
        self.posiciones = []
        self.giros = []
        self.escalas = []
        self.indices = array("l")
        self.ids = array("l")

    def __len__(self):
        return len(self.indices)


def _nivel(d, opciones, ruido):
    if not opciones.lod:
        return 0
    d *= ruido
    if d < opciones.cerca:
        return 0
    return 1 if d < opciones.medio else 2


def recorrer(cand, aceptados, opciones, camara, render=True):
    """Genera (índice de candidata, nivel, escala extra) de las matas que salen.

    En modo visor no hay recorte ni aclarado: se queda el porcentaje del visor.
    """
    X, Y, Z, K1, K2 = cand.x, cand.y, cand.z, cand.k_visor, cand.k_aclarar
    if not render:
        fraccion = opciones.visor_porcentaje / 100.0
        fijo = 2 if opciones.visor_como == "tarjetas" else 0
        for i in aceptados:
            if K1[i] < fraccion:
                yield i, fijo, 1.0
        return
    recorte = opciones.recorte and camara is not None
    cx, cy, cz = camara.pos if camara is not None else (0.0, 0.0, 0.0)
    if recorte:
        th = math.tan(min(89.0, math.degrees(math.atan(camara.tan_h)) + opciones.margen) * math.pi / 180)
        tv = math.tan(min(89.0, math.degrees(math.atan(camara.tan_v)) + opciones.margen) * math.pi / 180)
        ex, ey, ez = camara.eje_x, camara.eje_y, camara.eje_z
    lejos = opciones.lejos if opciones.lejos > 0 else None
    usar_distancia = camara is not None
    aclarar = opciones.aclarar and opciones.aclarar_cantidad > 0 and usar_distancia
    medio = opciones.medio
    for i in aceptados:
        x, y, z = X[i], Y[i], Z[i]
        dx, dy, dz = x - cx, y - cy, z - cz
        d = math.sqrt(dx * dx + dy * dy + dz * dz) if usar_distancia else 0.0
        if recorte and d > CERCA_SIEMPRE:
            if lejos is not None and d > lejos:
                continue
            prof = -(dx * ez[0] + dy * ez[1] + dz * ez[2])
            if prof <= 0:
                continue
            if abs(dx * ex[0] + dy * ex[1] + dz * ex[2]) > th * prof:
                continue
            if abs(dx * ey[0] + dy * ey[1] + dz * ey[2]) > tv * prof:
                continue
        extra = 1.0
        if aclarar and d > medio:
            cantidad = opciones.aclarar_cantidad * min(1.0, (d - medio) / (0.5 * medio + 1.0))
            quedan = 1.0 - cantidad
            if K2[i] >= quedan:
                continue
            extra = (1.0 / quedan) ** 0.35
        nivel = _nivel(d, opciones, 0.9 + 0.2 * ((K1[i] * 7.31) % 1.0)) if usar_distancia else 0
        yield i, nivel, extra


def salida(cand, aceptados, opciones, camara=None, render=True):
    """Listas para el instanciador (ver el docstring del módulo)."""
    s = Salida()
    T, V, E, G, IX, IZ = cand.tipo, cand.variante, cand.escala, cand.giro, cand.incl_x, cand.incl_z
    X, Y, Z = cand.x, cand.y, cand.z
    pos, gir, esc, idx, ids = s.posiciones.append, s.giros.append, s.escalas.append, s.indices.append, s.ids.append
    for i, nivel, extra in recorrer(cand, aceptados, opciones, camara, render):
        pos((X[i], Y[i], Z[i]))
        gir((IX[i], G[i], IZ[i]))
        e = E[i] * extra
        esc((e, e, e))
        idx(T[i] * PROTOTIPOS_POR_TIPO + V[i] * NIVELES + nivel)
        ids(i)
    return s


def recuento(cand, aceptados, opciones, camara=None, render=True):
    """{(hueco de tipo, nivel): número de matas}, sin construir las listas."""
    cuenta = {}
    T = cand.tipo
    for i, nivel, _ in recorrer(cand, aceptados, opciones, camara, render):
        clave = (T[i], nivel)
        cuenta[clave] = cuenta.get(clave, 0) + 1
    return cuenta
