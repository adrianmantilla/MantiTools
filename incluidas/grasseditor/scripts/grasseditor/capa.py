"""Una capa de hierba: sus ajustes y el motor que calcula sus matas.

``AjustesCapa`` es lo que se guarda en el nodo de la capa (como JSON): la
mezcla de tipos, la densidad, la semilla, las caras, las reglas y las
opciones de rendimiento. La máscara pintada va aparte (es más grande).

``Motor`` guarda los resultados intermedios del reparto y solo recalcula lo
que hace falta: si cambias la máscara no vuelve a sembrar candidatas, y si
mueves la cámara no vuelve a aplicar las reglas.

Python puro: se prueba sin Maya.
"""

import base64
import json
import zlib
from array import array

from grasseditor import camara as cam
from grasseditor import estadisticas as est
from grasseditor import matas, reparto
from grasseditor.mascara import Mascara


class AjustesCapa(object):
    CAMPOS = ("mezcla", "densidad", "semilla", "escala_var", "inclinacion", "caras", "reglas", "opciones",
              "activa")

    def __init__(self, mezcla=None, densidad=100.0, semilla=1, escala_var=0.25, inclinacion=12.0, caras=None,
                 reglas=None, opciones=None, activa=True):
        self.mezcla = [list(m) for m in (mezcla or [["silvestre", 100.0]])]
        self.densidad = float(densidad)
        self.semilla = int(semilla)
        self.escala_var = float(escala_var)
        self.inclinacion = float(inclinacion)
        self.caras = sorted(set(int(c) for c in caras)) if caras else None
        self.reglas = reparto.Reglas.desde_dict(reglas).a_dict()
        self.opciones = cam.Opciones.desde_dict(opciones).a_dict()
        self.activa = bool(activa)

    def a_dict(self):
        return {c: getattr(self, c) for c in self.CAMPOS}

    def a_json(self):
        return json.dumps(self.a_dict(), sort_keys=True)

    @classmethod
    def desde_json(cls, texto):
        try:
            datos = json.loads(texto) if texto else {}
        except ValueError:
            datos = {}
        if not isinstance(datos, dict):
            datos = {}
        return cls(**{c: datos[c] for c in cls.CAMPOS if c in datos})

    def claves(self):
        return [m[0] for m in self.mezcla]


_CACHE_TRIANGULOS = {}


def triangulos_tipo(tipo):
    """[completa, simple, tarjeta] de ``tipo``, calculados una vez por definición."""
    clave = json.dumps(tipo.a_dict(), sort_keys=True)
    if clave not in _CACHE_TRIANGULOS:
        _CACHE_TRIANGULOS[clave] = matas.triangulos_por_nivel(tipo)
    return _CACHE_TRIANGULOS[clave]


# --- horneado ---------------------------------------------------------------------------

# Lo que hace falta después de la máscara y las reglas (que ya no se vuelven a aplicar).
_CAMPOS_HORNEADO = (("x", "f"), ("y", "f"), ("z", "f"), ("tipo", "B"), ("variante", "B"), ("escala", "f"),
                    ("giro", "f"), ("incl_x", "f"), ("incl_z", "f"), ("k_visor", "f"), ("k_aclarar", "f"))


def hornear(cand, aceptados):
    """Texto con las matas aceptadas, para guardarlo en la escena y no recalcular."""
    partes = []
    for nombre, tipo in _CAMPOS_HORNEADO:
        origen = getattr(cand, nombre)
        partes.append(array(tipo, (origen[i] for i in aceptados)).tobytes())
    cabecera = json.dumps({"n": len(aceptados), "claves": cand.claves}).encode("utf-8")
    crudo = len(cabecera).to_bytes(4, "little") + cabecera + b"".join(partes)
    return base64.b64encode(zlib.compress(crudo, 6)).decode("ascii")


def deshornear(texto):
    """Candidatas guardadas con ``hornear`` (todas aceptadas), o None si el texto no vale."""
    try:
        crudo = zlib.decompress(base64.b64decode(texto))
        largo = int.from_bytes(crudo[:4], "little")
        cabecera = json.loads(crudo[4:4 + largo].decode("utf-8"))
        n = int(cabecera["n"])
        cand = reparto.Candidatas(cabecera["claves"])
        pos = 4 + largo
        for nombre, tipo in _CAMPOS_HORNEADO:
            a = array(tipo)
            tam = a.itemsize * n
            a.frombytes(crudo[pos:pos + tam])
            pos += tam
            if len(a) != n:
                return None
            setattr(cand, nombre, a)
        return cand
    except (ValueError, KeyError, TypeError, zlib.error, UnicodeDecodeError):
        return None


