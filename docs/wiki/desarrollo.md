---
titulo: Para desarrollar
corto: Para desarrollar
resumen: Cómo está hecho el pack, cómo se añade una herramienta, cómo se regeneran los iconos, las capturas y esta wiki, y cómo se prueba.
---

## Cómo está hecho

Cada herramienta sigue siendo su propio plugin, con su repositorio. El pack trae una copia de cada una en
`incluidas/<id>`, con la versión elegida en `versiones.json`, y un plugin que las carga por ruta.

```
mantitools/
├── instalar.py               ← se arrastra a Maya
├── plug-ins/mantitools_plugin.py
├── scripts/mantitools/       ← menú, estante, carga, ventana central, ajustes, documentación
├── icons/                    ← iconos del estante (generados)
├── incluidas/<id>/           ← copia de cada herramienta (no se edita aquí)
├── plantillas/pack.py        ← contrato que lleva cada herramienta
├── versiones.json            ← repositorio, rama, versión y commit de cada una
├── docs/wiki/                ← esta wiki (.md fuente y .html generado)
├── docs/capturas/            ← capturas de la ventana central (generadas)
├── docs/medios/              ← imágenes y GIF de cada herramienta
├── herramientas/             ← sincronizar, generar iconos, capturas y wiki, prueba en Maya
└── tests/
```

El código de cada herramienta se arregla **en su propio repositorio**, y se trae con `sincronizar.py`.

## Fichas

`scripts/mantitools/herramientas.py` tiene una ficha por herramienta: nombre, color, plugin, cómo se crea su menú y
sus órdenes. El menú, el estante, las tarjetas, la comprobación y las tablas de esta wiki salen de las fichas.
`GRUPOS` define los grupos del estante.

## Añadir una herramienta

1. Su repositorio lleva `scripts/<id>/pack.py` (copia de `plantillas/pack.py`) y `scripts/<id>/estilo.py` (copia
   de `scripts/mantitools/estilo.py`). Las pruebas comprueban que las copias son idénticas.
2. En MantiTools: ficha en `herramientas.py`, página en `adaptadores.py`, trazo del icono en `iconos.py`, textos en
   `i18n/es.json` y `i18n/en.json`, y su entrada en `versiones.json`.
3. `python herramientas/sincronizar.py <id>` la copia en `incluidas/`.
4. Una página `docs/wiki/<id>.md` con `herramienta: <id>` en la cabecera.
5. Regenera iconos, capturas y wiki (abajo).

## Regenerar

| Qué | Orden | Necesita |
|---|---|---|
| Traer versiones nuevas | `python herramientas/sincronizar.py` (o `--desde ~/clones`, o solo `radial muro`) | git |
| Iconos del estante | `python herramientas/generar_iconos.py` | PySide6 |
| Capturas a doble resolución | `python herramientas/capturas_docs.py` | PySide6, Pillow |
| Esta wiki | `python herramientas/generar_wiki.py` | PySide6, pandoc |

## La wiki

Cada página es un `.md` en `docs/wiki/` con una cabecera:

```
---
titulo: Muro
corto: Muro                 ← nombre en la barra lateral
herramienta: muro           ← solo en las páginas de herramientas
resumen: Tablero de referencias…
---
```

- Se escribe en Markdown de GitHub, que GitHub ya enseña bien. Los avisos `> [!TIP]`, `> [!NOTE]`,
  `> [!IMPORTANT]` y `> [!WARNING]` salen como recuadros.
- Los bloques `<!-- auto:ordenes <id> -->`, `<!-- auto:ajustes <id> -->`, `<!-- auto:todas-ordenes -->` y
  `<!-- auto:herramientas -->` se rellenan desde el código al generar. No se editan a mano.
- `generar_wiki.py` escribe el `.html` de cada página (barra lateral, buscador, índice, anterior y siguiente), los
  iconos en `recursos/iconos/`, el esquema `recursos/flujo.svg` y el índice del buscador. Las páginas funcionan sin
  conexión y sin servidor.
- El orden de la barra lateral está en `navegacion()` del mismo script.
- `scripts/mantitools/documentacion.py` abre las páginas desde Maya.

## Pruebas

- **Sin Maya** (necesitan PySide6): `python -m unittest discover -s tests`. Usan un Maya falso para comprobar el
  arranque, los submenús, el estante, cada ajuste contra el código real de cada herramienta, y que la wiki no tiene
  enlaces ni imágenes rotos.
- **En Maya**: `mayapy herramientas/prueba_maya.py`, o desde el Script Editor con Maya abierto para revisar también
  el menú, el estante y la ventana.
