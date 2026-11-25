"""Iconos de las herramientas: línea blanca (o del color pedido) sobre 24×24, como SVG.

Con ellos se dibujan las tarjetas de la ventana central y se generan los PNG del
estante (``herramientas/generar_iconos.py``).
"""

# Estilo de los iconos (25-nov-2026): dibujo de línea fina clara sobre el gris de los botones
# de Maya, con una marca pequeña del color de cada herramienta bajo el dibujo.
FONDO = "#5b5b5b"
TRAZO = "#ececec"
GROSOR_ESTANTE = 0.85
GROSOR_TARJETA = 1.0
FONDO_TARJETA = "#333333"


def tono_marca(color):
    """El color de la herramienta, apagado para que conviva con el gris de Maya."""
    import colorsys
    r, g, b = (int(color.lstrip("#")[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    h, _l, _s = colorsys.rgb_to_hls(r, g, b)
    r, g, b = colorsys.hls_to_rgb(h, 0.62, 0.45)
    return "#{:02x}{:02x}{:02x}".format(*(int(round(v * 255)) for v in (r, g, b)))


TRAZOS = {
    "trepadora": '<path d="M12 21c0-6 1-10 5-14"/><path d="M14 12c-3 0-5-1.5-5.5-4 2.6-.4 4.6.8 5.5 4z"/>'
                 '<path d="M15.5 8.5c2.4.2 4-.9 4.5-3-2.2-.4-3.9.6-4.5 3z"/>'
                 '<path d="M12.6 16.5c-2.6.4-4.6-.6-5.4-2.8 2.4-.5 4.4.5 5.4 2.8z"/>',
    "arboles": '<path d="M12 21v-7"/><path d="M12 14l-3-3"/><path d="M12 15l3.5-3"/><circle cx="12" cy="8" r="5"/>',
    "radial": '<circle cx="12" cy="12" r="2"/><circle cx="12" cy="4" r="1.3"/><circle cx="18.9" cy="8" r="1.3"/>'
              '<circle cx="18.9" cy="16" r="1.3"/><circle cx="12" cy="20" r="1.3"/><circle cx="5.1" cy="16" r="1.3"/>'
              '<circle cx="5.1" cy="8" r="1.3"/>',
    "muro": '<rect x="3.5" y="4.5" width="17" height="15" rx="2"/><rect x="6.5" y="7.5" width="5" height="4"/>'
            '<rect x="13" y="9" width="4.5" height="6"/><path d="M6.5 15h4.5"/>',
    "materials": '<circle cx="12" cy="12" r="8"/><path d="M7.5 9.5a5 5 0 0 1 4-3"/><path d="M4 13c3 2 13 2 16 0"/>',
    "lightmanager": '<path d="M5.2 6.4l5.6-2.2 2 5.2-5.6 2.2z"/>'
                    '<path d="M12.8 6.2l5.7-1.4M13.6 8.3l6 .6M13.1 10.6l4.8 2.6"/>'
                    '<path d="M8.9 11l1.1 3.2M10 14.2v6M10 14.2l-3.4 5.8M10 14.2l3.4 5.8"/>',
    "renderdesk": '<rect x="3.5" y="4.5" width="17" height="12" rx="1.5"/><path d="M10.5 8l4 2.5-4 2.5z"/>'
                  '<path d="M8 20h8M12 16.5V20"/>',
    "grasseditor": '<path d="M4 20h16"/><path d="M7 20c0-5-1-8-3-11"/><path d="M11 20c0-6 0-10 1.5-14"/>'
                   '<path d="M15 20c.3-5 1.5-8 4-10"/><path d="M18.5 20c0-2.5.5-4 1.5-5"/>',
    "simplesave": '<path d="M5 4h11l3 3v13H5z"/><path d="M8 4v5h7V4"/><circle cx="12" cy="15" r="3"/>'
                  '<path d="M12 13.5V15l1 .8"/>',
    "centro": '<rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/>'
              '<rect x="4" y="13" width="7" height="7" rx="1.5"/><path d="M16.5 13v7M13 16.5h7"/>',
    "wiki": '<path d="M12 6.8C9.8 5.2 7 4.7 3.8 5.1v13.2c3.2-.4 6 .1 8.2 1.7 2.2-1.6 5-2.1 8.2-1.7V5.1'
            'c-3.2-.4-6 .1-8.2 1.7z"/><path d="M12 6.8V20"/><path d="M6.5 9.2c1.2 0 2.4.3 3.3.8M6.5 12.2'
            'c1.2 0 2.4.3 3.3.8M14.2 10c.9-.5 2.1-.8 3.3-.8M14.2 13c.9-.5 2.1-.8 3.3-.8"/>',
}


def svg(ident, color=TRAZO, grosor=GROSOR_TARJETA, fondo=None, radio=5, marca=None):
    """El icono de ``ident`` como texto SVG. Con ``fondo``, sobre un cuadrado redondeado de ese color;
    con ``marca``, una raya corta de ese color al pie."""
    base = ""
    if fondo:
        base = '<rect x="0" y="0" width="24" height="24" rx="{}" fill="{}" stroke="none"/>'.format(radio, fondo)
        if marca:
            base += '<rect x="7" y="20.6" width="10" height="1.5" rx=".75" fill="{}" stroke="none"/>'.format(marca)
        # El dibujo, un poco más pequeño para que respire dentro del cuadrado.
        trazos = '<g transform="translate(3.6 {}) scale(0.7)">{}</g>'.format(2.8 if marca else 3.6, TRAZOS[ident])
        grosor = grosor / 0.7
    else:
        trazos = TRAZOS[ident]
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">{}'
            '<g fill="none" stroke="{}" stroke-width="{}" stroke-linecap="round" stroke-linejoin="round">{}</g>'
            '</svg>').format(base, color, grosor, trazos)


def pixmap(ident, lado, color=TRAZO, fondo=None, grosor=GROSOR_TARJETA, marca=None):
    """QPixmap del icono (necesita QtSvg). None si no se puede dibujar."""
    from mantitools.qt import QtCore, QtGui, QtSvg
    if QtSvg is None:
        return None
    render = QtSvg.QSvgRenderer(QtCore.QByteArray(svg(ident, color, grosor, fondo, marca=marca).encode("utf-8")))
    mapa = QtGui.QPixmap(lado, lado)
    mapa.fill(QtCore.Qt.transparent)
    pintor = QtGui.QPainter(mapa)
    pintor.setRenderHint(QtGui.QPainter.Antialiasing, True)
    render.render(pintor)
    pintor.end()
    return mapa
