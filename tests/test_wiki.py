"""La wiki (docs/wiki): HTML al día con sus .md, enlaces e imágenes que existen, y la orden que la abre."""

import os
import re
import sys
import unittest

import comun  # noqa: F401  (rutas del pack)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "herramientas"))

import generar_wiki as gw  # noqa: E402
from mantitools import herramientas as hr  # noqa: E402
from mantitools import wiki  # noqa: E402


class PruebaWiki(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archivos, cls.faltan = gw.construir()

    def test_todas_las_paginas_tienen_md(self):
        self.assertEqual(self.faltan, [])

    def test_cada_herramienta_tiene_pagina(self):
        for ident in hr.ORDEN:
            self.assertIn(ident + ".html", self.archivos)
            self.assertEqual(wiki.pagina_de(ident), ident)
        self.assertEqual(wiki.pagina_de("mantitools"), "index")

    def test_html_al_dia(self):
        for relativa, texto in self.archivos.items():
            ruta = os.path.join(gw.WIKI, *relativa.split("/"))
            self.assertTrue(os.path.isfile(ruta), "falta " + relativa + ": ejecuta herramientas/generar_wiki.py")
            with open(ruta, encoding="utf-8") as f:
                self.assertEqual(f.read(), texto, relativa + " está viejo: ejecuta herramientas/generar_wiki.py")

    def test_enlaces_e_imagenes_existen(self):
        anclas = {}
        for relativa, texto in self.archivos.items():
            if relativa.endswith(".html"):
                anclas[relativa] = set(re.findall(r'id="([^"]+)"', texto))
        for relativa, texto in self.archivos.items():
            if not relativa.endswith(".html"):
                continue
            for destino in re.findall(r'(?:href|src)="([^"]+)"', texto):
                if re.match(r"^[a-z]+:", destino):
                    continue
                ruta, _, frag = destino.partition("#")
                if not ruta:
                    ruta = relativa
                else:
                    self.assertTrue(os.path.exists(os.path.join(gw.WIKI, *ruta.split("/"))),
                                    "{}: no existe {}".format(relativa, destino))
                if frag and ruta.endswith(".html"):
                    self.assertIn(frag, anclas.get(ruta, set()), "{}: no hay sección #{} en {}".format(
                        relativa, frag, ruta))

    def test_markdown(self):
        html, titulo, titulos = gw.bloques("# T\n\nUn **a** y `b`.\n\n## Sección dos\n\n> **Consejo:** hola\n\n"
                                           "- uno\n  - dos\n\n| x | y |\n|---|---|\n| 1 | 2 |\n\n"
                                           "![alt](img/a.png)\n\n*Pie.*\n\n[p](otra.md#s)\n")
        self.assertEqual(titulo, "T")
        self.assertEqual(titulos, [(2, "Sección dos", "seccion-dos")])
        for trozo in ("<strong>a</strong>", "<code>b</code>", 'class="aviso consejo"', "<ul><li>uno<ul><li>dos",
                      "<td>1</td>", "<figcaption>Pie.</figcaption>", 'href="otra.html#s"'):
            self.assertIn(trozo, html)


if __name__ == "__main__":
    unittest.main()
