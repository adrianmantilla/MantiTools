"""Tipos de hierba: los preajustes del generador de matas.

Una «mata» es un grupo de briznas que se instancia muchas veces. Cada tipo
describe cómo es su mata (altura, número de briznas, curvatura...) y cuántas
matas hay por metro cuadrado. Las medidas van en centímetros, como trabaja Maya.

Los tipos de serie no se pueden borrar; el alumno puede editar sus valores en
la escena o guardar uno nuevo con otro nombre (``Tipo.desde_dict``).
"""

import json

VARIANTES = 6           # matas distintas de cada tipo
NIVELES = 3             # completa, simple, tarjeta
PROTOTIPOS_POR_TIPO = VARIANTES * NIVELES

CABEZAS = (None, "flor", "espiga", "trebol")


class Tipo(object):
    """Preajuste de un tipo de hierba."""

    CAMPOS = ("clave", "altura_min", "altura_max", "densidad", "briznas", "segmentos", "anchura",
              "curvatura", "abertura", "radio", "color_raiz", "color_punta", "cabeza", "cabezas",
              "color_cabeza", "color_cabeza2", "propio")

    def __init__(self, clave, altura_min, altura_max, densidad, briznas, segmentos, anchura,
                 curvatura, abertura, radio, color_raiz, color_punta, cabeza=None, cabezas=0,
                 color_cabeza=(1.0, 1.0, 1.0), color_cabeza2=None, propio=False):
        self.clave = clave
        self.altura_min = float(altura_min)      # cm
        self.altura_max = float(altura_max)      # cm
        self.densidad = float(densidad)          # matas por m²
        self.briznas = int(briznas)
        self.segmentos = int(segmentos)
        self.anchura = float(anchura)            # cm en la base de cada brizna
        self.curvatura = float(curvatura)        # 0 recta, 1 muy doblada
        self.abertura = float(abertura)          # grados que se abren las briznas
        self.radio = float(radio)                # cm: de dónde salen las briznas
        self.color_raiz = tuple(color_raiz)
        self.color_punta = tuple(color_punta)
        self.cabeza = cabeza                     # flor, espiga, trébol o nada
        self.cabezas = int(cabezas)              # tallos con cabeza
        self.color_cabeza = tuple(color_cabeza)
        self.color_cabeza2 = tuple(color_cabeza2) if color_cabeza2 else None
        self.propio = bool(propio)               # creado por el alumno

    @property
    def altura(self):
        """Altura media: a esta altura se construye la mata (las copias se escalan)."""
        return (self.altura_min + self.altura_max) / 2.0

    def a_dict(self):
        return {c: getattr(self, c) for c in self.CAMPOS}

    @classmethod
    def desde_dict(cls, datos):
        datos = dict(datos)
        return cls(**{c: datos[c] for c in cls.CAMPOS if c in datos})

    def copiar(self, **cambios):
        datos = self.a_dict()
        datos.update(cambios)
        return Tipo.desde_dict(datos)

    def validar(self):
        """Corrige valores fuera de rango (por ejemplo, escritos a mano en la escena)."""
        self.altura_min = max(0.5, self.altura_min)
        self.altura_max = max(self.altura_min, self.altura_max)
        self.densidad = min(2000.0, max(0.01, self.densidad))
        self.briznas = min(200, max(1, self.briznas))
        self.segmentos = min(10, max(1, self.segmentos))
        self.anchura = max(0.02, self.anchura)
        self.curvatura = min(1.0, max(0.0, self.curvatura))
        self.abertura = min(85.0, max(0.0, self.abertura))
        self.radio = max(0.0, self.radio)
        self.cabezas = min(self.briznas, max(0, self.cabezas))
        if self.cabeza not in CABEZAS:
            self.cabeza = None
        return self


def _t(*a, **k):
    return Tipo(*a, **k)


