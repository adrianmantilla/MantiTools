"""Módulos de un árbol (tronco y ramas) y su malla, en Python puro.

Cada módulo es un tubo que sigue una curva guía calculada a partir de sus
parámetros. La forma es una función continua de la posición a lo largo del
tubo (s, de 0 a 1) y del ángulo alrededor (theta). La malla solo la muestrea:
la versión densa y la ligera son el mismo tubo con más o menos divisiones, y
cada punto (s, theta) tiene la misma UV en las dos.

Unidades: centímetros (las de Maya por defecto) y grados en los parámetros.
"""

import math
import zlib

from arboles import vectores as v

TRONCO = "tronco"
RAMA = "rama"
TIPOS = (TRONCO, RAMA)

# nombre: (por defecto, mínimo, máximo, avanzado)
PARAMETROS = {
    TRONCO: {
        "altura": (600.0, 50.0, 3000.0, False),
        "grosor": (25.0, 2.0, 200.0, False),          # radio en la base
        "estrechamiento": (0.35, 0.05, 1.0, False),   # radio en la punta / radio en la base
        "inclinacion": (0.0, 0.0, 60.0, False),
        "curvatura": (0.15, -1.0, 1.0, False),
        "direccion": (0.0, 0.0, 360.0, True),         # hacia dónde se inclina y se curva
        "torsion": (0.0, -360.0, 360.0, True),
        "raices": (0.4, 0.0, 1.0, True),
        "irregularidad": (0.25, 0.0, 1.0, True),
        "nudos": (2, 0, 10, True),
        "horquilla": (0.0, 0.0, 0.9, True),           # altura (fracción) donde se divide; 0 = no se divide
        "brazos": (2, 2, 3, True),                    # en cuántos troncos se divide
        "abertura": (30.0, 5.0, 80.0, True),          # ángulo entre cada brazo y el eje del tronco
    },
    RAMA: {
        "longitud": (250.0, 10.0, 2000.0, False),
        "angulo": (50.0, 0.0, 120.0, False),          # ángulo de salida respecto a la madre
        "caida": (0.3, 0.0, 1.0, False),              # cuánto la dobla su propio peso
        "curvatura": (0.1, -1.0, 1.0, False),         # positiva hacia arriba
        "posicion": (0.6, 0.0, 1.0, True),            # dónde nace a lo largo de la madre
        "giro": (0.0, 0.0, 360.0, True),              # alrededor de la madre
        "grosor": (0.45, 0.05, 1.0, True),            # radio respecto al de la madre en ese punto
        "estrechamiento": (0.2, 0.02, 1.0, True),
        "torsion": (0.0, -360.0, 360.0, True),
        "irregularidad": (0.15, 0.0, 1.0, True),
        "nudos": (1, 0, 10, True),
        # Follaje (sección propia en el editor)
        "follaje": ("hoja_ancha", None, None, False),
        "densidad": (0.6, 0.0, 2.0, False),
        "tamano_hoja": (1.0, 0.3, 3.0, False),
        "zona": (0.6, 0.05, 1.0, True),               # parte de la rama con hojas, desde la punta
        "hacia_arriba": (0.4, 0.0, 1.0, True),        # cuánto miran las hojas hacia el cielo
    },
}

# Parámetros con una lista cerrada de valores
OPCIONES = {"follaje": ("ninguno", "hoja_ancha", "hoja_roble", "hoja_fina", "hoja_redonda", "hoja_pequena",
                        "hoja_palmeada", "hoja_castano", "hoja_grande", "plumosa", "escama", "aguja",
                        "pinocha", "aguja_corta", "foliolo", "flor")}
PARAMETROS_FOLLAJE = ("follaje", "densidad", "tamano_hoja", "zona", "hacia_arriba")
# Al copiar ajustes no se copia dónde nace la rama
PARAMETROS_DE_SITIO = ("posicion", "giro")

# Puntos de la curva guía que se pueden mover a mano (fracción del largo)
CONTROLES = (1.0 / 3.0, 2.0 / 3.0, 1.0)

