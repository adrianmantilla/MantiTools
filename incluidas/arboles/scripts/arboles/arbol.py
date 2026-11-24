"""Un árbol: sus módulos, su receta en JSON y sus mallas por nivel de detalle.

La receta guarda solo parámetros, nunca mallas: con ella el árbol se vuelve a
construir a cualquier resolución, en cualquier escena.
"""

import copy
import json

from arboles import follaje
from arboles import modulos as mod

VERSION_RECETA = 1
_DORADO = 137.5

# Semáforo de polígonos: triángulos de un árbol generado (calidad media) para
# que un jardín de 50 árboles se pueda renderizar en un ordenador del aula.
SEMAFORO = ((40000, "verde"), (80000, "amarillo"))

# Juegos de texturas de las especies de serie. Las recetas guardadas antes de que hubiera
# texturas no traen «material»: si su nombre es el de una especie, usan sus texturas.
ESPECIES_CON_TEXTURAS = ("roble", "haya", "pino_pinonero", "abeto", "abedul", "sauce_lloron", "cipres",
                         "olivo", "arbusto", "encina", "platano", "chopo", "castano", "arce", "arce_otono",
                         "alcornoque", "arbol_seco", "almendro", "palmera")
_ALIAS_MATERIAL = {
    "lloron": "sauce_lloron", "sauce": "sauce_lloron", "conifera": "abeto", "columnar": "chopo",
    "copa_redonda": "roble", "platano_de_sombra": "platano", "almendro_en_flor": "almendro",
    "arce_en_otono": "arce_otono", "pino": "pino_pinonero", "arbusto_sencillo": "arbusto",
    "abedul_sencillo": "abedul",
}


def material_por_nombre(nombre):
    """Especie que corresponde a un nombre de árbol («Llorón», «Abedul_frondosa»…), o «clay»."""
    import re
    import unicodedata
    clave = unicodedata.normalize("NFKD", nombre or "").encode("ascii", "ignore").decode("ascii").lower()
    clave = re.sub(r"[^a-z0-9]+", "_", clave).strip("_")
    for _ in range(2):  # «abedul_frondosa_2» → «abedul»
        clave = re.sub(r"_(\d+|clara|normal|frondosa)$", "", clave)
    clave = _ALIAS_MATERIAL.get(clave, clave)
    return clave if clave in ESPECIES_CON_TEXTURAS else "clay"


