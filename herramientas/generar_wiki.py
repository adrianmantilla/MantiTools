"""Genera la wiki en HTML (``docs/wiki/*.html``) a partir de sus páginas en Markdown.

Uso (no necesita Maya ni nada instalado aparte de Python 3)::

    python herramientas/generar_wiki.py

Las páginas se escriben en ``docs/wiki/<pagina>.md`` con un Markdown sencillo
(títulos, párrafos, listas, tablas, código, imágenes, avisos «> **Consejo:**»),
que también se lee bien en GitHub. Este script las pasa a HTML con la misma
plantilla: barra lateral con los iconos del pack, índice de la página, buscador,
anterior/siguiente y visor de imágenes. El resultado funciona sin conexión: la
orden «MantiTools → Documentación (wiki)» abre ``docs/wiki/index.html``.

Escribe también los iconos de las herramientas en ``docs/wiki/img/iconos/``.
Hay que volver a ejecutarlo (y hacer commit del HTML) cada vez que cambia un ``.md``;
las pruebas avisan si el HTML se ha quedado viejo.
"""

import html
import json
import os
import re
import sys
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
WIKI = os.path.join(RAIZ, "docs", "wiki")

from mantitools import herramientas as hr  # noqa: E402  (no depende de Maya)
from mantitools import iconos  # noqa: E402

# Navegación: (sección, [(página, título, icono)]). El icono es el de una herramienta o uno de ICONOS_WIKI.
GRUPO_TITULOS = {"empezar": "Empezar", "construir": "Construir la escena", "look": "Materiales, luz y render",
                 "a_mano": "Siempre a mano"}


def navegacion():
    nav = [("Guía", [("index", "Inicio", "centro"),
                     ("instalacion", "Instalación", "descargar"),
                     ("primeros-pasos", "Primeros pasos", "brujula"),
                     ("ventana-central", "Ventana central", "ventana"),
                     ("ajustes", "Ajustes", "ajustes"),
                     ("flujo-de-trabajo", "Flujo de trabajo", "flujo")])]
    for grupo, ids in hr.GRUPOS:
        nav.append(("Herramientas · " + GRUPO_TITULOS.get(grupo, grupo),
                    [(i, hr.ficha(i).nombre, i) for i in ids]))
    nav.append(("Más", [("openpbr", "Materiales OpenPBR", "materials"),
                        ("profesor", "Para el profesor", "clase"),
                        ("problemas", "Problemas y preguntas", "ayuda"),
                        ("desarrollo", "Para desarrollar", "codigo")]))
    return nav


# Iconos propios de la wiki, en el mismo estilo de línea que los del pack (24×24).
ICONOS_WIKI = {
    "descargar": '<path d="M12 4v11"/><path d="M7.5 10.5L12 15l4.5-4.5"/><path d="M5 19h14"/>',
    "brujula": '<circle cx="12" cy="12" r="8"/><path d="M14.8 9.2l-1.6 4-4 1.6 1.6-4z"/>',
    "ventana": '<rect x="3.5" y="5" width="17" height="14" rx="2"/><path d="M3.5 9h17"/><path d="M6.5 7h.01M8.5 7h.01"/>',
    "ajustes": '<path d="M5 7h9M18 7h1M5 12h3M12 12h7M5 17h11M19 17h0"/><circle cx="16" cy="7" r="2"/>'
               '<circle cx="10" cy="12" r="2"/><circle cx="17.5" cy="17" r="1.5"/>',
    "flujo": '<circle cx="6" cy="6" r="2"/><circle cx="18" cy="12" r="2"/><circle cx="6" cy="18" r="2"/>'
             '<path d="M8 6h4a4 4 0 0 1 4 4M16 14a4 4 0 0 1-4 4H8"/>',
    "clase": '<path d="M3 9l9-4 9 4-9 4z"/><path d="M7 11v4c3 2 7 2 10 0v-4"/><path d="M21 9v5"/>',
    "ayuda": '<circle cx="12" cy="12" r="8"/><path d="M9.8 9.6a2.3 2.3 0 0 1 4.4.9c0 1.6-2.2 2-2.2 3.3"/>'
             '<path d="M12 16.8h.01"/>',
    "codigo": '<path d="M9 8l-4 4 4 4M15 8l4 4-4 4"/>',
    "buscar": '<circle cx="11" cy="11" r="6"/><path d="M15.5 15.5L20 20"/>',
}


