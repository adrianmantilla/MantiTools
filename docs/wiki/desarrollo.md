# Para desarrollar

Esta página es para quien mantiene MantiTools o quiere añadirle una herramienta. Para usarlo no hace falta nada de esto.

## Cómo está organizado

El código de cada herramienta vive y se arregla **en su propio repositorio**. MantiTools trae una copia de cada una en `incluidas/<id>`, con la versión fijada en `versiones.json`, y añade lo común: el menú, el estante, la carga, la ventana central y los adaptadores de ajustes.

```text
mantitools/
├── instalar.py               ← se arrastra a Maya
├── plug-ins/mantitools_plugin.py
├── scripts/mantitools/       ← menú, estante, carga, ventana central, adaptadores de ajustes, wiki
├── icons/                    ← iconos del estante (generados)
├── incluidas/<id>/           ← copia de cada herramienta (no se edita aquí)
├── plantillas/pack.py        ← contrato que lleva cada herramienta
├── versiones.json            ← repositorio, rama, versión y commit de cada una
├── docs/wiki/                ← esta wiki: páginas .md, su HTML generado, imágenes y recursos
├── herramientas/             ← sincronizar, generar_iconos, generar_wiki, prueba_maya
└── tests/
```

### Módulos del paquete mantitools

| Módulo | Qué hace |
|---|---|
| `herramientas.py` | Las **fichas**: nombre, color, plugin, menú, órdenes y grupo del estante de cada herramienta. Todo lo demás se construye a partir de ellas. No depende de Maya. |
| `carga.py` | Carga las herramientas activas desde `incluidas/`, aplica el idioma y la carpeta de clase. |
| `menu.py` | El menú **MantiTools**: un submenú por herramienta (lo crea cada una con su `pack.py`) y las órdenes del pack. |
| `estante.py` | El estante, con sus grupos y separadores, y el clic derecho de cada icono. |
| `centro.py` | La ventana central (Herramientas, Ajustes, Ayuda). |
| `adaptadores.py` | Una **página de ajustes** por herramienta: qué controles tiene, cómo se leen y escriben en las preferencias de la herramienta, y lo que fija la carpeta de clase. |
| `clase.py` | Lee la carpeta de clase y su `mantitools_clase.json`. No depende de Maya. |
| `comprobar.py` | El informe de **Comprobar instalación**. |
| `acciones.py` | Ejecuta las órdenes de las fichas y la conversión a OpenPBR. |
| `iconos.py` | Los dibujos de los iconos (SVG de línea 24×24) y su estilo. |
| `estilo.py` | El kit de estilo común de las ventanas (botones, colores, tipografía). |
| `wiki.py` | Abre esta wiki en el navegador. |
| `painter.py` | Instala el complemento de Substance Painter de Materials. |

## Tareas habituales

| Tarea | Orden |
|---|---|
| Traer versiones nuevas de las herramientas | `python herramientas/sincronizar.py` (o `--desde ~/clones` con clones locales, o solo `radial muro`) |
| Regenerar los iconos del estante | `python herramientas/generar_iconos.py` (necesita PySide6) |
| Regenerar la wiki en HTML | `python herramientas/generar_wiki.py` |
| Pruebas sin Maya | `python -m unittest discover -s tests` (necesitan PySide6) |
| Prueba dentro de Maya | `mayapy herramientas/prueba_maya.py` |

Las pruebas sin Maya usan un Maya falso para comprobar el arranque, los submenús, el estante y cada ajuste contra el código real de cada herramienta. `prueba_maya.py` arranca Maya sin interfaz con una carpeta de preferencias temporal (no toca las tuyas); también se puede ejecutar desde el Script Editor con Maya abierto para revisar el menú, el estante y la ventana.

## Añadir una herramienta al pack

1. En el repositorio de la herramienta, copia `plantillas/pack.py` a `scripts/<id>/pack.py` y haz que su menú se cree con `pack.crear_menu()`: así va como submenú de MantiTools si el pack está cargado, o en la barra de Maya si no.
2. Copia `scripts/mantitools/estilo.py` a `scripts/<id>/estilo.py` si quieres el mismo aspecto.
3. En MantiTools, añade su entrada a `versiones.json` y ejecuta `herramientas/sincronizar.py <id>`.
4. Añade su **ficha** en `scripts/mantitools/herramientas.py` (nombre, color, plugin, menú, órdenes) y su sitio en `GRUPOS`.
5. Añade su dibujo en `iconos.py` y regenera los iconos.
6. Si tiene ajustes generales, escribe su página en `adaptadores.py`.
7. Añade los textos (`desc_<id>`, `accion_<id>_<orden>`…) en `scripts/mantitools/i18n/es.json` y `en.json`.
8. Escribe su página de la wiki en `docs/wiki/<id>.md` y regenera la wiki.
9. Pasa las pruebas.

> **Importante:** Las pruebas comprueban que las copias de `pack.py` y `estilo.py` de cada herramienta son idénticas a las del pack. Si cambias una, cámbiala en MantiTools y cópiala a todas.

## La wiki

Las páginas están en `docs/wiki/*.md`, en un Markdown sencillo que se lee bien también en GitHub. `herramientas/generar_wiki.py` las pasa a HTML con la misma plantilla: barra lateral con los iconos del pack, índice de la página, buscador, anterior/siguiente y visor de imágenes. El HTML se guarda en el repositorio para que funcione sin conexión y sin instalar nada; la orden **MantiTools → Documentación (wiki)** abre `docs/wiki/index.html`.

Lo que admite el Markdown de la wiki:

- títulos `#` (uno por página), `##`, `###`,
- párrafos con **negrita**, *cursiva*, `código` y enlaces (a otras páginas con `pagina.md` o `pagina.md#seccion`),
- imágenes en su propia línea, con un pie opcional en cursiva justo debajo,
- listas con viñetas o numeradas (un nivel de anidado), tablas y bloques de código,
- avisos: un párrafo que empieza por `> **Consejo:**`, `> **Importante:**` o `> **Nota:**`.

Las imágenes van en `docs/wiki/img/<id>/`. Después de cambiar un `.md`, regenera el HTML y súbelo con el mismo commit: la prueba `tests/test_wiki.py` avisa si el HTML se ha quedado viejo o si algún enlace o imagen no existe.

## Ver también

- [Instalación](instalacion.md)
- El README de cada herramienta, en su repositorio de GitHub.
