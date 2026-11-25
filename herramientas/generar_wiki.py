"""Genera la wiki de MantiTools (``docs/wiki/*.html``) a partir de sus ``.md``.

Uso (fuera de Maya; necesita ``pandoc`` y PySide6)::

    python herramientas/generar_wiki.py

Las páginas se escriben en Markdown (``docs/wiki/<página>.md``), que GitHub ya
enseña bien. Este script:

1. Rellena los bloques automáticos ``<!-- auto:... -->`` … ``<!-- /auto -->`` a
   partir del código (órdenes del estante, ajustes de cada herramienta, lista de
   herramientas), y vuelve a guardar el ``.md`` si han cambiado. Así la wiki no se
   queda atrás cuando cambia un ajuste.
2. Convierte cada página a HTML con la plantilla de la wiki: barra lateral,
   buscador, cabecera con el icono de la herramienta, índice de la página y
   enlaces a la anterior y la siguiente.
3. Escribe los iconos (``recursos/iconos``), el esquema del flujo de trabajo y el
   índice del buscador.

Las páginas HTML no necesitan conexión: MantiTools las abre en el navegador
desde el menú, el estante y la pestaña Ayuda.
"""

import html
import json
import os
import re
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIKI = os.path.join(RAIZ, "docs", "wiki")
RECURSOS = os.path.join(WIKI, "recursos")
REPO = "https://github.com/adrianmantilla/mantitools"

sys.path.insert(0, os.path.join(RAIZ, "tests"))
import comun  # noqa: E402  (rutas de las herramientas incluidas y QT offscreen)
import maya_falso  # noqa: E402

# Navegación: (título del grupo, [páginas]). Las herramientas van en el orden del estante.
GRUPOS_HERRAMIENTAS = {
    "empezar": "Empezar el proyecto",
    "construir": "Construir",
    "look": "Look y render",
    "a_mano": "Siempre a mano",
}


def navegacion():
    from mantitools import herramientas as hr
    nav = [("Empezar", ["index", "instalar", "primeros-pasos"]),
           ("La suite", ["interfaz", "flujo", "carpeta-compartida", "openpbr"])]
    for grupo, ids in hr.GRUPOS:
        nav.append((GRUPOS_HERRAMIENTAS[grupo], list(ids)))
    nav.append(("Referencia", ["atajos", "problemas", "desarrollo"]))
    return nav


# --- Markdown con cabecera ---------------------------------------------------------------------

def leer(pagina):
    with open(os.path.join(WIKI, pagina + ".md"), encoding="utf-8") as f:
        texto = f.read()
    datos = {}
    m = re.match(r"---\n(.*?)\n---\n", texto, re.S)
    if m:
        for linea in m.group(1).splitlines():
            clave, _, valor = linea.partition(":")
            datos[clave.strip()] = valor.strip()
        texto = texto[m.end():]
    return datos, texto


def cabecera_md(datos):
    return "---\n" + "".join("{}: {}\n".format(k, v) for k, v in datos.items()) + "---\n"


# --- Bloques automáticos -----------------------------------------------------------------------

def _celda(texto):
    return str(texto).replace("|", "\\|").replace("\n", " ")


def _valores(c):
    if c.tipo == "opciones":
        return ", ".join(texto for _v, texto in c.opciones)
    if c.tipo in ("entero", "decimal"):
        if c.minimo is None:
            return "Número"
        def num(v):
            return ("{:g}".format(v)).replace(".", ",")
        return "{} a {}{}".format(num(c.minimo), num(c.maximo), c.sufijo.rstrip() and " " + c.sufijo.strip())
    return {"casilla": "Sí / no", "carpeta": "Una carpeta", "archivo": "Un archivo", "texto": "Texto",
            "boton": "Botón"}.get(c.tipo, "")


def auto_ajustes(ident):
    from mantitools import adaptadores as ad
    partes = []
    for titulo, controles in ad.pagina(ident).secciones():
        filas = [c for c in controles if c.tipo != "info"]
        if not filas:
            continue
        partes.append("**{}**\n\n| Ajuste | Valores | Qué hace | Clave |\n|---|---|---|---|".format(titulo))
        for c in filas:
            clave = "" if c.tipo == "boton" else "`{}`".format(c.clave)
            partes[-1] += "\n| {} | {} | {} | {} |".format(_celda(c.texto), _celda(_valores(c)),
                                                          _celda(c.ayuda), clave)
    return "\n\n".join(partes) if partes else "_Esta herramienta no tiene ajustes en la ventana central._"