# nivel: (lados, largo de cada segmento en radios de la base, largo mínimo en cm)
NIVELES = {
    "denso": (24, 0.5, 2.0),
    "alto": (12, 1.2, 8.0),
    "medio": (8, 2.0, 15.0),
    "bajo": (6, 3.0, 25.0),
}
NIVELES_GENERAR = ("alto", "medio", "bajo")
SEGMENTOS_MIN, SEGMENTOS_MAX = 3, 160

_MUESTRAS_GUIA = 64       # resolución fija de la curva guía, igual para todos los niveles
_ATRAS = (0.0, 0.0, -1.0)  # la costura del tronco mira hacia atrás
_TAU = 2.0 * math.pi


def valores_por_defecto(tipo):
    return {k: d[0] for k, d in PARAMETROS[tipo].items()}


PROPIA = "propia:"  # follaje con una hoja hecha por el alumno (ver follaje.py)


def limitar(tipo, nombre, valor):
    if nombre in OPCIONES:
        if nombre == "follaje" and isinstance(valor, str) and valor.startswith(PROPIA) and len(valor) > len(PROPIA):
            return valor
        if valor not in OPCIONES[nombre]:
            raise ValueError("{} no admite {!r}".format(nombre, valor))
        return valor
    defecto, minimo, maximo, _ = PARAMETROS[tipo][nombre]
    valor = max(minimo, min(maximo, valor))
    return int(round(valor)) if isinstance(defecto, int) else float(valor)


class Modulo(object):
    """Un tronco o una rama: tipo, madre y valores de sus parámetros."""

    def __init__(self, id_, tipo, padre=None, valores=None):
        if tipo not in TIPOS:
            raise ValueError("tipo desconocido: {}".format(tipo))
        if (tipo == TRONCO) != (padre is None):
            raise ValueError("el tronco no tiene madre y toda rama necesita una")
        self.id = id_
        self.tipo = tipo
        self.padre = padre
        self.valores = valores_por_defecto(tipo)
        for nombre, valor in (valores or {}).items():
            self.fijar(nombre, valor)
        self.curva = {}   # índice de CONTROLES -> desplazamiento (x, y, z) movido a mano
        self.guia = None  # Guia calculada

    def fijar(self, nombre, valor):
        if nombre not in PARAMETROS[self.tipo]:
            raise KeyError("{} no tiene el parámetro {}".format(self.tipo, nombre))
        self.valores[nombre] = limitar(self.tipo, nombre, valor)

    @property
    def semilla(self):
        return zlib.crc32(self.id.encode("utf-8")) & 0xFFFFFFFF

    def fijar_control(self, indice, desplazamiento):
        if not 0 <= indice < len(CONTROLES):
            raise IndexError(indice)
        if desplazamiento is None or v.largo(desplazamiento) < 1e-6:
            self.curva.pop(indice, None)
        else:
            self.curva[indice] = v.vec(desplazamiento)

    def desplazamiento(self, s):
        """Desplazamiento a mano de la curva en ``s``: suave y nulo en la base."""
        if not self.curva:
            return v.CERO
        puntos = [(0.0, v.CERO)] + [(c, self.curva.get(i, v.CERO)) for i, c in enumerate(CONTROLES)]
        for (s0, d0), (s1, d1) in zip(puntos, puntos[1:]):
            if s <= s1:
                f = (s - s0) / (s1 - s0)
                f = f * f * (3.0 - 2.0 * f)
                return v.suma(v.escala(d0, 1.0 - f), v.escala(d1, f))
        return puntos[-1][1]

    def a_dict(self):
        datos = {"id": self.id, "tipo": self.tipo, "padre": self.padre, "valores": dict(self.valores)}
        if self.curva:
            datos["curva"] = {str(i): list(d) for i, d in sorted(self.curva.items())}
        return datos

    @classmethod
    def de_dict(cls, datos):
        m = cls(datos["id"], datos["tipo"], datos.get("padre"), datos.get("valores"))
        for i, d in (datos.get("curva") or {}).items():
            m.fijar_control(int(i), d)
        return m


# --- Curva guía ---------------------------------------------------------------

