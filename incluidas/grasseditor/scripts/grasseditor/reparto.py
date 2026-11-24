"""Reparto de matas sobre el suelo, en tres pasos que se guardan por separado.

1. ``candidatos``: todas las matas posibles sobre la superficie, con la
   densidad de la mezcla. Es lo caro y solo se repite si cambia el suelo, la
   mezcla, la densidad o la semilla.
2. ``aceptados``: las que quedan tras la máscara pintada y las reglas
   (pendiente, altura, curvas, objetos, copas). Se repite al pintar.
3. ``salida`` (en camara.py): las que ve la cámara, con su nivel de detalle.

Cada candidata lleva sus números al azar ya sacados (tipo, variante, escala,
giro, y tres claves de 0 a 1). Por eso el resultado no cambia al repetirlo
con la misma semilla, y el visor puede quedarse con «el 10 %» sin barajar:
son las que tienen la clave del visor por debajo de 0,1.

Unidades: centímetros. Densidades: matas por metro cuadrado.
Python puro: se prueba sin Maya.
"""

import math
import random
from array import array

from grasseditor.tipos import VARIANTES

MAX_CANDIDATAS = 1500000
_R2_A1 = 0.7548776662466927
_R2_A2 = 0.5698402909980532


def _hash(*valores):
    h = 2166136261
    for v in valores:
        for ch in str(v):
            h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
        h = ((h ^ 124) * 16777619) & 0xFFFFFFFF
    return h