def auto_ordenes(ident):
    from mantitools import herramientas as hr
    from mantitools.i18n import t
    f = hr.ficha(ident)
    filas = ["| Cómo | Orden |", "|---|---|",
             "| **Clic** en el icono | {} |".format(t(f.texto(f.principal)))]
    for a in f.secundarias:
        filas.append("| Clic derecho | {} |".format(t(f.texto(a.clave))))
    return "\n".join(filas)


def auto_todas_ordenes():
    from mantitools import herramientas as hr
    from mantitools.i18n import t
    filas = ["| | Herramienta | Clic | Clic derecho |", "|---|---|---|---|"]
    for f in hr.FICHAS:
        filas.append("| ![](recursos/iconos/{id}.svg) | [{n}]({id}.md) | {p} | {s} |".format(
            id=f.id, n=f.nombre, p=t(f.texto(f.principal)),
            s=" · ".join(t(f.texto(a.clave)) for a in f.secundarias)))
    from mantitools import estante
    filas.append("| ![](recursos/iconos/centro.svg) | [MantiTools](interfaz.md) | Ventana central | {} |".format(
        " · ".join([t("menu_ajustes"), t("menu_ayuda"), t("menu_comprobar")])))
    filas.append("| ![](recursos/iconos/wiki.svg) | [Wiki](index.md) | Esta documentación | {} |".format(
        " · ".join(t(texto) for _p, texto in estante.PAGINAS_WIKI)))
    return "\n".join(filas)


def auto_herramientas():
    from mantitools import herramientas as hr
    filas = ["| | Herramienta | Grupo | Para qué sirve |", "|---|---|---|---|"]
    for f in hr.FICHAS:
        datos, _ = leer(f.id)
        filas.append("| ![](recursos/iconos/{id}.svg) | [**{n}**]({id}.md) | {g} | {r} |".format(
            id=f.id, n=f.nombre, g=GRUPOS_HERRAMIENTAS[hr.grupo(f.id)], r=datos.get("resumen", "")))
    return "\n".join(filas)


def html_herramientas():
    """En HTML, la lista de herramientas va en tarjetas, agrupadas como en el estante."""
    from mantitools import herramientas as hr
    partes = []
    for grupo, ids in hr.GRUPOS:
        tarjetas = []
        for ident in ids:
            f = hr.ficha(ident)
            datos, _ = leer(ident)
            tarjetas.append(
                '<a class="tarjeta" href="{id}.html" style="--marca:{m}">'
                '<img src="recursos/iconos/{id}.svg" alt=""><span><strong>{n}</strong>'
                '<small>{r}</small></span></a>'.format(id=ident, m=marca(ident), n=f.nombre,
                                                        r=html.escape(datos.get("resumen", ""))))
        partes.append('<div class="grupo-tarjetas"><h3>{}</h3><div class="tarjetas">{}</div></div>'.format(
            GRUPOS_HERRAMIENTAS[grupo], "".join(tarjetas)))
    return '<div class="herramientas">{}</div>'.format("".join(partes))


AUTOMATICOS = {
    "ajustes": (auto_ajustes, None),
    "ordenes": (auto_ordenes, None),
    "todas-ordenes": (auto_todas_ordenes, None),
    "herramientas": (auto_herramientas, html_herramientas),
}

PATRON_AUTO = re.compile(r"<!-- auto:([\w-]+)(?: ([\w-]+))? -->\n.*?<!-- /auto -->", re.S)


def rellenar(texto):
    """Devuelve (md con los bloques al día, {marca: html} para los que tienen versión HTML propia)."""
    ricos = {}

    def cambiar(m):
        nombre, arg = m.group(1), m.group(2)
        hacer_md, hacer_html = AUTOMATICOS[nombre]
        contenido = hacer_md(arg) if arg else hacer_md()
        bloque = "<!-- auto:{}{} -->\n{}\n<!-- /auto -->".format(nombre, " " + arg if arg else "", contenido)
        if hacer_html:
            ricos[bloque] = hacer_html(arg) if arg else hacer_html()
        return bloque

    return PATRON_AUTO.sub(cambiar, texto), ricos