def icono_svg(ident, lado=24, fondo=True, color=None):
    """SVG de un icono del pack o de la wiki; con ``fondo``, en el cuadrado gris del estante."""
    trazos = iconos.TRAZOS.get(ident) or ICONOS_WIKI[ident]
    marca = None
    try:
        marca = iconos.tono_marca(hr.ficha(ident).color)
    except KeyError:
        pass
    if fondo:
        base = '<rect width="24" height="24" rx="5" fill="{}"/>'.format(iconos.FONDO)
        if marca:
            base += '<rect x="7" y="20.6" width="10" height="1.5" rx=".75" fill="{}"/>'.format(marca)
        cuerpo = '<g transform="translate(3.6 {}) scale(0.7)">{}</g>'.format(2.8 if marca else 3.6, trazos)
        grosor = iconos.GROSOR_TARJETA / 0.7
        trazo = iconos.TRAZO
    else:
        base, cuerpo, grosor, trazo = "", trazos, 1.6, color or "currentColor"
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{l}" height="{l}" '
            'aria-hidden="true">{b}<g fill="none" stroke="{t}" stroke-width="{g:.3g}" stroke-linecap="round" '
            'stroke-linejoin="round">{c}</g></svg>').format(l=lado, b=base, t=trazo, g=grosor, c=cuerpo)


# --- Markdown -----------------------------------------------------------------------------

def ancla(texto):
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c)).lower()
    texto = re.sub(r"[`*_\[\]()]", "", texto)
    texto = re.sub(r"[^a-z0-9\s-]", "", texto)
    return re.sub(r"[\s]+", "-", texto.strip())


def _destino(url):
    if re.match(r"^[a-z]+:", url) or url.startswith("#"):
        return url
    ruta, _, frag = url.partition("#")
    if ruta.endswith(".md"):
        ruta = ruta[:-3] + ".html"
    return ruta + ("#" + frag if frag else "")


def en_linea(texto):
    """Formato dentro de un párrafo: código, imágenes, enlaces, negrita y cursiva."""
    codigos = []

    def guardar(m):
        codigos.append("<code>{}</code>".format(html.escape(m.group(1))))
        return "\x00{}\x00".format(len(codigos) - 1)
    t = re.sub(r"`([^`]+)`", guardar, texto)
    t = html.escape(t, quote=False)
    t = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)",
               lambda m: '<img src="{}" alt="{}" loading="lazy">'.format(m.group(2), html.escape(m.group(1))), t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
               lambda m: '<a href="{}"{}>{}</a>'.format(
                   _destino(m.group(2)),
                   ' target="_blank" rel="noopener"' if m.group(2).startswith("http") else "", m.group(1)), t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    return re.sub(r"\x00(\d+)\x00", lambda m: codigos[int(m.group(1))], t)


AVISOS = {"consejo": ("consejo", "Consejo"), "importante": ("importante", "Importante"), "nota": ("nota", "Nota"),
          "atención": ("importante", "Atención"), "atencion": ("importante", "Atención")}