class Motor(object):
    """Calcula las matas de una capa guardando los pasos intermedios.

    Las aceptadas se calculan cuando hacen falta: el visor solo necesita las
    de su porcentaje, así pintar con el pincel no obliga a revisar todas.
    """

    def __init__(self):
        self._clave_cand = None
        self._clave_reglas = None
        self._clave_horneado = None
        self._aceptadas = {}          # fracción del visor (o None = todas) -> índices
        self.horneada = False
        self.candidatas = None
        self.ajustes = AjustesCapa()
        self.catalogo = None
        self._mascara = None
        self._reglas = None

    def preparar(self, suelo, ajustes, catalogo, mascara_texto="", horneado=""):
        """Deja listas las candidatas y las reglas. Devuelve True si algo ha cambiado."""
        self.ajustes = ajustes
        self.catalogo = catalogo
        if horneado:
            if horneado == self._clave_horneado and self.candidatas is not None:
                return False
            cand = deshornear(horneado)
            if cand is not None:
                self._clave_horneado = horneado
                self.candidatas = cand
                self.horneada = True
                self._aceptadas = {None: array("l", range(len(cand)))}
                self._clave_cand = self._clave_reglas = None
                return True
        self._clave_horneado = None
        if self.horneada:
            self.horneada = False
            self._clave_cand = None
        tipos = {c: catalogo[c].a_dict() for c in ajustes.claves() if c in catalogo}
        clave_cand = json.dumps([suelo.huella() if suelo else 0, ajustes.mezcla, ajustes.densidad,
                                 ajustes.semilla, ajustes.caras, ajustes.escala_var, ajustes.inclinacion,
                                 tipos], sort_keys=True)
        cambio = False
        if clave_cand != self._clave_cand:
            if suelo is None:
                self.candidatas = reparto.Candidatas([])
            else:
                self.candidatas = reparto.candidatos(
                    suelo, ajustes.mezcla, catalogo, ajustes.densidad, ajustes.semilla, ajustes.caras,
                    ajustes.escala_var, ajustes.inclinacion)
            self._clave_cand = clave_cand
            self._clave_reglas = None
            cambio = True
        clave_reglas = (mascara_texto or "", json.dumps(ajustes.reglas, sort_keys=True))
        if clave_reglas != self._clave_reglas:
            self._mascara = Mascara.desde_texto(mascara_texto) if mascara_texto else None
            self._reglas = reparto.Reglas.desde_dict(ajustes.reglas)
            self._clave_reglas = clave_reglas
            self._aceptadas = {}
            cambio = True
        return cambio

    def aceptadas(self, fraccion=None):
        """Índices aceptados; con ``fraccion``, solo entre las que enseña el visor."""
        if self.candidatas is None:
            return array("l")
        if None in self._aceptadas:
            todas = self._aceptadas[None]
            if fraccion is None:
                return todas
            if fraccion not in self._aceptadas:
                K = self.candidatas.k_visor
                self._aceptadas[fraccion] = array("l", (i for i in todas if K[i] < fraccion))
            return self._aceptadas[fraccion]
        if fraccion not in self._aceptadas:
            self._aceptadas[fraccion] = reparto.aceptados(self.candidatas, self._mascara, self._reglas,
                                                          visor=fraccion)
        return self._aceptadas[fraccion]

    def opciones(self):
        return cam.Opciones.desde_dict(self.ajustes.opciones)

    def salida(self, camara=None, render=True):
        if not self.ajustes.activa or self.candidatas is None:
            return cam.Salida()
        opciones = self.opciones()
        fraccion = None if render else opciones.visor_porcentaje / 100.0
        return cam.salida(self.candidatas, self.aceptadas(fraccion), opciones, camara, render)

    def informe(self, camara=None):
        if self.candidatas is None or not self.ajustes.activa:
            return est.Informe()
        opciones = self.opciones()
        todas = self.aceptadas()
        recuento = cam.recuento(self.candidatas, todas, opciones, camara, True)
        visor = len(self.aceptadas(opciones.visor_porcentaje / 100.0))
        claves = self.candidatas.claves
        tris = {c: triangulos_tipo(self.catalogo[c]) for c in claves if c in self.catalogo}
        return est.informe_capa(claves, tris, recuento, len(todas), visor, opciones.a_dict(),
                                self.candidatas.recortadas)

    def horneado(self):
        return hornear(self.candidatas, self.aceptadas()) if self.candidatas is not None else ""