class Guia(object):
    """Curva guía muestreada a resolución fija, con marcos sin giros bruscos.

    ``puntos``, ``tangentes``, ``normales`` y ``binormales`` tienen
    _MUESTRAS_GUIA + 1 elementos repartidos por igual a lo largo del tubo.
    """

    def __init__(self, puntos, normal_inicial, radio_base, radio_fn, desplazamiento=None):
        self.base = puntos  # sin los retoques a mano
        if desplazamiento:
            n = float(len(puntos) - 1)
            puntos = [v.suma(p, desplazamiento(i / n)) for i, p in enumerate(puntos)]
        self.puntos = puntos
        self.largo = sum(v.distancia(a, b) for a, b in zip(puntos, puntos[1:]))
        self.radio_base = radio_base
        self.radio_fn = radio_fn  # radio_fn(s, theta)
        self.horquilla = None  # altura (s) donde el tronco se divide en ``brazos``
        self.corte = None      # altura (s) donde nacen los brazos, algo por debajo
        self.brazos = []
        n = len(puntos) - 1
        self.tangentes = []
        for i in range(n + 1):
            a, b = puntos[max(0, i - 1)], puntos[min(n, i + 1)]
            self.tangentes.append(v.unitario(v.resta(b, a)) or v.ARRIBA)
        # Transporte paralelo: la normal gira lo justo para seguir a la tangente.
        normal = v.unitario(v.tangente(normal_inicial, self.tangentes[0])) or v.perpendicular(self.tangentes[0])
        self.normales, self.binormales = [], []
        anterior = self.tangentes[0]
        for t in self.tangentes:
            eje = v.unitario(v.cruz(anterior, t))
            if eje:
                normal = v.rotar(normal, eje, v.angulo_entre(anterior, t))
            normal = v.unitario(v.tangente(normal, t)) or v.perpendicular(t)
            self.normales.append(normal)
            self.binormales.append(v.cruz(t, normal))
            anterior = t

    def _indice(self, s):
        x = max(0.0, min(1.0, s)) * (len(self.puntos) - 1)
        i = min(int(x), len(self.puntos) - 2)
        return i, x - i

    @staticmethod
    def _mezcla(a, b, f):
        return v.suma(v.escala(a, 1.0 - f), v.escala(b, f))

    def punto(self, s):
        i, f = self._indice(s)
        return self._mezcla(self.puntos[i], self.puntos[i + 1], f)

    def punto_base(self, s):
        i, f = self._indice(s)
        return self._mezcla(self.base[i], self.base[i + 1], f)

    def mas_cercano(self, p):
        """s del punto de la curva más cercano a ``p``."""
        mejor = min(range(len(self.puntos)), key=lambda i: v.distancia(self.puntos[i], p))
        return mejor / float(len(self.puntos) - 1)

    def marco(self, s):
        """(tangente, normal, binormal) ortonormales en ``s``."""
        i, f = self._indice(s)
        t = v.unitario(self._mezcla(self.tangentes[i], self.tangentes[i + 1], f)) or self.tangentes[i]
        n = v.unitario(v.tangente(self._mezcla(self.normales[i], self.normales[i + 1], f), t)) \
            or v.perpendicular(t)
        return t, n, v.cruz(t, n)

    def radio(self, s, theta=0.0):
        return self.radio_fn(s, theta)

    def sitio(self, s, giro):
        """(guia, s) donde nace algo en ``s`` con ``giro``: por encima de la horquilla, en su brazo."""
        if not self.brazos or s <= self.corte:
            return self, s
        k = int((giro % 360.0) / (360.0 / len(self.brazos))) % len(self.brazos)
        return self.brazos[k], max(0.0, (s - self.horquilla) / (1.0 - self.horquilla))

    def radio_medio(self, s):
        return sum(self.radio_fn(s, k * _TAU / 8.0) for k in range(8)) / 8.0


def _azar(semilla):
    """Generador congruencial sencillo: mismos valores en cualquier Python."""
    estado = [semilla or 1]

    def siguiente():
        estado[0] = (1103515245 * estado[0] + 12345) & 0x7FFFFFFF
        return estado[0] / float(0x7FFFFFFF)
    return siguiente


