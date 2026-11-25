"""La ventana central sin Maya (Qt offscreen), con unos servicios falsos."""

import unittest

import comun
from mantitools import adaptadores as ad
from mantitools import herramientas as hr
from mantitools.ajustes import Ajustes
from mantitools.clase import Clase


class PaginaFalsa(ad.Pagina):
    ident = "muro"

    def __init__(self, clase=None):
        super(PaginaFalsa, self).__init__(clase)
        self.valores = {"abrir_con_escena": True, "opacidad": 0.5}

    def secciones(self):
        return [("General", [ad.Control("casilla", "abrir_con_escena", "Abrir con la escena"),
                             ad.Control("decimal", "opacidad", "Opacidad", minimo=0.0, maximo=1.0)])]

    def leer(self, clave):
        return self.valores[clave]

    def escribir(self, clave, valor):
        self.valores[clave] = valor


class ServiciosFalsos(object):
    def __init__(self, carpeta):
        self._ajustes = Ajustes(carpeta)
        self.ejecutadas = []
        self.cambios = []
        self.paginas = {}

    def activa(self, ident):
        return self._ajustes.activa(ident)

    def desactivada_por_profesor(self, ident):
        return False

    def cargada(self, ident):
        return self.activa(ident)

    def fallo(self, ident):
        return ""

    def version(self, ident):
        return "1.0.0"

    def ejecutar(self, ident, clave):
        self.ejecutadas.append((ident, clave))

    def cambiar_activa(self, ident, valor):
        self.cambios.append((ident, valor))
        self._ajustes.fijar_activa(ident, valor)

    def ajustes(self):
        return self._ajustes

    def clase(self):
        return Clase("")

    def pagina(self, ident):
        return self.paginas.setdefault(ident, PaginaFalsa())

    def tras_escribir(self, pagina):
        pass

    def cambiar_idioma(self, codigo):
        self._ajustes["idioma"] = codigo

    def cambiar_carpeta_clase(self, ruta):
        self._ajustes["carpeta_clase"] = ruta

    def recrear_estante(self):
        pass

    def informe(self):
        return True, ["✓ todo"]

    def guia(self, ident):
        return ""


class Centro(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.app = comun.aplicacion()
        from mantitools import centro
        self.servicios = ServiciosFalsos(tempfile.mkdtemp())
        self.v = centro.VentanaCentro(self.servicios)
        self.v.resize(800, 600)
        self.v.show()
        self.app.processEvents()

    def tearDown(self):
        self.v.close()
        self.v.deleteLater()

    def test_una_tarjeta_por_herramienta(self):
        self.assertEqual([t.ficha.id for t in self.v.tarjetas], [f.id for f in hr.FICHAS])

    def test_pestanas(self):
        for i, nombre in enumerate(("herramientas", "ajustes", "ayuda")):
            self.v.ir_a(nombre)
            self.assertEqual(self.v.pestanas.currentIndex(), i)

    def test_boton_principal_ejecuta(self):
        tarjeta = self.v.tarjetas[hr.ORDEN.index("radial")]
        tarjeta.boton_abrir.click()
        self.assertEqual(self.servicios.ejecutadas, [("radial", hr.ficha("radial").principal)])

    def test_comprobar_muestra_informe(self):
        self.v.ir_a("ayuda")
        self.v._comprobar()
        self.assertIn("todo", self.v.informe.toPlainText())

    def test_actualizar_tras_desactivar(self):
        self.servicios.cambiar_activa("muro", False)
        self.v.actualizar()
        self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
