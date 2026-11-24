"""Fichas, textos, iconos y copias del kit: todo lo que el pack da por hecho de cada herramienta."""

import ast
import json
import os
import re
import unittest

import comun  # noqa: F401  (rutas)
from mantitools import herramientas as hr
from mantitools import iconos

RAIZ = comun.RAIZ


def _json(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def _nombres(ident, modulo):
    """Funciones, clases y variables de nivel de módulo de ``modulo`` dentro de la copia incluida."""
    ruta = os.path.join(comun.INCLUIDAS, ident, "scripts", *modulo.split(".")) + ".py"
    if not os.path.isfile(ruta):
        ruta = ruta[:-3] + os.sep + "__init__.py"
    with open(ruta, encoding="utf-8") as f:
        arbol = ast.parse(f.read())
    nombres = set()
    for nodo in arbol.body:
        if isinstance(nodo, (ast.FunctionDef, ast.ClassDef)):
            nombres.add(nodo.name)
        elif isinstance(nodo, ast.Assign):
            nombres.update(t.id for t in nodo.targets if isinstance(t, ast.Name))
    return nombres


class Fichas(unittest.TestCase):
    def test_orden_y_ids(self):
        self.assertEqual([f.id for f in hr.FICHAS], list(hr.ORDEN))
        self.assertEqual(len({f.menu for f in hr.FICHAS}), len(hr.FICHAS))

    def test_la_principal_es_una_accion(self):
        for f in hr.FICHAS:
            self.assertEqual(f.accion(f.principal).clave, f.principal, f.id)
            self.assertNotIn(f.principal, [a.clave for a in f.secundarias])

    def test_cada_herramienta_esta_incluida(self):
        for f in hr.FICHAS:
            carpeta = os.path.join(comun.INCLUIDAS, f.id)
            self.assertTrue(os.path.isfile(os.path.join(carpeta, "plug-ins", f.plugin + ".py")), f.id)
            self.assertTrue(os.path.isfile(os.path.join(carpeta, "scripts", f.paquete, "pack.py")), f.id)

    def test_menus_y_acciones_existen_en_cada_herramienta(self):
        for f in hr.FICHAS:
            modulo, funcion = hr.separar(f.crear_menu)
            self.assertIn(funcion, _nombres(f.id, modulo), f.crear_menu)
            for a in f.acciones:
                for mod, alias in re.findall(r"import ([\w.]+) as (_\w+)", a.codigo):
                    for llamada in re.findall(re.escape(alias) + r"\.(\w+)", a.codigo):
                        self.assertIn(llamada, _nombres(f.id, mod), "{} {}".format(f.id, a.clave))

    def test_versiones_registradas(self):
        versiones = _json(os.path.join(RAIZ, "versiones.json"))
        self.assertEqual(set(versiones), set(hr.ORDEN))
        for ident, datos in versiones.items():
            self.assertTrue(datos.get("version"), ident)


class Textos(unittest.TestCase):
    def setUp(self):
        carpeta = os.path.join(RAIZ, "scripts", "mantitools", "i18n")
        self.es = _json(os.path.join(carpeta, "es.json"))
        self.en = _json(os.path.join(carpeta, "en.json"))

    def test_mismas_claves_en_los_dos_idiomas(self):
        self.assertEqual(set(self.es), set(self.en))

    def test_textos_de_acciones_y_descripciones(self):
        for f in hr.FICHAS:
            self.assertIn("desc_" + f.id, self.es)
            for a in f.acciones:
                self.assertIn(f.texto(a.clave), self.es)

    def test_claves_usadas_en_el_codigo(self):
        usadas = set()
        carpeta = os.path.join(RAIZ, "scripts", "mantitools")
        for nombre in os.listdir(carpeta):
            if nombre.endswith(".py"):
                with open(os.path.join(carpeta, nombre), encoding="utf-8") as f:
                    usadas.update(re.findall(r'\bt\("([a-z0-9_]+)"', f.read()))
        with open(os.path.join(RAIZ, "instalar.py"), encoding="utf-8") as f:
            usadas.update(re.findall(r'\bt\("([a-z0-9_]+)"', f.read()))
        usadas = {c for c in usadas if not c.endswith("_")}  # prefijos: t("desc_" + id)
        self.assertEqual(sorted(usadas - set(self.es)), [])


class Iconos(unittest.TestCase):
    def test_hay_trazo_y_png_para_cada_icono(self):
        for ident in list(hr.ORDEN) + ["centro"]:
            self.assertIn(ident, iconos.TRAZOS)
            for sufijo in ("", "_150", "_200"):
                ruta = os.path.join(RAIZ, "icons", "mantitools_{}{}.png".format(ident, sufijo))
                self.assertTrue(os.path.isfile(ruta), ruta)

    def test_svg_con_fondo(self):
        texto = iconos.svg("radial", fondo="#a58bd6")
        self.assertIn('fill="#a58bd6"', texto)
        self.assertIn("scale(0.7)", texto)


class Copias(unittest.TestCase):
    """Cada herramienta lleva una copia idéntica del kit y del contrato del pack."""

    def _leer(self, *partes):
        with open(os.path.join(*partes), encoding="utf-8") as f:
            return f.read()

    def test_pack_py_igual_a_la_plantilla(self):
        plantilla = self._leer(RAIZ, "plantillas", "pack.py")
        for f in hr.FICHAS:
            copia = self._leer(comun.INCLUIDAS, f.id, "scripts", f.paquete, "pack.py")
            self.assertEqual(copia, plantilla.replace("{herramienta}", f.id), f.id)

    def test_estilo_igual_al_kit(self):
        kit = self._leer(RAIZ, "scripts", "mantitools", "estilo.py")
        for f in hr.FICHAS:
            if f.id in ("materials", "radial"):  # Materials es el original; Radial tiene diseño propio
                continue
            copia = self._leer(comun.INCLUIDAS, f.id, "scripts", f.paquete, "estilo.py")
            self.assertEqual(copia, kit, f.id)


if __name__ == "__main__":
    unittest.main()