# --- Iconos y esquema ---------------------------------------------------------------------------

def marca(ident):
    from mantitools import herramientas as hr, iconos
    return hr.ACENTO if ident in ("centro", "wiki") else iconos.tono_marca(hr.ficha(ident).color)


def escribir_iconos():
    from mantitools import herramientas as hr, iconos
    carpeta = os.path.join(RECURSOS, "iconos")
    os.makedirs(carpeta, exist_ok=True)
    for ident in list(hr.ORDEN) + ["centro", "wiki"]:
        with open(os.path.join(carpeta, ident + ".svg"), "w", encoding="utf-8") as f:
            f.write(iconos.svg(ident, fondo=iconos.FONDO, grosor=iconos.GROSOR_ESTANTE, marca=marca(ident)))
        with open(os.path.join(carpeta, ident + "_linea.svg"), "w", encoding="utf-8") as f:
            f.write(iconos.svg(ident, color=marca(ident), grosor=1.3))


def escribir_flujo():
    """El esquema del flujo de trabajo: los cuatro grupos del estante, de izquierda a derecha."""
    from mantitools import herramientas as hr, iconos
    lado, hueco, pad = 56, 14, 22
    columnas = []
    x = 20
    for grupo, ids in hr.GRUPOS:
        ancho = len(ids) * lado + (len(ids) - 1) * hueco + 2 * pad
        columnas.append((x, ancho, grupo, ids))
        x += ancho + 46
    total = x - 46 + 20
    alto = 196
    partes = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
              'font-family="-apple-system, Segoe UI, Helvetica, Arial, sans-serif">'.format(w=total, h=alto),
              '<rect width="{}" height="{}" rx="14" fill="#2b2b2b"/>'.format(total, alto)]
    for i, (x, ancho, grupo, ids) in enumerate(columnas):
        partes.append('<rect x="{}" y="22" width="{}" height="150" rx="12" fill="#333333" stroke="#444"/>'.format(x, ancho))
        partes.append('<text x="{}" y="48" fill="#8fc3e8" font-size="12" font-weight="700" letter-spacing="1" '
                      'text-anchor="middle">{}. {}</text>'.format(x + ancho / 2, i + 1,
                                                                    GRUPOS_HERRAMIENTAS[grupo].upper()))
        for j, ident in enumerate(ids):
            ix = x + pad + j * (lado + hueco)
            icono = iconos.svg(ident, fondo=iconos.FONDO, grosor=iconos.GROSOR_ESTANTE, marca=marca(ident))
            icono = icono.replace('width="24" height="24"', 'x="{}" y="66" width="{}" height="{}"'.format(ix, lado, lado), 1)
            partes.append(icono)
            partes.append('<text x="{}" y="146" fill="#dcdcdc" font-size="11" text-anchor="middle">{}</text>'.format(
                ix + lado / 2, hr.ficha(ident).nombre))
        if i < len(columnas) - 1:
            fx = x + ancho + 10
            partes.append('<path d="M{} 97h22m-7 -6l7 6-7 6" fill="none" stroke="#4a9bd1" stroke-width="2.2" '
                          'stroke-linecap="round" stroke-linejoin="round"/>'.format(fx + 2))
    partes.append("</svg>")
    with open(os.path.join(RECURSOS, "flujo.svg"), "w", encoding="utf-8") as f:
        f.write("".join(partes))


# --- HTML ---------------------------------------------------------------------------------------

AVISOS = {"NOTE": ("nota", "Nota"), "TIP": ("consejo", "Consejo"), "IMPORTANT": ("importante", "Importante"),
          "WARNING": ("cuidado", "Cuidado"), "CAUTION": ("cuidado", "Cuidado")}


def pandoc(texto):
    proceso = subprocess.run(["pandoc", "-f", "gfm", "-t", "html5", "--wrap=none"], input=texto.encode("utf-8"),
                             stdout=subprocess.PIPE, check=True)
    return proceso.stdout.decode("utf-8")