def bloques(md):
    """Pasa el Markdown a HTML. Devuelve (html, título, [(nivel, texto, ancla)])."""
    lineas = md.replace("\r\n", "\n").split("\n")
    salida, titulos, titulo = [], [], None
    usadas = {}
    i = 0

    def es_inicio(linea):
        return (linea.startswith("#") or linea.startswith("```") or linea.startswith("> ")
                or re.match(r"^\s*([-*]|\d+\.)\s", linea) or linea.startswith("|")
                or linea.strip() == "---" or re.match(r"^!\[[^\]]*\]\([^)]+\)\s*$", linea.strip()))

    while i < len(lineas):
        linea = lineas[i]
        s = linea.strip()
        if not s:
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            nivel, texto = len(m.group(1)), m.group(2).strip()
            if nivel == 1 and titulo is None:
                titulo = texto
                i += 1
                continue
            a = ancla(texto)
            if a in usadas:
                usadas[a] += 1
                a = "{}-{}".format(a, usadas[a])
            else:
                usadas[a] = 0
            titulos.append((nivel, re.sub(r"[`*]", "", texto), a))
            salida.append('<h{n} id="{a}">{t}<a class="ancla" href="#{a}" aria-label="Enlace">#</a></h{n}>'
                          .format(n=nivel, a=a, t=en_linea(texto)))
            i += 1
            continue
        if s.startswith("```"):
            lengua = s[3:].strip()
            i += 1
            codigo = []
            while i < len(lineas) and not lineas[i].strip().startswith("```"):
                codigo.append(lineas[i])
                i += 1
            i += 1
            salida.append('<div class="codigo"><button class="copiar" type="button">Copiar</button>'
                          '<pre><code class="{}">{}</code></pre></div>'
                          .format(html.escape(lengua), html.escape("\n".join(codigo))))
            continue
        if s == "---":
            salida.append("<hr>")
            i += 1
            continue
        m = re.match(r"^!\[([^\]]*)\]\(([^)\s]+)\)\s*$", s)
        if m:
            alt, src = m.group(1), m.group(2)
            pie = ""
            j = i + 1
            while j < len(lineas) and not lineas[j].strip():
                j += 1
            if j < len(lineas):
                mp = re.match(r"^\*([^*].*[^*]|[^*])\*\s*$", lineas[j].strip())
                if mp:
                    pie = mp.group(1)
                    i = j
            salida.append('<figure><a class="zoom" href="{s}"><img src="{s}" alt="{a}" loading="lazy"></a>{p}</figure>'
                          .format(s=src, a=html.escape(alt),
                                  p="<figcaption>{}</figcaption>".format(en_linea(pie)) if pie else ""))
            i += 1
            continue
        if s.startswith(">"):
            cita = []
            while i < len(lineas) and lineas[i].strip().startswith(">"):
                cita.append(lineas[i].strip()[1:].strip())
                i += 1
            texto = " ".join(c for c in cita if c)
            m = re.match(r"^\*\*([^*:]+):\*\*\s*(.*)$", texto)
            clase, etiqueta = "nota", None
            if m and m.group(1).lower() in AVISOS:
                clase, etiqueta = AVISOS[m.group(1).lower()]
                texto = m.group(2)
            salida.append('<div class="aviso {c}">{e}<p>{t}</p></div>'.format(
                c=clase, e='<span class="aviso-titulo">{}</span>'.format(etiqueta) if etiqueta else "",
                t=en_linea(texto)))
            continue
        if s.startswith("|"):
            filas = []
            while i < len(lineas) and lineas[i].strip().startswith("|"):
                filas.append(lineas[i].strip())
                i += 1

            def celdas(f):
                return [c.strip() for c in f.strip("|").split("|")]
            cab = celdas(filas[0])
            cuerpo = [celdas(f) for f in filas[1:] if not re.match(r"^\|[\s:|-]+\|?$", f)]
            t = ['<div class="tabla"><table><thead><tr>']
            t += ["<th>{}</th>".format(en_linea(c)) for c in cab]
            t.append("</tr></thead><tbody>")
            for f in cuerpo:
                t.append("<tr>" + "".join("<td>{}</td>".format(en_linea(c)) for c in f) + "</tr>")
            t.append("</tbody></table></div>")
            salida.append("".join(t))
            continue
        if re.match(r"^\s*([-*]|\d+\.)\s", linea):
            salida.append(_lista(lineas, i))
            i = _fin_lista(lineas, i)
            continue
        parrafo = [s]
        i += 1
        while i < len(lineas) and lineas[i].strip() and not es_inicio(lineas[i]):
            parrafo.append(lineas[i].strip())
            i += 1
        salida.append("<p>{}</p>".format(en_linea(" ".join(parrafo))))
    return "\n".join(salida), titulo or "", titulos


