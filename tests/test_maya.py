"""El pack dentro de un Maya falso: arranque, menú con submenús, estante, acciones y ajustes.

No sustituye a la prueba en Maya (``herramientas/prueba_maya.py``), pero comprueba
que cada herramienta incluida responde al contrato del pack.
"""

import importlib
import sys
import unittest

import comun
import maya_falso


def setUpModule():
    global cmds, mel
    comun.aplicacion()
    cmds, mel = maya_falso.instalar()


def tearDownModule():
    maya_falso.quitar()


class Arranque(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from mantitools import carga
        cls.carga = carga
        carga._estado.update(ajustes=None, clase=None, fallos={})
        carga.iniciar()

    def test_carga_todas_las_herramientas_desde_el_pack(self):
        from mantitools import herramientas as hr
        for ficha in hr.FICHAS:
            self.assertTrue(self.carga.cargada(ficha.id), ficha.id)
            self.assertEqual(self.carga.fallo(ficha.id), "")

    def test_submenus_dentro_de_mantitools_en_orden(self):
        from mantitools import herramientas as hr
        from mantitools import menu
        elementos = cmds.menus[menu.MENU]
        corte = elementos.index(menu.SEPARADOR)
        self.assertEqual(elementos[:corte], [f.menu for f in hr.FICHAS])
        for ficha in hr.FICHAS:
            self.assertTrue(cmds.menus.get(ficha.menu), "{} sin entradas".format(ficha.menu))

    def test_ninguna_herramienta_crea_menu_arriba(self):
        from mantitools import herramientas as hr
        from mantitools import menu
        dentro = set(cmds.menus[menu.MENU])
        for ficha in hr.FICHAS:
            self.assertIn(ficha.menu, dentro)

    def test_rehacer_el_menu_no_duplica(self):
        from mantitools import herramientas as hr
        from mantitools import menu
        menu.construir()
        menu.construir()
        elementos = cmds.menus[menu.MENU]
        for ficha in hr.FICHAS:
            self.assertEqual(elementos.count(ficha.menu), 1, ficha.id)

    def test_estante_un_boton_por_herramienta_y_el_centro(self):
        from mantitools import estante
        from mantitools import herramientas as hr
        estante.crear(forzar=True)
        botones = [k for nombre, k in [(c[0], c[1]) for c in cmds.llamadas if c[0] == "shelfButton"]]
        ultimos = botones[-(len(hr.FICHAS) + 1):]
        self.assertEqual([b["label"] for b in ultimos], [f.nombre for f in hr.FICHAS] + ["MantiTools"])
        self.assertEqual(len(cmds.estantes[estante.ESTANTE]), len(hr.FICHAS) + 1)
        for b in ultimos:
            self.assertEqual(len(b.get("menuItem", [])), len(b.get("menuItemPython", [])))

    def test_estante_de_la_instalacion_usa_rutas_y_luego_nombres(self):
        import os
        from mantitools import estante
        estante._sesion["rutas"] = False
        botones = estante.botones(ruta_completa=True)
        for _, _, imagen, _, _ in botones:
            self.assertTrue(os.path.isfile(imagen), imagen)
        self.assertEqual([b[2] for b in estante.botones()][-1], "mantitools_centro.png")

    def test_desactivar_quita_submenu_y_boton(self):
        from mantitools import estante, menu
        self.carga.cambiar_activa("muro", False)
        try:
            self.assertFalse(self.carga.cargada("muro"))
            self.assertNotIn("MuroMenu", cmds.menus[menu.MENU])
            self.assertEqual(len(cmds.estantes[estante.ESTANTE]), 7)
        finally:
            self.carga.cambiar_activa("muro", True)
        self.assertIn("MuroMenu", cmds.menus[menu.MENU])

    def test_el_profesor_puede_desactivar(self):
        import json
        import os
        import tempfile
        carpeta = tempfile.mkdtemp()
        with open(os.path.join(carpeta, "mantitools_clase.json"), "w") as f:
            json.dump({"desactivar": ["radial"]}, f)
        self.carga.ajustes()["carpeta_clase"] = carpeta
        try:
            self.carga.releer_clase()
            self.assertFalse(self.carga.activa("radial"))
            self.assertIsNone(__import__("mantitools.menu", fromlist=["x"]).lugar_para("radial"))
        finally:
            self.carga.ajustes()["carpeta_clase"] = ""
            self.carga.releer_clase()


class Acciones(unittest.TestCase):
    def test_codigo_del_estante(self):
        from mantitools.acciones import codigo_estante
        espacio = {}
        codigo = codigo_estante("radial", "alternar")
        compile(codigo, "<estante>", "exec")
        self.assertIn("'radial'", codigo)
        self.assertEqual(espacio, {})

    def test_convertir_a_openpbr(self):
        """La orden del pack llama a la de cada herramienta que la tiene y resume lo hecho."""
        from unittest import mock

        from mantitools import acciones
        llamadas = []

        def falsa(ident, clave=None):
            llamadas.append((ident, clave))
            return ["{}_mat".format(ident)] if ident == "trepadora" else []

        with mock.patch.object(acciones, "ejecutar", falsa):
            hechos = acciones.convertir_a_openpbr()
        self.assertEqual(sorted(llamadas), [("arboles", "openpbr"), ("trepadora", "openpbr")])
        self.assertEqual(hechos, {"Trepadora": ["trepadora_mat"], "Árboles": []})
        self.assertIn("Trepadora: 1", acciones.resumen_openpbr(hechos))
        self.assertNotIn("Trepadora", acciones.resumen_openpbr({"Trepadora": []}))

    def test_cada_accion_importa_su_modulo(self):
        from mantitools import herramientas as hr
        for ficha in hr.FICHAS:
            for accion in ficha.acciones:
                modulo = accion.codigo.split()[1]
                importlib.import_module(modulo)


class PaginasDeAjustes(unittest.TestCase):
    """Cada control de la ventana central lee y escribe en la herramienta de verdad."""

    def test_carpeta_del_complemento_de_painter(self):
        import os
        import tempfile
        from mantitools import adaptadores as ad
        from mantitools import carga, painter
        pagina = ad.pagina("materials", None)
        primera, segunda = tempfile.mkdtemp(), tempfile.mkdtemp()
        try:
            pagina.escribir("carpeta_complemento", primera)
            self.assertEqual(pagina.leer("carpeta_complemento"), primera)
            self.assertFalse(painter.instalado(primera))
            self.assertIn(primera, pagina.boton("instalar_complemento"))
            self.assertTrue(painter.instalado(primera))
            # Al cambiar de carpeta, el complemento se mueve con ella
            pagina.escribir("carpeta_complemento", segunda)
            self.assertTrue(painter.instalado(segunda))
            self.assertFalse(painter.instalado(primera))
            # Elegir la de por defecto la deja vacía en los ajustes
            pagina.escribir("carpeta_complemento", painter.carpeta_por_defecto())
            self.assertEqual(carga.ajustes()["carpeta_painter"], "")
        finally:
            carga.ajustes()["carpeta_painter"] = ""
            painter.quitar(painter.carpeta_por_defecto())

    def test_leer_y_escribir_cada_control(self):
        from mantitools import adaptadores as ad
        from mantitools import herramientas as hr
        for ficha in hr.FICHAS:
            pagina = ad.pagina(ficha.id, None)
            controles = [c for _, lista in pagina.secciones() for c in lista]
            self.assertTrue(controles, ficha.id)
            for control in controles:
                if control.tipo in ("boton", "info"):
                    continue
                with self.subTest(herramienta=ficha.id, clave=control.clave):
                    valor = pagina.leer(control.clave)
                    pagina.escribir(control.clave, valor)
                    self.assertEqual(pagina.leer(control.clave), valor)

    def test_opciones_validas(self):
        from mantitools import adaptadores as ad
        from mantitools import herramientas as hr
        for ficha in hr.FICHAS:
            pagina = ad.pagina(ficha.id, None)
            for _, lista in pagina.secciones():
                for control in lista:
                    if control.tipo == "opciones":
                        valores = [o[0] for o in control.opciones]
                        self.assertIn(pagina.leer(control.clave), valores, "{} {}".format(ficha.id, control.clave))


if __name__ == "__main__":
    unittest.main()
