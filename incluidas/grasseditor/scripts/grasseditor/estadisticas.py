"""Cifras de la escena, semáforo y consejos (la parte de enseñar a optimizar).

Las cifras de memoria son una estimación para comparar: el instanciador
guarda la geometría de cada prototipo una vez y, por cada mata, su posición,
giro y escala. Sin instancias, cada triángulo de cada mata ocuparía memoria.

Python puro: se prueba sin Maya.
"""

from grasseditor.tipos import VARIANTES

BYTES_POR_MATA = 120        # matriz y datos de una instancia en Arnold, aprox.
BYTES_POR_TRIANGULO = 45    # vértices, normales, UVs y colores, aprox.

# Triángulos que calcula Arnold en el render: verde, ámbar, rojo
SEMAFORO = ((4000000, "verde"), (10000000, "ambar"))


def semaforo(triangulos):
    for limite, color in SEMAFORO:
        if triangulos < limite:
            return color
    return "rojo"


class Informe(object):
    """Resumen de una capa o de toda la escena."""

    def __init__(self):
        self.matas = 0
        self.triangulos = 0
        self.descartadas = 0          # fuera de la cámara o aclaradas
        self.posibles = 0             # las que habría sin recorte ni aclarado
        self.unicos = 0               # triángulos de los prototipos usados
        self.visor = 0                # matas que dibuja el visor
        self.por_tipo = {}            # clave -> triángulos en render
        self.por_capa = {}            # capa -> triángulos en render
        self.recortadas = False       # se llegó al máximo de candidatas
        self.opciones = {}            # recorte, lod, aclarar y visor de la capa (para consejos)

    @property
    def memoria(self):
        """Bytes aproximados con instancias."""
        return self.matas * BYTES_POR_MATA + self.unicos * BYTES_POR_TRIANGULO

    @property
    def memoria_sin_instancias(self):
        return self.triangulos * BYTES_POR_TRIANGULO

    @property
    def color(self):
        return semaforo(self.triangulos)

    def sumar(self, otro, nombre=None):
        self.matas += otro.matas
        self.triangulos += otro.triangulos
        self.descartadas += otro.descartadas
        self.posibles += otro.posibles
        self.visor += otro.visor
        self.recortadas = self.recortadas or otro.recortadas
        for clave, valor in otro.por_tipo.items():
            self.por_tipo[clave] = self.por_tipo.get(clave, 0) + valor
        if nombre:
            self.por_capa[nombre] = otro.triangulos
            self.opciones[nombre] = otro.opciones.get(None, {})
        return self

    def a_dict(self):
        return {"matas": self.matas, "triangulos": self.triangulos, "descartadas": self.descartadas,
                "posibles": self.posibles, "unicos": self.unicos, "visor": self.visor,
                "por_tipo": self.por_tipo, "por_capa": self.por_capa, "recortadas": self.recortadas,
                "memoria": self.memoria, "memoria_sin_instancias": self.memoria_sin_instancias,
                "color": self.color}


def informe_capa(claves, triangulos_tipo, recuento_render, total_aceptadas, visor, opciones=None,
                 recortadas=False):
    """Informe de una capa.

    ``claves``: tipo de cada hueco. ``triangulos_tipo``: {clave: [t0, t1, t2]}.
    ``recuento_render``: {(hueco, nivel): matas} del render. ``visor``: matas del visor.
    """
    inf = Informe()
    usados = set()
    for (hueco, nivel), n in recuento_render.items():
        clave = claves[hueco]
        tris = triangulos_tipo[clave][nivel] * n
        inf.matas += n
        inf.triangulos += tris
        inf.por_tipo[clave] = inf.por_tipo.get(clave, 0) + tris
        usados.add((clave, nivel))
    inf.unicos = sum(triangulos_tipo[c][n] * VARIANTES for c, n in usados)
    inf.posibles = total_aceptadas
    inf.descartadas = max(0, total_aceptadas - inf.matas)
    inf.visor = visor
    inf.recortadas = recortadas
    inf.opciones = {None: dict(opciones or {})}
    return inf


def unicos_escena(usados, triangulos_tipo):
    """Triángulos de prototipos de toda la escena: cada (tipo, nivel) cuenta una vez."""
    return sum(triangulos_tipo[c][n] * VARIANTES for c, n in usados)


def consejos(inf, opciones_por_capa=None):
    """Lista de (clave de texto, valores) con lo más útil para aligerar, de más a menos."""
    lista = []
    opciones_por_capa = opciones_por_capa or {}
    if inf.recortadas:
        lista.append(("consejo_maximo", {}))
    if inf.color == "verde" and not inf.recortadas:
        return lista
    peor_capa = max(inf.por_capa, key=inf.por_capa.get) if inf.por_capa else None
    if peor_capa:
        op = opciones_por_capa.get(peor_capa, {})
        if not op.get("recorte", True):
            lista.append(("consejo_recorte", {"capa": peor_capa}))
        if not op.get("lod", True):
            lista.append(("consejo_lod", {"capa": peor_capa}))
        if not op.get("aclarar", True):
            lista.append(("consejo_aclarar", {"capa": peor_capa}))
        total = float(inf.triangulos) or 1.0
        lista.append(("consejo_capa", {"capa": peor_capa, "parte": int(round(100 * inf.por_capa[peor_capa] / total))}))
    if inf.por_tipo:
        peor_tipo = max(inf.por_tipo, key=inf.por_tipo.get)
        total = float(inf.triangulos) or 1.0
        lista.append(("consejo_tipo", {"tipo": peor_tipo,
                                       "parte": int(round(100 * inf.por_tipo[peor_tipo] / total))}))
    lista.append(("consejo_densidad", {}))
    return lista


def miles(n):
    return "{:,}".format(int(round(n))).replace(",", ".")


def corto(n):
    """1.234.567 -> «1,2 M»; 45.300 -> «45 mil»."""
    if n >= 1e6:
        return "{:.1f} M".format(n / 1e6).replace(".", ",")
    if n >= 1e4:
        return "{} mil".format(int(round(n / 1e3)))
    return miles(n)


def bytes_legibles(b):
    if b >= 1024 ** 3:
        return "{:.1f} GB".format(b / 1024.0 ** 3).replace(".", ",")
    if b >= 1024 ** 2:
        return "{} MB".format(int(round(b / 1024.0 ** 2)))
    return "{} KB".format(max(1, int(round(b / 1024.0))))