def _fin_lista(lineas, i):
    while i < len(lineas):
        linea = lineas[i]
        if not linea.strip():
            j = i + 1
            while j < len(lineas) and not lineas[j].strip():
                j += 1
            if j < len(lineas) and (re.match(r"^\s*([-*]|\d+\.)\s", lineas[j]) or lineas[j].startswith("  ")):
                i = j
                continue
            return i
        if not (re.match(r"^\s*([-*]|\d+\.)\s", linea) or linea.startswith("  ")):
            return i
        i += 1
    return i


def _lista(lineas, inicio):
    """Lista (con un nivel de anidado por sangría) a HTML."""
    fin = _fin_lista(lineas, inicio)
    elementos = []  # (sangría, ordenada, texto)
    for linea in lineas[inicio:fin]:
        if not linea.strip():
            continue
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", linea)
        if m:
            elementos.append([len(m.group(1)), m.group(2)[-1] == ".", m.group(3)])
        elif elementos:
            elementos[-1][2] += " " + linea.strip()

    def construir(items, k):
        if not items:
            return "", k
        base = items[k][0]
        ordenada = items[k][1]
        partes = ["<ol>" if ordenada else "<ul>"]
        while k < len(items) and items[k][0] >= base:
            if items[k][0] > base:
                sub, k = construir(items, k)
                partes[-1] = partes[-1][:-5] + sub + "</li>"
                continue
            partes.append("<li>{}</li>".format(en_linea(items[k][2])))
            k += 1
        partes.append("</ol>" if ordenada else "</ul>")
        return "".join(partes), k

    resultado, k = "", 0
    while k < len(elementos):
        trozo, k = construir(elementos, k)
        resultado += trozo
    return resultado


# --- Plantilla ----------------------------------------------------------------------------

PLANTILLA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo}</title>
<link rel="icon" href="img/iconos/centro.svg">
<link rel="stylesheet" href="recursos/wiki.css">
</head>
<body>
<header class="barra">
  <button class="menu-movil" type="button" aria-label="Menú">☰</button>
  <a class="marca" href="index.html">{logo}<span>MantiTools <small>wiki</small></span></a>
  <div class="buscador">{lupa}<input id="buscar" type="search" placeholder="Buscar en la wiki…" autocomplete="off">
    <div id="resultados" hidden></div></div>
  <span class="version">v{version}</span>
