"""Copia cada herramienta de su repositorio a ``incluidas/<id>`` y apunta qué versión lleva el pack.

El código de cada herramienta se arregla en su propio repositorio; este script trae
la versión elegida al pack. Uso::

    python herramientas/sincronizar.py                    # clona cada repositorio (rama de versiones.json)
    python herramientas/sincronizar.py --desde ~/clones   # usa clones que ya tienes (~/clones/radial…)
    python herramientas/sincronizar.py radial muro        # solo esas

Solo se copia lo que hace falta para usar la herramienta (``COPIAR``); las pruebas,
los documentos y los scripts de desarrollo se quedan en su repositorio. Al final
se escribe ``versiones.json`` con la versión y el commit de cada una.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSIONES = os.path.join(RAIZ, "versiones.json")
COPIAR = ("scripts", "plug-ins", "icons", "iconos", "texturas", "painter", "LICENSE", "README.md", "GUIA_ALUMNOS.md",
          "GUIA_DE_USO.md")
IGNORAR = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")


def leer_versiones():
    with open(VERSIONES, encoding="utf-8") as f:
        return json.load(f)


def escribir_versiones(datos):
    with open(VERSIONES, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        f.write("\n")


def version_de(carpeta, ident):
    ruta = os.path.join(carpeta, "scripts", ident, "__init__.py")
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            if linea.startswith("__version__"):
                return linea.split("=")[1].strip().strip("\"'")
    return "0.0.0"


def _git(*argumentos, carpeta=None):
    return subprocess.check_output(("git",) + argumentos, cwd=carpeta, text=True).strip()


def origen(ident, datos, desde, temporal):
    """Carpeta con el repositorio de ``ident`` en la rama pedida."""
    if desde:
        carpeta = os.path.join(os.path.expanduser(desde), ident)
        if not os.path.isdir(carpeta):
            raise SystemExit("No encuentro {}".format(carpeta))
        return carpeta
    carpeta = os.path.join(temporal, ident)
    url = "https://github.com/{}.git".format(datos["repositorio"])
    _git("clone", "--depth", "1", "--branch", datos.get("rama", "main"), url, carpeta)
    return carpeta


def copiar(ident, carpeta_origen):
    destino = os.path.join(RAIZ, "incluidas", ident)
    if os.path.isdir(destino):
        shutil.rmtree(destino)
    os.makedirs(destino)
    for nombre in COPIAR:
        ruta = os.path.join(carpeta_origen, nombre)
        if os.path.isdir(ruta):
            shutil.copytree(ruta, os.path.join(destino, nombre), ignore=IGNORAR)
        elif os.path.isfile(ruta):
            shutil.copy2(ruta, os.path.join(destino, nombre))
    return destino


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("herramientas", nargs="*", help="las que se sincronizan (todas si no se dice)")
    parser.add_argument("--desde", help="carpeta con un clon de cada repositorio, con el nombre del id")
    args = parser.parse_args(argv)
    versiones = leer_versiones()
    elegidas = args.herramientas or list(versiones)
    with tempfile.TemporaryDirectory() as temporal:
        for ident in elegidas:
            datos = versiones[ident]
            carpeta = origen(ident, datos, args.desde, temporal)
            copiar(ident, carpeta)
            datos["version"] = version_de(carpeta, ident)
            try:
                datos["commit"] = _git("rev-parse", "--short", "HEAD", carpeta=carpeta)
            except (subprocess.CalledProcessError, OSError):
                datos["commit"] = ""
            print("{:12} {:8} {}".format(ident, datos["version"], datos["commit"]))
    escribir_versiones(versiones)
    return 0


if __name__ == "__main__":
    sys.exit(main())