class Arbol(object):
    def __init__(self, nombre="arbol", escala_textura=60.0, material="clay"):
        self.nombre = nombre
        self.material = material or "clay"  # juego de texturas (ver texturas.py) o «clay»
        self.escala_textura = float(escala_textura)  # cm que ocupa una repetición de la textura de corteza
        self.modulos = {}   # id -> Modulo, en orden de creación
        self._contador = {}

    # --- edición ---

    def _nuevo_id(self, tipo):
        n = self._contador.get(tipo, 0) + 1
        while "{}{}".format(tipo, n) in self.modulos:
            n += 1
        self._contador[tipo] = n
        return "{}{}".format(tipo, n)

    @property
    def tronco(self):
        return next((m for m in self.modulos.values() if m.tipo == mod.TRONCO), None)

    def anadir_tronco(self, **valores):
        if self.tronco:
            raise ValueError("el árbol ya tiene tronco")
        m = mod.Modulo(self._nuevo_id(mod.TRONCO), mod.TRONCO, None, valores)
        self.modulos[m.id] = m
        return m

    def anadir_rama(self, padre, **valores):
        padre = getattr(padre, "id", padre)
        if padre not in self.modulos:
            raise KeyError("no existe el módulo {}".format(padre))
        m = mod.Modulo(self._nuevo_id(mod.RAMA), mod.RAMA, padre, valores)
        self.modulos[m.id] = m
        return m

    def hijos(self, id_):
        return [m for m in self.modulos.values() if m.padre == id_]

    def descendientes(self, id_):
        resultado = []
        for hijo in self.hijos(id_):
            resultado.append(hijo.id)
            resultado += self.descendientes(hijo.id)
        return resultado

    def subarbol(self, id_):
        """Diccionario con la rama ``id_`` y todo lo que cuelga de ella."""
        return {"raiz": id_, "modulos": [self.modulos[i].a_dict() for i in [id_] + self.descendientes(id_)]}

    def injertar(self, subarbol, padre, **cambios):
        """Copia un subárbol bajo ``padre`` con ids nuevos; ``cambios`` van a la raíz."""
        padre = getattr(padre, "id", padre)
        nuevos = {}
        raiz = None
        for datos in subarbol["modulos"]:
            datos = copy.deepcopy(datos)
            nueva_madre = padre if datos["id"] == subarbol["raiz"] else nuevos[datos["padre"]]
            m = self.anadir_rama(nueva_madre, **datos["valores"])
            for i, d in (datos.get("curva") or {}).items():
                m.fijar_control(int(i), d)
            nuevos[datos["id"]] = m.id
            if datos["id"] == subarbol["raiz"]:
                raiz = m
        for nombre, valor in cambios.items():
            raiz.fijar(nombre, valor)
        return raiz

    def repetir_alrededor(self, id_, copias):
        """Reparte ``copias`` más de la rama alrededor de su madre, con el ángulo dorado."""
        original = self.modulos[id_]
        if original.tipo != mod.RAMA:
            raise ValueError("solo se pueden repetir ramas")
        sub = self.subarbol(id_)
        nuevas = []
        for k in range(1, copias + 1):
            posicion = original.valores["posicion"] + (0.06 * ((k + 1) // 2)) * (1 if k % 2 else -1)
            nuevas.append(self.injertar(
                sub, original.padre,
                giro=(original.valores["giro"] + k * _DORADO) % 360.0,
                posicion=min(1.0, max(0.0, posicion))))
        return nuevas

    def pegar_ajustes(self, valores, destinos):
        """Copia ``valores`` en los módulos del mismo tipo, salvo dónde nacen."""
        cambiados = []
        for id_ in destinos:
            m = self.modulos[id_]
            for nombre, valor in valores.items():
                if nombre in mod.PARAMETROS[m.tipo] and nombre not in mod.PARAMETROS_DE_SITIO:
                    m.fijar(nombre, valor)
            cambiados.append(id_)
        return cambiados

    def quitar(self, id_):
        """Quita el módulo y todo lo que cuelga de él."""
        for hijo in self.hijos(id_):
            self.quitar(hijo.id)
        self.modulos.pop(id_, None)

    # --- cálculo ---

    def _orden(self):
        """Módulos con cada madre antes que sus hijas."""
        hechos, orden = set(), []
        pendientes = list(self.modulos.values())
        while pendientes:
            avance = False
            for m in list(pendientes):
                if m.padre is None or m.padre in hechos:
                    orden.append(m)
                    hechos.add(m.id)
                    pendientes.remove(m)
                    avance = True
            if not avance:
                raise ValueError("hay ramas sin madre: {}".format([m.id for m in pendientes]))
        return orden

    def calcular(self):
        for m in self._orden():
            if m.tipo == mod.TRONCO:
                m.guia = mod.guia_tronco(m)
            else:
                m.guia = mod.guia_rama(m, self.modulos[m.padre].guia)
        return self

    def mallas(self, nivel="denso"):
        self.calcular()
        return [mod.malla_modulo(m.guia, nivel, m.id, m.valores["torsion"], self.escala_textura)
                for m in self._orden()]

    def follaje(self):
        """{id de rama: (tipo, [matrices])} con la guía ya calculada."""
        self.calcular()
        resultado = {}
        for m in self.modulos.values():
            if m.tipo == mod.RAMA:
                matrices = follaje.colocar(m)
                if matrices:
                    resultado[m.id] = (m.valores["follaje"], matrices)
        return resultado

    def triangulos(self, nivel, con_follaje=True):
        total = sum(malla.triangulos for malla in self.mallas(nivel))
        if con_follaje:
            for tipo, matrices in self.follaje().values():
                total += len(matrices) * follaje.triangulos_prototipo(tipo, nivel)
        return total

    def semaforo(self, nivel="medio"):
        triangulos = self.triangulos(nivel)
        for limite, color in SEMAFORO:
            if triangulos <= limite:
                return color, triangulos
        return "rojo", triangulos

    def copiar(self):
        return Arbol.de_dict(self.a_dict())

    # --- receta ---

    def hojas_propias(self):
        """Nombres de las hojas propias (del alumno) que usan sus ramas."""
        return sorted({m.valores["follaje"][len(follaje.PROPIA):] for m in self.modulos.values()
                       if follaje.es_propia(m.valores.get("follaje"))})

    def a_dict(self):
        datos = {"version": VERSION_RECETA, "nombre": self.nombre, "escala_textura": self.escala_textura,
                 "material": self.material, "modulos": [m.a_dict() for m in self.modulos.values()]}
        propias = {n: follaje.HOJAS_PROPIAS[n] for n in self.hojas_propias() if n in follaje.HOJAS_PROPIAS}
        if propias:  # la receta lleva sus hojas propias: funciona en cualquier ordenador
            datos["hojas_propias"] = propias
        return datos

    def a_json(self):
        return json.dumps(self.a_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def de_dict(cls, datos):
        nombre = datos.get("nombre", "arbol")
        for hoja, malla in datos.get("hojas_propias", {}).items():
            follaje.registrar_hoja(hoja, malla)
        material = datos["material"] if "material" in datos else material_por_nombre(nombre)
        arbol = cls(nombre, datos.get("escala_textura", 60.0), material)
        for d in datos.get("modulos", []):
            m = mod.Modulo.de_dict(d)
            arbol.modulos[m.id] = m
        arbol._orden()  # valida madres
        return arbol

    @classmethod
    def de_json(cls, texto):
        return cls.de_dict(json.loads(texto))