def _forma(modulo, radio_base, largo):
    """Función radio(s, theta) del módulo: estrechamiento, irregularidad, nudos y raíces."""
    val = modulo.valores
    azar = _azar(modulo.semilla)
    estrecho = val["estrechamiento"]
    irregular = val["irregularidad"]
    ondas = [(1 + int(azar() * 3), 0.5 + azar() * 2.5, azar() * _TAU, 0.4 + azar() * 0.6) for _ in range(4)]
    nudos = [(0.15 + azar() * 0.75, azar() * _TAU) for _ in range(val["nudos"])]
    ancho_nudo = max(radio_base * 0.9, 1e-3) / max(largo, 1e-3)
    raices = val.get("raices", 0.0)
    lobulos = 4 + int(azar() * 3)
    fase_raices = azar() * _TAU
    alto_raices = min(0.35, radio_base * 3.0 / max(largo, 1e-3))

    def radio(s, theta):
        r = radio_base * (1.0 + (estrecho - 1.0) * (s ** 0.8))
        if irregular:
            ruido = sum(a * math.sin(f * s * largo / max(radio_base, 1e-3) + m * theta + fase)
                        for m, f, fase, a in ondas) / len(ondas)
            r *= 1.0 + 0.12 * irregular * ruido
        for s_nudo, theta_nudo in nudos:
            ds = (s - s_nudo) / ancho_nudo
            dt = math.atan2(math.sin(theta - theta_nudo), math.cos(theta - theta_nudo)) / 0.6
            r *= 1.0 + 0.3 * math.exp(-ds * ds - dt * dt)
        if raices and s < alto_raices:
            f = (1.0 - s / alto_raices) ** 2
            r *= 1.0 + raices * f * (0.8 + 0.7 * math.cos(lobulos * theta + fase_raices))
        return r
    return radio


def guia_tronco(modulo, origen=v.CERO):
    val = modulo.valores
    largo = val["altura"]
    d = math.radians(val["direccion"])
    horizontal = (math.sin(d), 0.0, math.cos(d))
    eje_curva = v.unitario(v.cruz(v.ARRIBA, horizontal))
    inclinacion = math.radians(val["inclinacion"])
    direccion = v.rotar(v.ARRIBA, eje_curva, inclinacion)
    paso = largo / _MUESTRAS_GUIA
    giro_paso = val["curvatura"] * (math.pi / 2.0) / _MUESTRAS_GUIA
    puntos = [v.vec(origen)]
    for _ in range(_MUESTRAS_GUIA):
        puntos.append(v.suma(puntos[-1], v.escala(direccion, paso)))
        direccion = v.rotar(direccion, eje_curva, giro_paso)
    radio = _forma(modulo, val["grosor"], largo)
    guia = Guia(puntos, _ATRAS, val["grosor"], radio, modulo.desplazamiento if modulo.curva else None)
    if val.get("horquilla", 0.0) > 0.0:
        _horquilla(guia, val)
    return guia


def _horquilla(guia, val):
    """Divide el tronco en ``brazos`` a la altura ``horquilla``: cada brazo es una Guia propia.

    El tronco se dibuja hasta la horquilla y los brazos nacen dentro de él, abiertos
    ``abertura`` grados y enderezándose hacia arriba. Las ramas que nacen por encima de la
    horquilla se cuelgan del brazo que les toca por su giro (ver ``Guia.sitio``).
    """
    h = val["horquilla"]
    brazos = int(val["brazos"])
    t, n, b = guia.marco(h)
    # Los brazos arrancan algo por debajo de la horquilla, dentro del tronco: así su boca no se ve
    guia.corte = max(0.0, h - 2.5 * guia.radio_medio(h) / max(guia.largo, 1e-3))
    origen = guia.punto(guia.corte)
    largo = (1.0 - h) * val["altura"] * 1.3  # algo más largos: siguen como guías dentro de la copa
    abertura = math.radians(val["abertura"])
    reparto = 0.88 if brazos == 2 else 0.76  # grosor de cada brazo respecto al tronco en la horquilla
    radio_h = guia.radio_medio(h)
    paso = largo / _MUESTRAS_GUIA
    guia.horquilla = h
    guia.brazos = []
    for k in range(brazos):
        phi = (k + 0.5) * _TAU / brazos
        radial = v.suma(v.escala(n, math.cos(phi)), v.escala(b, math.sin(phi)))
        direccion = v.unitario(v.suma(v.escala(t, math.cos(abertura)), v.escala(radial, math.sin(abertura))))
        puntos = [origen]
        for i in range(_MUESTRAS_GUIA):
            puntos.append(v.suma(puntos[-1], v.escala(direccion, paso)))
            # Se endereza poco a poco: acaba con la mitad de la abertura
            eje = v.unitario(v.cruz(direccion, v.ARRIBA))
            if eje and v.angulo_entre(direccion, v.ARRIBA) > abertura * 0.5:
                direccion = v.rotar(direccion, eje, abertura * 0.5 / _MUESTRAS_GUIA)

        def radio(s, theta, h=h):
            # Se estrechan hacia la punta más que el tronco, para no acabar en un tocón
            return guia.radio_fn(h + (1.0 - h) * s, theta) * reparto * (1.0 - 0.6 * s ** 1.2)
        guia.brazos.append(Guia(puntos, _ATRAS, radio_h * reparto, radio))