def pulir(cuerpo):
    # Enlaces entre páginas: .md -> .html
    cuerpo = re.sub(r'href="([\w-]+)\.md(#[^"]*)?"', lambda m: 'href="{}.html{}"'.format(m.group(1), m.group(2) or ""),
                    cuerpo)
    # Avisos de GitHub (> [!TIP]) -> recuadros
    def aviso(m):
        clase, titulo = AVISOS[m.group(1)]
        return '<div class="aviso {}"><p class="aviso-titulo">{}</p><p>{}</div>'.format(clase, titulo, m.group(2).strip())
    cuerpo = re.sub(r'<blockquote>\s*<p>\[!(\w+)\]\s*(.*?)</blockquote>', aviso, cuerpo, flags=re.S)
    # Imagen sola en un párrafo -> figura con pie (el texto alternativo)
    def figura(m):
        img = m.group(1)
        alt = re.search(r'alt="([^"]*)"', img)
        pie = alt.group(1) if alt else ""
        img = img.replace("<img ", '<img loading="lazy" ', 1)
        return '<figure>{}{}</figure>'.format(img, "<figcaption>{}</figcaption>".format(pie) if pie else "")
    cuerpo = re.sub(r'<p>(<img [^>]*>)</p>', figura, cuerpo)
    # Tablas con iconos pequeños
    cuerpo = cuerpo.replace('<img src="recursos/iconos/', '<img class="icono" src="recursos/iconos/')
    # Tablas anchas: que se puedan desplazar en pantallas estrechas
    cuerpo = cuerpo.replace("<table>", '<div class="tabla"><table>').replace("</table>", "</table></div>")
    return cuerpo


def indice_de(cuerpo):
    return re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', cuerpo)


def texto_plano(cuerpo):
    texto = re.sub(r"<[^>]+>", " ", cuerpo)
    return re.sub(r"\s+", " ", html.unescape(texto)).strip()


def titulo_de(pagina):
    datos, _ = leer(pagina)
    return datos.get("titulo", pagina)


def barra_lateral(actual, nav):
    partes = []
    for grupo, paginas in nav:
        enlaces = []
        for p in paginas:
            datos, _ = leer(p)
            icono = ""
            if datos.get("herramienta"):
                icono = '<img src="recursos/iconos/{}.svg" alt="">'.format(datos["herramienta"])
            enlaces.append('<li><a href="{p}.html"{c}>{i}{t}</a></li>'.format(
                p=p, c=' class="actual" aria-current="page"' if p == actual else "", i=icono,
                t=html.escape(datos.get("corto", datos.get("titulo", p)))))
        partes.append("<h4>{}</h4><ul>{}</ul>".format(grupo, "".join(enlaces)))
    return "".join(partes)


def cabecera(pagina, datos):
    from mantitools import herramientas as hr
    ident = datos.get("herramienta")
    if ident:
        f = hr.ficha(ident)
        grupo = GRUPOS_HERRAMIENTAS[hr.grupo(ident)]
        version = _version(ident)
        return ('<header class="portada-herramienta" style="--marca:{m}">'
                '<img class="icono-grande" src="recursos/iconos/{id}.svg" alt="">'
                '<div><p class="miga">{g}</p><h1>{n}</h1><p class="resumen">{r}</p>'
                '<p class="chips"><span>Estante: icono {n}</span><span>Menú MantiTools › {n}</span>'
                '<span>Versión {v}</span>'
                '<a href="https://github.com/{repo}">Código</a></p></div></header>').format(
                    m=marca(ident), id=ident, g=grupo, n=f.nombre, r=html.escape(datos.get("resumen", "")),
                    v=version, repo=f.repositorio)
    clase = "portada" if pagina == "index" else "titulo-pagina"
    return '<header class="{}"><h1>{}</h1>{}</header>'.format(
        clase, html.escape(datos.get("titulo", pagina)),
        '<p class="resumen">{}</p>'.format(html.escape(datos["resumen"])) if datos.get("resumen") else "")


def _version(ident):
    try:
        with open(os.path.join(RAIZ, "versiones.json"), encoding="utf-8") as f:
            return json.load(f)[ident].get("version", "")
    except Exception:
        return ""


