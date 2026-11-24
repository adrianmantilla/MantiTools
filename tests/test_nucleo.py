"""Lo que no necesita Maya: ajustes, carpeta de clase, instalador y comprobación."""

import json
import os
import shutil
import tempfile
import unittest

import comun
import instalar
from mantitools import comprobar
from mantitools.ajustes import Ajustes
from mantitools.clase import Clase, subcarpeta


class Temporal(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)


class PruebaAjustes(Temporal):
    def test_por_defecto_todo_activo_y_en_espanol(self):
        a = Ajustes(self.dir)
        self.assertEqual(a.idioma, "es")
        self.assertTrue(a.activa("radial"))

    def test_guarda_y_relee(self):
        a = Ajustes(self.dir)
        a.fijar_activa("radial", False)
        a["idioma"] = "en"
        b = Ajustes(self.dir)
        self.assertFalse(b.activa("radial"))
        self.assertEqual(b.idioma, "en")
        b.fijar_activa("radial", True)
        self.assertEqual(Ajustes(self.dir)["activas"], {})

    def test_archivo_roto_o_valores_raros(self):
        with open(os.path.join(self.dir, "ajustes.json"), "w") as f:
            f.write("{roto")
        self.assertEqual(Ajustes(self.dir).idioma, "es")
        with open(os.path.join(self.dir, "ajustes.json"), "w") as f:
            json.dump({"idioma": "klingon", "activas": []}, f)
        a = Ajustes(self.dir)
        self.assertEqual(a.idioma, "es")
        self.assertTrue(a.activa("muro"))


class PruebaClase(Temporal):
    def escribir(self, datos):
        with open(os.path.join(self.dir, "mantitools_clase.json"), "w", encoding="utf-8") as f:
            f.write(datos if isinstance(datos, str) else json.dumps(datos))

    def test_sin_carpeta(self):
        c = Clase("")
        self.assertFalse(c.existe)
        self.assertEqual(c.desactivadas, [])
        self.assertFalse(c.bloqueada("muro", "abrir_con_escena"))

    def test_desactivar_y_fijar(self):
        self.escribir({"desactivar": ["radial", 3], "fijar": {"muro": {"abrir_con_escena": False}}})
        c = Clase(self.dir)
        self.assertEqual(c.desactivadas, ["radial"])
        self.assertEqual(c.fijadas("muro"), {"abrir_con_escena": False})
        self.assertTrue(c.bloqueada("muro", "abrir_con_escena"))
        self.assertEqual(c.fijadas("materials"), {})

    def test_json_roto_avisa(self):
        self.escribir("[1,")
        c = Clase(self.dir)
        self.assertTrue(c.error)
        self.assertEqual(c.datos, {})

    def test_subcarpetas(self):
        self.assertEqual(subcarpeta(self.dir, "radial"), os.path.join(self.dir, "radial"))
        self.assertEqual(subcarpeta(self.dir, "trepadora"), "")
        self.assertEqual(subcarpeta("", "radial"), "")


class PruebaInstalador(Temporal):
    def test_incluidas_en_orden(self):
        self.assertEqual([i for i, _ in instalar.incluidas(comun.RAIZ)],
                         ["trepadora", "arboles", "radial", "muro", "materials", "grasseditor", "simplesave"])

    def test_mod_con_un_bloque_por_herramienta(self):
        texto = instalar.contenido_mod(comun.RAIZ, self.dir)
        bloques = [b for b in texto.split("\n\n") if b.strip()]
        self.assertEqual(len(bloques), 8)
        self.assertTrue(bloques[0].startswith("+ MantiTools 1."))
        self.assertIn("+ MantiTools_materials ", texto)
        for b in bloques:
            self.assertIn("scripts: scripts", b)
        # Cada herramienta con carpeta de iconos (icons o iconos) la declara en su bloque.
        for ident, carpeta in instalar.incluidas(comun.RAIZ):
            bloque = [b for b in bloques if b.startswith("+ MantiTools_{} ".format(ident))][0]
            for nombre in ("icons", "iconos"):
                if os.path.isdir(os.path.join(carpeta, nombre)):
                    self.assertIn("icons: " + nombre, bloque)
                    break

    def test_ruta_con_tildes(self):
        modulos = os.path.join(self.dir, "maya", "modules")
        self.assertEqual(instalar.ruta_para_mod("/a/b", modulos), "/a/b")
        con_tilde = os.path.join(self.dir, "José", "mantitools")
        self.assertEqual(instalar.ruta_para_mod(con_tilde, os.path.join(self.dir, "José", "modules")),
                         "../mantitools")

    def test_apartar_y_devolver_sueltas(self):
        for nombre in ("radial.mod", "muestrario.mod", "otro.mod"):
            open(os.path.join(self.dir, nombre), "w").close()
        apartadas = instalar.apartar_sueltas(self.dir)
        self.assertEqual(sorted(i for i, _ in apartadas), ["materials", "radial"])
        self.assertTrue(os.path.isfile(os.path.join(self.dir, "otro.mod")))
        self.assertFalse(os.path.exists(os.path.join(self.dir, "radial.mod")))
        self.assertEqual(comprobar.sueltas_activas(self.dir), [])
        devueltas = instalar.devolver_sueltas([r for _, r in apartadas])
        self.assertEqual(len(devueltas), 2)
        self.assertTrue(os.path.isfile(os.path.join(self.dir, "muestrario.mod")))

    def test_devolver_no_pisa(self):
        ruta = os.path.join(self.dir, "radial.mod")
        open(ruta + ".mantitools", "w").close()
        open(ruta, "w").close()
        self.assertEqual(instalar.devolver_sueltas([ruta + ".mantitools"]), [])


class PruebaComprobar(Temporal):
    def test_sueltas_activas(self):
        open(os.path.join(self.dir, "pradera.mod"), "w").close()
        self.assertEqual([i for i, _ in comprobar.sueltas_activas(self.dir)], ["grasseditor"])


if __name__ == "__main__":
    unittest.main()