# clave, altura min-max (cm), matas/m², briznas, segmentos, anchura, curvatura, abertura, radio, colores
_SERIE = [
    _t("cesped", 6, 10, 100, 22, 4, 0.5, 0.25, 22, 4.5, (0.14, 0.30, 0.09), (0.40, 0.66, 0.24)),
    _t("silvestre", 25, 45, 60, 22, 4, 0.7, 0.45, 32, 7.0, (0.16, 0.28, 0.09), (0.55, 0.68, 0.28)),
    _t("seca", 30, 50, 50, 18, 4, 0.6, 0.6, 34, 7.0, (0.34, 0.32, 0.17), (0.80, 0.72, 0.44)),
    _t("trebol", 5, 12, 90, 9, 2, 0.15, 0.2, 35, 5.0, (0.12, 0.30, 0.10), (0.25, 0.52, 0.20),
       cabeza="trebol", cabezas=9, color_cabeza=(0.22, 0.50, 0.20)),
    _t("espigas", 40, 70, 35, 16, 4, 0.45, 0.35, 24, 5.0, (0.25, 0.34, 0.13), (0.78, 0.74, 0.46),
       cabeza="espiga", cabezas=5, color_cabeza=(0.86, 0.78, 0.50)),
    _t("juncos", 60, 120, 20, 16, 5, 0.55, 0.1, 14, 5.0, (0.16, 0.26, 0.10), (0.42, 0.56, 0.26)),
    _t("flores", 20, 40, 20, 14, 3, 0.45, 0.3, 30, 5.0, (0.15, 0.30, 0.11), (0.38, 0.56, 0.24),
       cabeza="flor", cabezas=3, color_cabeza=(0.95, 0.95, 0.92), color_cabeza2=(0.85, 0.12, 0.08)),
    _t("ornamental", 20, 30, 12, 40, 4, 0.35, 0.7, 55, 4.0, (0.30, 0.44, 0.47), (0.66, 0.80, 0.84)),
]

SERIE = {t.clave: t for t in _SERIE}
ORDEN = [t.clave for t in _SERIE]

# Para qué sirve cada tipo (para la interfaz y la documentación)
USOS = {
    "cesped": "uso_cesped", "silvestre": "uso_silvestre", "seca": "uso_seca", "trebol": "uso_trebol",
    "espigas": "uso_espigas", "juncos": "uso_juncos", "flores": "uso_flores", "ornamental": "uso_ornamental",
}


def de_serie(clave):
    """Copia del tipo de serie ``clave`` (para poder cambiarla sin tocar el original)."""
    return SERIE[clave].copiar()


class Catalogo(object):
    """Los tipos de una escena: los de serie más los editados o creados por el alumno."""

    def __init__(self, propios=None):
        self.tipos = {c: de_serie(c) for c in ORDEN}
        for datos in (propios or {}).values():
            tipo = Tipo.desde_dict(datos).validar()
            self.tipos[tipo.clave] = tipo

    def __contains__(self, clave):
        return clave in self.tipos

    def __getitem__(self, clave):
        return self.tipos[clave]

    def claves(self):
        extra = sorted(c for c in self.tipos if c not in SERIE)
        return ORDEN + extra

    def poner(self, tipo):
        self.tipos[tipo.clave] = tipo.validar()

    def cambiados(self):
        """Tipos que no son iguales a los de serie (lo que hay que guardar en la escena)."""
        return {c: t.a_dict() for c, t in self.tipos.items()
                if c not in SERIE or t.a_dict() != SERIE[c].a_dict()}

    def a_json(self):
        return json.dumps(self.cambiados(), sort_keys=True)

    @classmethod
    def desde_json(cls, texto):
        try:
            datos = json.loads(texto) if texto else {}
        except ValueError:
            datos = {}
        return cls(datos if isinstance(datos, dict) else {})


def clave_libre(nombre, ocupadas):
    """Clave válida y no usada para un tipo nuevo a partir del nombre que da el alumno."""
    import re
    import unicodedata
    base = unicodedata.normalize("NFKD", nombre or "").encode("ascii", "ignore").decode("ascii")
    base = re.sub(r"[^a-zA-Z0-9]+", "_", base).strip("_").lower() or "tipo"
    if base[0].isdigit():
        base = "t_" + base
    clave, n = base, 2
    while clave in ocupadas:
        clave = "{}_{}".format(base, n)
        n += 1
    return clave