PLANTILLA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo} · MantiTools</title>
<link rel="icon" href="recursos/iconos/centro.svg">
<link rel="stylesheet" href="recursos/estilo.css">
</head>
<body>
<a class="saltar" href="#contenido">Ir al contenido</a>
<button class="abrir-menu" aria-label="Menú" aria-expanded="false">☰</button>
<nav class="lateral" aria-label="Páginas de la wiki">
  <a class="marca" href="index.html"><img src="recursos/iconos/centro.svg" alt=""><span>MantiTools<small>Documentación · v{version}</small></span></a>
  <div class="buscar"><input type="search" id="buscar" placeholder="Buscar en la wiki…" autocomplete="off" aria-label="Buscar en la wiki"><ul id="resultados" hidden></ul></div>
  {lateral}
</nav>
<main id="contenido">
{cabecera}
<div class="cuerpo">
<article>
{cuerpo}
<footer class="pie">
  <div class="vecinas">{anterior}{siguiente}</div>
  <p>MantiTools {version} · Licencia MIT · <a href="{repo}">github.com/adrianmantilla/mantitools</a> · <a href="{repo}/blob/main/docs/wiki/{pagina}.md">Ver esta página en GitHub</a></p>
</footer>
</article>
{indice}
</div>
</main>
<script src="recursos/buscador.js"></script>
<script src="recursos/wiki.js"></script>
</body>
</html>
"""


def generar():
    maya_falso.instalar()
    from mantitools import carga
    carga.iniciar()
    import mantitools
    os.makedirs(RECURSOS, exist_ok=True)
    escribir_iconos()
    escribir_flujo()
    nav = navegacion()
    orden = [p for _g, paginas in nav for p in paginas]
    buscador = []
    escritas = []
    for i, pagina in enumerate(orden):
        datos, texto = leer(pagina)
        nuevo, ricos = rellenar(texto)
        if nuevo != texto:
            with open(os.path.join(WIKI, pagina + ".md"), "w", encoding="utf-8") as f:
                f.write(cabecera_md(datos) + nuevo)
        marcas_ricas = {}
        for n, (bloque, rico) in enumerate(ricos.items()):
            marca_txt = "MTAUTO{}FIN".format(n)
            nuevo = nuevo.replace(bloque, "\n\n" + marca_txt + "\n\n")
            marcas_ricas[marca_txt] = rico
        cuerpo = pulir(pandoc(nuevo))
        for marca_txt, rico in marcas_ricas.items():
            cuerpo = cuerpo.replace("<p>{}</p>".format(marca_txt), rico)
        apartados = indice_de(cuerpo)
        indice = ""
        if len(apartados) >= 2:
            indice = '<aside class="indice"><h4>En esta página</h4><ul>{}</ul></aside>'.format(
                "".join('<li><a href="#{}">{}</a></li>'.format(a, re.sub(r"<[^>]+>", "", t)) for a, t in apartados))
        anterior = siguiente = ""
        if i > 0:
            anterior = '<a class="anterior" href="{}.html"><small>Anterior</small>{}</a>'.format(
                orden[i - 1], html.escape(titulo_de(orden[i - 1])))
        if i < len(orden) - 1:
            siguiente = '<a class="siguiente" href="{}.html"><small>Siguiente</small>{}</a>'.format(
                orden[i + 1], html.escape(titulo_de(orden[i + 1])))
        pagina_html = PLANTILLA.format(
            titulo=html.escape(datos.get("titulo", pagina)), version=mantitools.__version__,
            lateral=barra_lateral(pagina, nav), cabecera=cabecera(pagina, datos), cuerpo=cuerpo,
            indice=indice, anterior=anterior, siguiente=siguiente, repo=REPO, pagina=pagina)
        with open(os.path.join(WIKI, pagina + ".html"), "w", encoding="utf-8") as f:
            f.write(pagina_html)
        escritas.append(pagina)
        buscador.append({"p": pagina, "t": datos.get("titulo", pagina),
                         "h": [[a, re.sub(r"<[^>]+>", "", t)] for a, t in apartados],
                         "x": texto_plano(cuerpo)[:6000]})
    with open(os.path.join(RECURSOS, "buscador.js"), "w", encoding="utf-8") as f:
        f.write("window.WIKI_PAGINAS = " + json.dumps(buscador, ensure_ascii=False) + ";\n")
    return escritas


if __name__ == "__main__":
    for p in generar():
        print("docs/wiki/{}.html".format(p))
