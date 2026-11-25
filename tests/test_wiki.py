"""La wiki (docs/wiki): una página por herramienta, sin enlaces ni imágenes rotos, y se abre desde el pack."""

import os
import re
import unittest

import comun
from mantitools import herramientas as hr

WIKI = os.path.join(comun.RAIZ, "docs", "wiki")
ENLACE_HTML = re.compile(r'(?:href|src)="([^"]+)"')
ENLACE_MD = re.compile(r'!?\[[^\]]*\]\(([^)\s]+)\)|<img src="([^"]+)"')


def paginas(extension):
    return sorted(f for f in os.listdir(WIKI) if f.endswith(extension))


def _locales(enlaces):
    for enlace in enlaces:
        if not enlace or enlace.startswith(("http://", "https://", "mailto:", "#")):
            continue
        yield enlace


class Wiki(unittest.TestCase):
    def test_una_pagina_por_herramienta(self):
        for f in hr.FICHAS:
            for extension in (".md", ".html"):
                self.assertTrue(os.path.isfile(os.path.join(WIKI, f.id + extension)), f.id + extension)
            with open(os.path.join(WIKI, f.id + ".md"), encoding="utf-8") as archivo:
                self.assertIn("herramienta: {}\n".format(f.id), archivo.read())

    def test_cada_md_tiene_su_html(self):
        self.assertEqual([p[:-3] for p in paginas(".md")], [p[:-5] for p in paginas(".html")])

    def test_html_sin_enlaces_rotos(self):
        anclas = {}
        for pagina in paginas(".html"):
            with open(os.path.join(WIKI, pagina), encoding="utf-8") as archivo:
                anclas[pagina] = set(re.findall(r'id="([^"]+)"', archivo.read()))
        for pagina in paginas(".html"):
            with open(os.path.join(WIKI, pagina), encoding="utf-8") as archivo:
                texto = archivo.read()
            for enlace in _locales(ENLACE_HTML.findall(texto)):
                ruta, _, ancla = enlace.partition("#")
                destino = os.path.normpath(os.path.join(WIKI, ruta))
                self.assertTrue(os.path.isfile(destino), "{}: {}".format(pagina, enlace))
                if ancla and ruta.endswith(".html"):
                    self.assertIn(ancla, anclas[os.path.basename(ruta)], "{}: {}".format(pagina, enlace))

    def test_md_sin_enlaces_rotos(self):
        """En GitHub se leen los .md: sus enlaces e imágenes también tienen que existir."""
        for pagina in paginas(".md"):
            with open(os.path.join(WIKI, pagina), encoding="utf-8") as archivo:
                texto = re.sub(r"```.*?```", "", archivo.read(), flags=re.S)
            for enlace in _locales(a or b for a, b in ENLACE_MD.findall(texto)):
                ruta = enlace.partition("#")[0]
                self.assertTrue(os.path.isfile(os.path.normpath(os.path.join(WIKI, ruta))),
                                "{}: {}".format(pagina, enlace))

    def test_bloques_automaticos_rellenos(self):
        for pagina in paginas(".md"):
            with open(os.path.join(WIKI, pagina), encoding="utf-8") as archivo:
                texto = archivo.read()
            self.assertNotRegex(texto, r"<!-- auto:[\w -]+ -->\n<!-- /auto -->", pagina)

    def test_documentacion_encuentra_las_paginas(self):
        from mantitools import documentacion
        self.assertTrue(documentacion.ruta().endswith("index.html"))
        self.assertEqual(documentacion.pagina_de("muro"), "muro")
        self.assertEqual(documentacion.pagina_de("mantitools"), "index")
        self.assertEqual(documentacion.pagina_de("no_existe"), "index")
        self.assertEqual(documentacion.ruta("no_existe"), "")

    def test_paginas_del_estante_existen(self):
        from mantitools import estante
        for pagina, _texto in estante.PAGINAS_WIKI:
            self.assertTrue(os.path.isfile(os.path.join(WIKI, pagina + ".html")), pagina)


if __name__ == "__main__":
    unittest.main()