def guia_rama(modulo, madre):
    """Curva guía de una rama que nace en el eje de su ``madre`` (una Guia)."""
    val = modulo.valores
    madre, s0 = madre.sitio(val["posicion"], val["giro"])
    inicio = madre.punto(s0)
    t, n, b = madre.marco(s0)
    giro = math.radians(val["giro"])
    radial = v.suma(v.escala(n, math.cos(giro)), v.escala(b, math.sin(giro)))
    angulo = math.radians(val["angulo"])
    direccion = v.unitario(v.suma(v.escala(t, math.cos(angulo)), v.escala(radial, math.sin(angulo))))
    radio_base = max(0.2, madre.radio_medio(s0) * val["grosor"])
    largo = val["longitud"]
    flexible = max(0.3, min(1.8, largo / radio_base / 40.0))
    paso = largo / _MUESTRAS_GUIA
    curva_paso = val["curvatura"] * (math.pi / 2.0) / _MUESTRAS_GUIA
    puntos = [inicio]
    for i in range(_MUESTRAS_GUIA):
        puntos.append(v.suma(puntos[-1], v.escala(direccion, paso)))
        eje = v.unitario(v.cruz(direccion, v.ARRIBA))
        if eje:
            direccion = v.rotar(direccion, eje, curva_paso)          # curvatura: hacia arriba
            hacia_abajo = v.angulo_entre(direccion, v.ABAJO)
            # Como una viga en voladizo: se dobla más cerca de donde nace.
            caida = val["caida"] * flexible * 1.2 * (1.5 - i / float(_MUESTRAS_GUIA)) / _MUESTRAS_GUIA
            direccion = v.rotar(direccion, eje, -min(caida, hacia_abajo * 0.5))
        direccion = v.unitario(direccion) or direccion
    # La costura de las ramas va por debajo, donde menos se ve.
    return Guia(puntos, v.ABAJO, radio_base, _forma(modulo, radio_base, largo),
                modulo.desplazamiento if modulo.curva else None)


# --- Malla --------------------------------------------------------------------

class Malla(object):
    """Datos de una malla listos para MFnMesh.create y assignUVs."""

    def __init__(self, nombre):
        self.nombre = nombre
        self.vertices = []
        self.conteos = []
        self.conexiones = []
        self.us, self.vs = [], []
        self.uv_ids = []

    @property
    def caras(self):
        return len(self.conteos)

    @property
    def triangulos(self):
        return sum(c - 2 for c in self.conteos)


# Ramitas finas en las versiones generadas: menos lados (de lejos no se nota y ahorra mucho)
RADIO_RAMITA = 1.5


