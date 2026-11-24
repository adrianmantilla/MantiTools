"""Máscara pintada de una capa: una rejilla sobre la planta (X, Z) del suelo.

La rejilla cubre la caja del suelo en su propio espacio (si el suelo se mueve,
la hierba pintada se mueve con él). Cada casilla mide unos 10 cm, hasta 512
casillas por lado, y guarda un valor de 0 (sin hierba) a 255 (toda la densidad).
No depende de los vértices del suelo: un plano de una sola cara se pinta igual
de fino que uno subdividido.

Se guarda en la escena como texto (zlib + base64), unos pocos KB.
"""

import base64
import math
import zlib

CASILLA = 10.0     # cm
MAXIMO = 512
MINIMO = 8


class Mascara(object):
    def __init__(self, caja, valor=255, ancho=None, alto=None):
        """``caja`` = (xmin, zmin, xmax, zmax) en el espacio del suelo."""
        x0, z0, x1, z1 = caja
        if x1 - x0 < 1e-6:
            x1 = x0 + 1.0
        if z1 - z0 < 1e-6:
            z1 = z0 + 1.0
        self.caja = (float(x0), float(z0), float(x1), float(z1))
        self.ancho = ancho or _lado(x1 - x0)
        self.alto = alto or _lado(z1 - z0)
        self.datos = bytearray([int(valor)]) * (self.ancho * self.alto)

    # --- coordenadas --------------------------------------------------------------

    @property
    def tam_casilla(self):
        x0, z0, x1, z1 = self.caja
        return (x1 - x0) / self.ancho, (z1 - z0) / self.alto

    def _a_rejilla(self, x, z):
        x0, z0, x1, z1 = self.caja
        return ((x - x0) / (x1 - x0) * self.ancho - 0.5, (z - z0) / (z1 - z0) * self.alto - 0.5)

    def valor(self, x, z):
        """Valor de 0 a 1 en el punto (x, z), interpolado entre casillas."""
        gx, gz = self._a_rejilla(x, z)
        if gx < -0.5 or gz < -0.5 or gx > self.ancho - 0.5 or gz > self.alto - 0.5:
            return 0.0
        gx = min(max(gx, 0.0), self.ancho - 1.0)
        gz = min(max(gz, 0.0), self.alto - 1.0)
        i, j = int(gx), int(gz)
        fx, fz = gx - i, gz - j
        i1, j1 = min(i + 1, self.ancho - 1), min(j + 1, self.alto - 1)
        d, w = self.datos, self.ancho
        a = d[j * w + i] + (d[j * w + i1] - d[j * w + i]) * fx
        b = d[j1 * w + i] + (d[j1 * w + i1] - d[j1 * w + i]) * fx
        return (a + (b - a) * fz) / 255.0

    def muestreador(self):
        """Función rápida (x, z) -> 0..1 para llamarla cientos de miles de veces."""
        if self.vacia():
            return lambda x, z: 0.0
        if self.llena():
            x0, z0, x1, z1 = self.caja
            return lambda x, z: 1.0 if (x0 <= x <= x1 and z0 <= z <= z1) else 0.0
        return self.valor

    def llena(self):
        return self.datos.count(255) == len(self.datos)

    def vacia(self):
        return self.datos.count(0) == len(self.datos)

    def cobertura(self):
        """Fracción de la superficie con hierba (0 a 1)."""
        return sum(self.datos) / (255.0 * len(self.datos))

    # --- pintar -------------------------------------------------------------------

    def llenar(self, valor=255):
        self.datos = bytearray([int(valor)]) * (self.ancho * self.alto)

    def pintar(self, x, z, radio, fuerza=1.0, modo="poner", dureza=0.5):
        """Un toque de pincel en (x, z) con ``radio`` (en las unidades del suelo).

        ``modo``: «poner», «quitar» o «suavizar». ``dureza`` es la parte del
        radio que se pinta entera; el resto se difumina hasta el borde.
        Devuelve cuántas casillas han cambiado.
        """
        cx, cz = self.tam_casilla
        gx, gz = self._a_rejilla(x, z)
        rx, rz = radio / cx, radio / cz
        i0, i1 = max(0, int(math.floor(gx - rx))), min(self.ancho - 1, int(math.ceil(gx + rx)))
        j0, j1 = max(0, int(math.floor(gz - rz))), min(self.alto - 1, int(math.ceil(gz + rz)))
        if i0 > i1 or j0 > j1:
            return 0
        fuerza = min(1.0, max(0.0, fuerza))
        dureza = min(0.99, max(0.0, dureza))
        original = self.datos[:] if modo == "suavizar" else None
        cambios = 0
        w = self.ancho
        for j in range(j0, j1 + 1):
            for i in range(i0, i1 + 1):
                d = math.hypot((i - gx) * cx, (j - gz) * cz) / radio if radio > 0 else 2.0
                if d > 1.0:
                    continue
                peso = 1.0 if d <= dureza else 1.0 - (d - dureza) / (1.0 - dureza)
                peso = peso * peso * (3 - 2 * peso) * fuerza
                k = j * w + i
                v = self.datos[k]
                if modo == "poner":
                    nuevo = v + (255 - v) * peso
                elif modo == "quitar":
                    nuevo = v * (1.0 - peso)
                else:
                    media = _media(original, w, self.alto, i, j)
                    nuevo = v + (media - v) * peso
                nuevo = int(round(nuevo))
                if nuevo != v:
                    self.datos[k] = nuevo
                    cambios += 1
        return cambios

    # --- guardar ------------------------------------------------------------------

    def a_texto(self):
        cabecera = "{}|{}|{}".format(self.ancho, self.alto, ",".join(repr(round(c, 4)) for c in self.caja))
        return cabecera + "|" + base64.b64encode(zlib.compress(bytes(self.datos), 9)).decode("ascii")

    @classmethod
    def desde_texto(cls, texto):
        """La máscara guardada, o None si el texto está vacío o roto."""
        try:
            ancho, alto, caja, datos = texto.split("|", 3)
            ancho, alto = int(ancho), int(alto)
            caja = tuple(float(c) for c in caja.split(","))
            crudo = zlib.decompress(base64.b64decode(datos))
            if len(crudo) != ancho * alto or len(caja) != 4:
                return None
        except (ValueError, AttributeError, zlib.error, TypeError):
            return None
        m = cls(caja, 0, ancho, alto)
        m.datos = bytearray(crudo)
        return m

    def ajustada_a(self, caja):
        """Copia de esta máscara sobre otra caja (si el suelo ha cambiado de tamaño)."""
        nueva = Mascara(caja, 0)
        x0, z0, x1, z1 = nueva.caja
        cx, cz = nueva.tam_casilla
        for j in range(nueva.alto):
            z = z0 + (j + 0.5) * cz
            for i in range(nueva.ancho):
                nueva.datos[j * nueva.ancho + i] = int(round(self.valor(x0 + (i + 0.5) * cx, z) * 255))
        return nueva


def _lado(tamano):
    return int(min(MAXIMO, max(MINIMO, math.ceil(tamano / CASILLA))))


def _media(datos, w, h, i, j):
    total, n = 0, 0
    for jj in range(max(0, j - 1), min(h, j + 2)):
        for ii in range(max(0, i - 1), min(w, i + 2)):
            total += datos[jj * w + ii]
            n += 1
    return total / float(n)