</header>
<div class="cuerpo">
<nav class="lateral">{nav}</nav>
<main>
<article>
{cabecera}
{contenido}
<nav class="pasos">{anterior}{siguiente}</nav>
</article>
<footer>MantiTools {version} · Wiki generada desde <code>docs/wiki/{pagina}.md</code> · Licencia MIT</footer>
</main>
<aside class="indice">{indice}</aside>
</div>
<div id="visor" hidden><img alt=""></div>
<script src="recursos/indice.js"></script>
<script src="recursos/wiki.js"></script>
</body>
</html>
"""


def _version(ident):
    try:
        with open(os.path.join(RAIZ, "versiones.json"), encoding="utf-8") as f:
            return json.load(f).get(ident, {}).get("version", "")
    except (OSError, ValueError):
        return ""


def _descripcion(ident):
    with open(os.path.join(RAIZ, "scripts", "mantitools", "i18n", "es.json"), encoding="utf-8") as f:
        return json.load(f).get("desc_" + ident, "")


def cabecera_pagina(pagina, titulo):
    try:
        ficha = hr.ficha(pagina)
    except KeyError:
        return "<h1>{}</h1>".format(en_linea(titulo))
    grupo = GRUPO_TITULOS.get(hr.grupo(pagina) or "", "")
    return ('<div class="ficha" style="--marca:{marca}">{icono}<div><h1>{t}</h1><p class="desc">{d}</p>'
            '<p class="datos"><span>v{v}</span><span>Estante: {g}</span>'
            '<a href="https://github.com/{r}" target="_blank" rel="noopener">github.com/{r}</a></p></div></div>'
            ).format(marca=iconos.tono_marca(ficha.color), icono=icono_svg(pagina, 72), t=html.escape(titulo),
                     d=html.escape(_descripcion(pagina)), v=_version(pagina), g=grupo, r=ficha.repositorio)


def html_nav(nav, actual):
    partes = []
    for seccion, paginas in nav:
        partes.append('<div class="grupo"><h4>{}</h4>'.format(html.escape(seccion)))
        for pagina, titulo, icono in paginas:
            partes.append('<a href="{p}.html"{c}>{i}<span>{t}</span></a>'.format(
                p=pagina, c=' class="actual"' if pagina == actual else "",
                i=icono_svg(icono, 22, fondo=icono in iconos.TRAZOS),
                t=html.escape(titulo)))
        partes.append("</div>")
    return "".join(partes)


def html_indice(titulos):
    h2 = [(n, t, a) for n, t, a in titulos if n in (2, 3)]
    if len(h2) < 2:
        return ""
    return '<h4>En esta página</h4><ul>{}</ul>'.format("".join(
        '<li class="n{}"><a href="#{}">{}</a></li>'.format(n, a, html.escape(t)) for n, t, a in h2))


def texto_plano(contenido):
    t = re.sub(r"<[^>]+>", " ", contenido)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def construir():
    """Todo lo que se escribe, sin escribirlo: ({ruta relativa a docs/wiki: texto}, [páginas sin .md])."""
    nav = navegacion()
    orden = [p for _, paginas in nav for p, _, _ in paginas]
    archivos = {}
    for ident in list(iconos.TRAZOS) + list(ICONOS_WIKI):
        archivos["img/iconos/{}.svg".format(ident)] = icono_svg(ident, 96)
    titulos_nav = {p: t for _, paginas in nav for p, t, _ in paginas}
    indice_busqueda, faltan = [], []
    for n, pagina in enumerate(orden):
        ruta_md = os.path.join(WIKI, pagina + ".md")
        if not os.path.isfile(ruta_md):
            faltan.append(pagina)
            continue
        with open(ruta_md, encoding="utf-8") as f:
            contenido, titulo, titulos = bloques(f.read())
        titulo = titulo or titulos_nav[pagina]
        anterior = siguiente = ""
        if n > 0:
            p = orden[n - 1]
            anterior = '<a class="ant" href="{}.html"><small>Anterior</small>{}</a>'.format(p, titulos_nav[p])
        if n + 1 < len(orden):
            p = orden[n + 1]
            siguiente = '<a class="sig" href="{}.html"><small>Siguiente</small>{}</a>'.format(p, titulos_nav[p])
        archivos[pagina + ".html"] = PLANTILLA.format(
            titulo=html.escape(re.sub(r"[`*]", "", titulo) + ("" if pagina == "index" else " · Wiki de MantiTools")), logo=icono_svg("centro", 30),
            lupa=icono_svg("buscar", 18, fondo=False), version=_version_pack(), nav=html_nav(nav, pagina),
            cabecera=cabecera_pagina(pagina, titulo), contenido=contenido, anterior=anterior,
            siguiente=siguiente, indice=html_indice(titulos), pagina=pagina)
        indice_busqueda.append({"p": pagina, "t": titulos_nav[pagina],
                                "s": [[t, a] for nv, t, a in titulos if nv in (2, 3)],
                                "x": texto_plano(contenido)[:20000]})
    archivos["recursos/indice.js"] = ("window.WIKI_INDICE = " + json.dumps(indice_busqueda, ensure_ascii=False)
                                      + ";\n")
    return archivos, faltan


def generar():
    archivos, faltan = construir()
    for relativa, texto in archivos.items():
        destino = os.path.join(WIKI, *relativa.split("/"))
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
    return sorted(r[:-5] for r in archivos if r.endswith(".html")), faltan


def _version_pack():
    with open(os.path.join(RAIZ, "scripts", "mantitools", "__init__.py"), encoding="utf-8") as f:
        m = re.search(r'__version__\s*=\s*"([^"]+)"', f.read())
    return m.group(1) if m else ""


if __name__ == "__main__":
    hechas, sin_md = generar()
    print("Páginas: {} · en {}".format(len(hechas), WIKI))
    if sin_md:
        print("Sin .md todavía: " + ", ".join(sin_md))