def lados(guia, nivel):
    n = NIVELES[nivel][0]
    if nivel != "denso" and guia.radio_base < RADIO_RAMITA:
        n = max(4, n // 2)
    return n


def segmentos(guia, nivel):
    _, largo_segmento, minimo = NIVELES[nivel]
    n = int(math.ceil(guia.largo / max(guia.radio_base * largo_segmento, minimo)))
    return max(SEGMENTOS_MIN, min(SEGMENTOS_MAX, n))


def repeticiones_u(radio_base, escala_textura):
    """Vueltas enteras de textura alrededor del tubo (enteras para que no se note la costura)."""
    return max(1, int(round(_TAU * radio_base / escala_textura)))


def uv(s, theta, guia, escala_textura, v0=0.0):
    """UV de un punto del tubo: no depende de la resolución de la malla."""
    return (theta / _TAU * repeticiones_u(guia.radio_base, escala_textura),
            v0 + s * guia.largo / escala_textura)


def malla_tubo(guia, nivel, nombre, torsion=0.0, escala_textura=60.0, cerrar_punta=True, hasta=1.0, v0=0.0,
               punta=0.6):
    """Tubo de ``guia`` desde s=0 hasta s=``hasta``; ``v0`` desplaza la v de las UVs.

    ``punta``: alto del cono que cierra el extremo, en radios."""
    lados_ = lados(guia, nivel)
    n_seg = max(SEGMENTOS_MIN, int(math.ceil(segmentos(guia, nivel) * hasta)))
    torsion = math.radians(torsion)
    m = Malla(nombre)
    for k in range(n_seg + 1):
        s = k / float(n_seg) * hasta
        centro = guia.punto(s)
        _, n, b = guia.marco(s)
        for j in range(lados_):
            theta = j * _TAU / lados_
            a = theta + torsion * s
            direccion = v.suma(v.escala(n, math.cos(a)), v.escala(b, math.sin(a)))
            m.vertices.append(v.suma(centro, v.escala(direccion, guia.radio(s, theta))))
        for j in range(lados_ + 1):  # una UV más por anillo: la costura
            u_, v_ = uv(s, j * _TAU / lados_, guia, escala_textura, v0)
            m.us.append(u_)
            m.vs.append(v_)
    for k in range(n_seg):
        for j in range(lados_):
            j2 = (j + 1) % lados_
            m.conteos.append(4)
            m.conexiones += [k * lados_ + j, k * lados_ + j2, (k + 1) * lados_ + j2, (k + 1) * lados_ + j]
            fila, sig = k * (lados_ + 1), (k + 1) * (lados_ + 1)
            m.uv_ids += [fila + j, fila + j + 1, sig + j + 1, sig + j]
    if cerrar_punta:
        t, _, _ = guia.marco(hasta)
        alto_punta = guia.radio_medio(hasta) * punta
        punta = v.suma(guia.punto(hasta), v.escala(t, alto_punta))
        i_punta = len(m.vertices)
        m.vertices.append(punta)
        uv_punta = len(m.us)
        u_max, v_fin = uv(hasta, _TAU, guia, escala_textura, v0)
        m.us.append(u_max * 0.5)
        m.vs.append(v_fin + alto_punta / escala_textura)
        ultimo, fila = n_seg * lados_, n_seg * (lados_ + 1)
        for j in range(lados_):
            m.conteos.append(3)
            m.conexiones += [ultimo + j, ultimo + (j + 1) % lados_, i_punta]
            m.uv_ids += [fila + j, fila + j + 1, uv_punta]
    return m


def unir(nombre, mallas):
    """Una sola Malla con todas las de ``mallas`` (índices de vértices y UVs desplazados)."""
    m = Malla(nombre)
    for parte in mallas:
        dv, duv = len(m.vertices), len(m.us)
        m.vertices += parte.vertices
        m.us += parte.us
        m.vs += parte.vs
        m.conteos += parte.conteos
        m.conexiones += [i + dv for i in parte.conexiones]
        m.uv_ids += [i + duv for i in parte.uv_ids]
    return m


def malla_modulo(guia, nivel, nombre, torsion=0.0, escala_textura=60.0):
    """Malla de un módulo: su tubo y, si el tronco tiene horquilla, también sus brazos."""
    if not guia.brazos:
        return malla_tubo(guia, nivel, nombre, torsion, escala_textura)
    h = guia.horquilla
    # El tronco acaba poco después de donde nacen los brazos: su remate queda dentro de ellos
    hasta = min(h, guia.corte + 1.0 * guia.radio_medio(h) / max(guia.largo, 1e-3))
    partes = [malla_tubo(guia, nivel, nombre, torsion, escala_textura, hasta=hasta)]
    v0 = guia.corte * guia.largo / escala_textura  # la corteza sigue por los brazos sin saltos
    for brazo in guia.brazos:
        partes.append(malla_tubo(brazo, nivel, nombre, torsion, escala_textura, v0=v0, punta=2.0))
    return unir(nombre, partes)