class Suelo(object):
    """La malla del suelo tal como la ve el reparto.

    ``puntos``: vértices en el espacio del objeto. ``triangulos``: índices de
    tres en tres. ``caras``: la cara de Maya de cada triángulo. ``matriz``: la
    matriz de mundo de Maya (16 números por filas; la fila 4 es la posición).
    """

    def __init__(self, puntos, triangulos, caras=None, matriz=None):
        self.puntos = [tuple(map(float, p[:3])) for p in puntos]
        self.triangulos = list(triangulos)
        n = len(self.triangulos) // 3
        self.caras = list(caras) if caras is not None else list(range(n))
        self.matriz = list(matriz) if matriz else [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]

    def a_mundo(self, p):
        m = self.matriz
        x, y, z = p
        return (x * m[0] + y * m[4] + z * m[8] + m[12],
                x * m[1] + y * m[5] + z * m[9] + m[13],
                x * m[2] + y * m[6] + z * m[10] + m[14])

    def escala(self):
        """Escala media del objeto (para pasar el radio del pincel a sus unidades)."""
        m = self.matriz
        return (math.sqrt(m[0] ** 2 + m[1] ** 2 + m[2] ** 2) + math.sqrt(m[8] ** 2 + m[9] ** 2 + m[10] ** 2)) / 2

    def caja_local(self):
        """(xmin, zmin, xmax, zmax) del suelo en su espacio: la caja de la máscara."""
        if not self.puntos:
            return (0.0, 0.0, 1.0, 1.0)
        xs = [p[0] for p in self.puntos]
        zs = [p[2] for p in self.puntos]
        return (min(xs), min(zs), max(xs), max(zs))

    def huella(self):
        """Número que cambia si cambia la forma o la posición del suelo."""
        h = _hash(len(self.puntos), len(self.triangulos), *[round(v, 3) for v in self.matriz])
        paso = max(1, len(self.puntos) // 997)
        for p in self.puntos[::paso]:
            h = _hash(h, round(p[0], 2), round(p[1], 2), round(p[2], 2))
        return h

    def area(self, caras=None):
        """Área en cm² (en el mundo) de las caras elegidas (todas si ``caras`` es None)."""
        total = 0.0
        mundo = [self.a_mundo(p) for p in self.puntos]
        validas = set(caras) if caras else None
        for t in range(len(self.triangulos) // 3):
            if validas is not None and self.caras[t] not in validas:
                continue
            a, b, c = (mundo[i] for i in self.triangulos[3 * t:3 * t + 3])
            total += _area(a, b, c)
        return total


def _area(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    cx, cy, cz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    return 0.5 * math.sqrt(cx * cx + cy * cy + cz * cz)


def normalizar_mezcla(mezcla):
    """[(clave, porcentaje)] sin repetidos ni ceros, con los porcentajes sumando 1."""
    vistos, limpia = {}, []
    for clave, porcentaje in mezcla:
        porcentaje = max(0.0, float(porcentaje))
        if porcentaje <= 0:
            continue
        if clave in vistos:
            limpia[vistos[clave]] = (clave, limpia[vistos[clave]][1] + porcentaje)
        else:
            vistos[clave] = len(limpia)
            limpia.append((clave, porcentaje))
    total = sum(p for _, p in limpia)
    return [(c, p / total) for c, p in limpia] if total > 0 else []


class Candidatas(object):
    """Las matas posibles, en arrays compactos (unos 60 bytes por mata)."""

    def __init__(self, claves):
        self.claves = list(claves)       # tipo de cada hueco (el índice que guarda «tipo»)
        self.x, self.y, self.z = array("f"), array("f"), array("f")
        self.lx, self.lz = array("f"), array("f")      # posición en el suelo (para la máscara)
        self.pendiente = array("f")                    # grados
        self.tipo = array("B")
        self.variante = array("B")
        self.escala = array("f")
        self.giro = array("f")
        self.incl_x, self.incl_z = array("f"), array("f")
        self.k_visor, self.k_aclarar, self.k_acepta = array("f"), array("f"), array("f")
        self.recortadas = False   # se llegó al máximo de candidatas

    def __len__(self):
        return len(self.x)


def candidatos(suelo, mezcla, catalogo, densidad=100.0, semilla=1, caras=None, escala_var=0.25,
               inclinacion=12.0, maximo=MAX_CANDIDATAS):
    """Todas las matas posibles sobre ``suelo`` (ver el docstring del módulo)."""
    mezcla = normalizar_mezcla(mezcla)
    mezcla = [(c, p) for c, p in mezcla if c in catalogo]
    cand = Candidatas([c for c, _ in mezcla])
    if not mezcla or densidad <= 0:
        return cand
    tipos = [catalogo[c] for c, _ in mezcla]
    pesos = [p * t.densidad for (_, p), t in zip(mezcla, tipos)]
    por_cm2 = sum(pesos) * densidad / 100.0 / 10000.0
    acumulado, s = [], 0.0
    for w in pesos:
        s += w
        acumulado.append(s / sum(pesos))
    alturas = [(t.altura_min / t.altura, t.altura_max / t.altura) for t in tipos]
    ntipos = len(tipos)
    validas = set(caras) if caras else None
    mundo = [suelo.a_mundo(p) for p in suelo.puntos]
    locales = suelo.puntos
    tri = suelo.triangulos
    a_x, a_y, a_z = cand.x.append, cand.y.append, cand.z.append
    a_lx, a_lz, a_pe = cand.lx.append, cand.lz.append, cand.pendiente.append
    a_t, a_v, a_e, a_g = cand.tipo.append, cand.variante.append, cand.escala.append, cand.giro.append
    a_ix, a_iz = cand.incl_x.append, cand.incl_z.append
    a_k1, a_k2, a_k3 = cand.k_visor.append, cand.k_aclarar.append, cand.k_acepta.append
    total = 0
    for t in range(len(tri) // 3):
        if validas is not None and suelo.caras[t] not in validas:
            continue
        i0, i1, i2 = tri[3 * t], tri[3 * t + 1], tri[3 * t + 2]
        A, B, C = mundo[i0], mundo[i1], mundo[i2]
        ux, uy, uz = B[0] - A[0], B[1] - A[1], B[2] - A[2]
        vx, vy, vz = C[0] - A[0], C[1] - A[1], C[2] - A[2]
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        doble = math.sqrt(nx * nx + ny * ny + nz * nz)
        if doble <= 1e-9:
            continue
        esperado = 0.5 * doble * por_cm2
        rnd = random.Random(_hash(semilla, t))
        n = int(esperado)
        if rnd.random() < esperado - n:
            n += 1
        if n <= 0:
            continue
        if total + n > maximo:
            n = maximo - total
            cand.recortadas = True
            if n <= 0:
                break
        pend = math.degrees(math.acos(max(-1.0, min(1.0, ny / doble))))
        hundir = min(1.0, math.tan(math.radians(min(pend, 60.0))))
        La, Lb, Lc = locales[i0], locales[i1], locales[i2]
        o1, o2 = rnd.random(), rnd.random()
        for j in range(n):
            r1 = (o1 + j * _R2_A1) % 1.0
            r2 = (o2 + j * _R2_A2) % 1.0
            if r1 + r2 > 1.0:
                r1, r2 = 1.0 - r1, 1.0 - r2
            q = rnd.random()
            k = 0
            while k < ntipos - 1 and q > acumulado[k]:
                k += 1
            lo, hi = alturas[k]
            esc = (lo + (hi - lo) * rnd.random()) * (1.0 + escala_var * (2 * rnd.random() - 1))
            a_x(A[0] + r1 * ux + r2 * vx)
            a_y(A[1] + r1 * uy + r2 * vy - hundir * tipos[k].radio * 0.5 * esc)
            a_z(A[2] + r1 * uz + r2 * vz)
            a_lx(La[0] + r1 * (Lb[0] - La[0]) + r2 * (Lc[0] - La[0]))
            a_lz(La[2] + r1 * (Lb[2] - La[2]) + r2 * (Lc[2] - La[2]))
            a_pe(pend)
            a_t(k)
            a_v(int(rnd.random() * VARIANTES) % VARIANTES)
            a_e(esc)
            a_g(rnd.random() * 360.0)
            a_ix(inclinacion * (rnd.random() + rnd.random() - 1.0))
            a_iz(inclinacion * (rnd.random() + rnd.random() - 1.0))
            a_k1(rnd.random())
            a_k2(rnd.random())
            a_k3(rnd.random())
        total += n
        if cand.recortadas:
            break
    return cand


def esperadas(suelo, mezcla, catalogo, densidad=100.0, caras=None):
    """Cuántas candidatas saldrían (sin generarlas): para avisar antes de algo enorme."""
    mezcla = [(c, p) for c, p in normalizar_mezcla(mezcla) if c in catalogo]
    por_m2 = sum(p * catalogo[c].densidad for c, p in mezcla) * densidad / 100.0
    return suelo.area(caras) / 10000.0 * por_m2


# --- reglas ---------------------------------------------------------------------------

class Reglas(object):
    """Lo que decide dónde no crece la hierba, aparte de la máscara pintada.

    ``curvas``: [{"puntos": [(x, z)...], "cerrada": bool, "modo": "dentro"|"fuera",
    "ancho": cm}] en el mundo. Una curva cerrada «dentro» limita la hierba a su
    interior (un parterre); «fuera» la quita de dentro. Una curva abierta
    «fuera» es un camino de ``ancho`` cm; «dentro», una franja a lo largo.
    ``objetos``: [(x, z, radio)] de los que se aparta. ``copas``: [(x, z, radio)]
    bajo las que crece ``factor_copa`` de la hierba. ``borde``: cm de transición.
    """

    def __init__(self, pendiente_max=90.0, altura_min=None, altura_max=None, curvas=None, objetos=None,
                 copas=None, borde=40.0, factor_copa=0.5):
        self.pendiente_max = float(pendiente_max)
        self.altura_min = altura_min
        self.altura_max = altura_max
        self.curvas = list(curvas or [])
        self.objetos = list(objetos or [])
        self.copas = list(copas or [])
        self.borde = max(1.0, float(borde))
        self.factor_copa = float(factor_copa)

    def a_dict(self):
        return {"pendiente_max": self.pendiente_max, "altura_min": self.altura_min,
                "altura_max": self.altura_max, "curvas": self.curvas, "objetos": self.objetos,
                "copas": self.copas, "borde": self.borde, "factor_copa": self.factor_copa}

    @classmethod
    def desde_dict(cls, datos):
        datos = datos or {}
        campos = ("pendiente_max", "altura_min", "altura_max", "curvas", "objetos", "copas", "borde",
                  "factor_copa")
        return cls(**{c: datos[c] for c in campos if c in datos})

    def hay_campo(self):
        return bool(self.curvas or self.objetos or self.copas)


class Campo(object):
    """Las curvas, objetos y copas pasados a una rejilla del mundo (X, Z) de 0 a 1.

    Calcular la distancia de cada mata a cada curva sería muy lento con
    cientos de miles de matas; así se calcula una vez por casilla.
    """

    MAX_CASILLAS = 250000

    def __init__(self, reglas, caja):
        x0, z0, x1, z1 = caja
        borde = reglas.borde
        x0, z0, x1, z1 = x0 - borde, z0 - borde, x1 + borde, z1 + borde
        area = max(1.0, (x1 - x0) * (z1 - z0))
        self.celda = max(5.0, math.sqrt(area / self.MAX_CASILLAS))
        self.x0, self.z0 = x0, z0
        self.nx = max(2, int(math.ceil((x1 - x0) / self.celda)) + 1)
        self.nz = max(2, int(math.ceil((z1 - z0) / self.celda)) + 1)
        dentro = [c for c in reglas.curvas if c.get("modo") == "dentro" and len(c.get("puntos", ())) >= 2]
        n = self.nx * self.nz
        if dentro:
            union = array("f", [0.0]) * n
            for curva in dentro:
                f = self._curva(curva, borde)
                for i in range(n):
                    if f[i] > union[i]:
                        union[i] = f[i]
            self.v = union
        else:
            self.v = array("f", [1.0]) * n
        for curva in reglas.curvas:
            if curva.get("modo") != "dentro" and len(curva.get("puntos", ())) >= 2:
                self._multiplicar(self._curva(curva, borde))
        for x, z, r in reglas.objetos:
            self._circulo(x, z, r, borde, 0.0)
        for x, z, r in reglas.copas:
            self._circulo(x, z, r, borde, reglas.factor_copa)

    def _centro(self, i, j):
        return self.x0 + i * self.celda, self.z0 + j * self.celda

    def _multiplicar(self, f):
        v = self.v
        for i in range(len(v)):
            v[i] *= f[i]

    def _distancias(self, puntos, cerrada, alcance):
        """Distancia de cada casilla a la línea (solo las que están a menos de ``alcance``)."""
        nx, nz, celda = self.nx, self.nz, self.celda
        d = array("f", [1e9]) * (nx * nz)
        segs = list(zip(puntos, puntos[1:] + (puntos[:1] if cerrada else [])))
        for (ax, az), (bx, bz) in segs:
            i0 = max(0, int((min(ax, bx) - alcance - self.x0) / celda))
            i1 = min(nx - 1, int((max(ax, bx) + alcance - self.x0) / celda) + 1)
            j0 = max(0, int((min(az, bz) - alcance - self.z0) / celda))
            j1 = min(nz - 1, int((max(az, bz) + alcance - self.z0) / celda) + 1)
            vx, vz = bx - ax, bz - az
            ll = vx * vx + vz * vz or 1e-9
            for j in range(j0, j1 + 1):
                z = self.z0 + j * celda
                fila = j * nx
                for i in range(i0, i1 + 1):
                    x = self.x0 + i * celda
                    t = ((x - ax) * vx + (z - az) * vz) / ll
                    t = 0.0 if t < 0 else (1.0 if t > 1 else t)
                    dd = math.hypot(x - ax - t * vx, z - az - t * vz)
                    if dd < d[fila + i]:
                        d[fila + i] = dd
        return d

    def _dentro(self, puntos):
        """1 en las casillas dentro del polígono (regla par-impar, por filas)."""
        nx, nz, celda = self.nx, self.nz, self.celda
        dentro = bytearray(nx * nz)
        segs = list(zip(puntos, puntos[1:] + puntos[:1]))
        for j in range(nz):
            z = self.z0 + j * celda
            cortes = []
            for (ax, az), (bx, bz) in segs:
                if (az <= z < bz) or (bz <= z < az):
                    cortes.append(ax + (z - az) * (bx - ax) / (bz - az))
            cortes.sort()
            for a, b in zip(cortes[::2], cortes[1::2]):
                i0 = max(0, int(math.ceil((a - self.x0) / celda)))
                i1 = min(nx - 1, int(math.floor((b - self.x0) / celda)))
                for i in range(i0, i1 + 1):
                    dentro[j * nx + i] = 1
        return dentro

    def _curva(self, curva, borde):
        puntos = [tuple(p[:2]) for p in curva["puntos"]]
        cerrada = bool(curva.get("cerrada")) and len(puntos) >= 3
        modo = curva.get("modo", "fuera")
        media = max(0.0, float(curva.get("ancho", 0.0))) / 2.0
        n = self.nx * self.nz
        d = self._distancias(puntos, cerrada, media + borde + self.celda)
        f = array("f", [0.0]) * n
        if cerrada:
            dentro = self._dentro(puntos)
            # Transición centrada en la curva (mitad dentro, mitad fuera): el área
            # con hierba es la de la curva, como esperaría quien la dibuja.
            signo = 1.0 if modo == "dentro" else -1.0
            for i in range(n):
                s = d[i] if dentro[i] else -d[i]
                f[i] = min(1.0, max(0.0, 0.5 + signo * s / borde))
        else:
            for i in range(n):
                fuera = 0.0 if d[i] < media else min(1.0, (d[i] - media) / borde)
                f[i] = 1.0 - fuera if modo == "dentro" else fuera
        return f

    def _circulo(self, cx, cz, radio, borde, minimo):
        nx, celda, v = self.nx, self.celda, self.v
        alcance = radio + borde
        i0 = max(0, int((cx - alcance - self.x0) / celda))
        i1 = min(nx - 1, int((cx + alcance - self.x0) / celda) + 1)
        j0 = max(0, int((cz - alcance - self.z0) / celda))
        j1 = min(self.nz - 1, int((cz + alcance - self.z0) / celda) + 1)
        for j in range(j0, j1 + 1):
            z = self.z0 + j * celda
            for i in range(i0, i1 + 1):
                d = math.hypot(self.x0 + i * celda - cx, z - cz)
                if d >= alcance:
                    continue
                f = minimo if d <= radio else minimo + (1.0 - minimo) * (d - radio) / borde
                v[j * nx + i] *= f

    def valor(self, x, z):
        gx = (x - self.x0) / self.celda
        gz = (z - self.z0) / self.celda
        if gx < 0 or gz < 0 or gx > self.nx - 1 or gz > self.nz - 1:
            return 1.0
        i, j = int(gx), int(gz)
        i1, j1 = min(i + 1, self.nx - 1), min(j + 1, self.nz - 1)
        fx, fz = gx - i, gz - j
        v, w = self.v, self.nx
        a = v[j * w + i] + (v[j * w + i1] - v[j * w + i]) * fx
        b = v[j1 * w + i] + (v[j1 * w + i1] - v[j1 * w + i]) * fx
        return a + (b - a) * fz


def caja_mundo(cand):
    if not len(cand):
        return (0.0, 0.0, 1.0, 1.0)
    return (min(cand.x), min(cand.z), max(cand.x), max(cand.z))


def aceptados(cand, mascara=None, reglas=None, visor=None):
    """Índices de las candidatas que sobreviven a la máscara y las reglas (array de enteros).

    Con ``visor`` (de 0 a 1) solo se miran las que enseña el visor (clave del visor menor).
    """
    reglas = reglas or Reglas()
    muestra = mascara.muestreador() if mascara is not None else None
    campo = Campo(reglas, caja_mundo(cand)).valor if reglas.hay_campo() else None
    pmax = reglas.pendiente_max
    hmin, hmax = reglas.altura_min, reglas.altura_max
    fundido = 10.0
    salida = array("l")
    poner = salida.append
    X, Y, Z, LX, LZ, PE, K = cand.x, cand.y, cand.z, cand.lx, cand.lz, cand.pendiente, cand.k_acepta
    K1 = cand.k_visor
    for i in range(len(cand)):
        if visor is not None and K1[i] >= visor:
            continue
        f = 1.0
        if muestra is not None:
            f = muestra(LX[i], LZ[i])
            if f <= 0.0:
                continue
        p = PE[i]
        if p > pmax:
            f *= 1.0 - (p - pmax) / 4.0
            if f <= 0.0:
                continue
        if hmin is not None and Y[i] < hmin:
            f *= 1.0 - (hmin - Y[i]) / fundido
            if f <= 0.0:
                continue
        if hmax is not None and Y[i] > hmax:
            f *= 1.0 - (Y[i] - hmax) / fundido
            if f <= 0.0:
                continue
        if campo is not None:
            f *= campo(X[i], Z[i])
        if K[i] < f:
            poner(i)
    return salida
