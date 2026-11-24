# Árboles

**Un editor de árboles para Autodesk Maya: los montas a mano, pieza a pieza, y los plantas en tu
escena.** Partes de una de las 19 especies de serie (o de un tronco vacío), cambias cada rama con
deslizadores que responden al momento, guardas el árbol en tu biblioteca y lo plantas con un clic
tantas veces como quieras. Las copias quedan ligadas al original: cambias el original y cambian todas.

No es un generador procedural: tú decides dónde va cada rama. Nació para un aula de 3D, pero lo
puede usar cualquiera que trabaje con Maya.

*[English summary below](#english).*

![Un jardín hecho con Árboles, renderizado con Arnold](docs/imagenes/hero.jpg)

## Qué hace

- **Editor en tiempo real**: tronco y ramas como tubos sobre curvas que puedes doblar a mano, con
  ramas añadidas con un clic, repartidas alrededor del tronco, copiadas de una a otra o guardadas
  como favoritas. Horquillas en Y, peso que dobla las ramas y una figura humana de referencia.
- **19 especies de partida**: roble, encina, alcornoque, haya, castaño, plátano de sombra, arce
  (también en otoño), chopo, abedul, sauce llorón, olivo, almendro en flor, pino piñonero, abeto,
  ciprés, palmera, árbol seco y arbusto, cada una con su frondosidad clara, normal o frondosa.
- **Follaje** de hojas anchas, lobuladas, palmeadas, finas, plumosas, flores, escamas o agujas.
- **Biblioteca** con miniaturas en tu carpeta, que puedes llevar a otro ordenador.
- **Jardín**: planta con clic sobre el suelo, con un giro al azar, en calidad baja, media o alta.
  Las copias son instancias de Maya ligadas al maestro; **Desligar** suelta una copia.
- **Contador de triángulos con semáforo**, pensado para jardines de hasta unos 50 árboles.
- **Texturas** de corteza y hoja para cada especie en 512, 1K, 2K y 4K, en tres estilos
  (realista, cartoon y estilizado), materiales *clay* para modelar y tus propios materiales.
- **Todo se deshace** con Ctrl+Z (Cmd+Z en Mac).

![Las 19 especies de serie](docs/imagenes/especies.jpg)

## Requisitos

| | |
| --- | --- |
| Maya | 2026 o 2027 |
| Sistema | Windows o macOS |
| Render | Arnold (MtoA) para el render final; en el visor se ve sin él |
| Dependencias | Ninguna: usa el Python que trae Maya |

Probado en Maya 2027 en macOS. Las pruebas automáticas (sin Maya) pasan en Windows, macOS y
Linux en cada cambio. Si encuentras algún problema en Windows o en Maya 2026,
[cuéntalo](https://github.com/adrianmantilla/arboles/issues).

## Instalar

1. Descarga este repositorio (botón **Code → Download ZIP** en GitHub) y descomprímelo en una
   carpeta que no vayas a mover, por ejemplo `Documentos/Plugins/Arboles`.
2. Abre Maya y **arrastra el archivo `instalar.py` hasta el visor**.
3. Si Maya avisa de un plug-in no confiable (*Untrusted Plugin Loading - Security Warning*),
   es el de Árboles: pulsa **Allow**.
4. Elige la carpeta de tu biblioteca. Por defecto, `Documentos/Arboles`.

Aparece el menú **Árboles** en la barra de Maya y se cargará solo cada vez que abras Maya.
Si algo falla, usa **Árboles › Comprobar instalación**.

**Actualizar:** sustituye la carpeta por la versión nueva y arrastra otra vez `instalar.py`.
Tu biblioteca está en otra carpeta y no se toca. Si mueves la carpeta del plugin, también hay
que volver a arrastrar `instalar.py`.

**Desinstalar:** borra el archivo `arboles.mod` de la carpeta `modules` de tus preferencias de
Maya (la ruta exacta se escribe en el Script Editor al instalar) y desactiva `arboles_plugin` en
el Plug-in Manager. Tu biblioteca no se borra.

## Primeros pasos

![El editor de árboles con el roble de serie en el visor de Maya](docs/imagenes/editor.png)

1. **Árboles › Editor de árboles…** En **Empezar desde** elige una especie y su frondosidad, y
   pulsa **Empezar**.
2. Haz clic en una rama (en la lista o en el visor) y mueve los deslizadores. Si dejas el ratón
   quieto sobre uno, sale qué hace con un dibujo. **Peso** dobla las ramas: con él se pasa de un
   roble a un sauce.
3. Ponle un nombre y pulsa **Guardar**.
4. **Árboles › Plantar desde la biblioteca…**, elige el árbol y pulsa **Plantar con clic**. Cada
   clic en el visor planta uno. **Esc** para terminar. (¿Biblioteca vacía? Pulsa **Ejemplos**.)
5. Para cambiar todas las copias: selecciona una, **Editar maestro**, cambia y guarda.

**Peso**, de 0 a 1, en el roble de serie: las ramas se doblan y el árbol cambia de carácter.

![El deslizador Peso dobla las ramas del roble en tiempo real](docs/imagenes/peso.gif)

**Plantar y editar el maestro**: cada clic planta una copia; al guardar el maestro con otro
material, cambian las ocho a la vez.

![Plantar con clic y actualizar todas las copias desde el maestro](docs/imagenes/jardin.gif)

La [guía rápida](GUIA_ALUMNOS.md) lo explica paso a paso, con todos los tipos de hoja, el
semáforo de triángulos, las texturas, los materiales propios y qué hacer si algo falla.

## Menú Árboles

| Opción | Qué hace |
| --- | --- |
| Editor de árboles... | Monta, edita y guarda árboles |
| Plantar desde la biblioteca... | Panel con miniaturas para plantar con un clic, Desligar, Editar maestro y Ejemplos |
| Herramientas rápidas | Árbol de ejemplo, generar versión ligera, cuadros en la corteza |
| Carpeta de la biblioteca... | Cambia dónde se guardan tus árboles |
| Resolución de texturas | 512 (aula), 1K (recomendada), 2K o 4K (render final); cambia también las texturas ya puestas en la escena |
| Estilo de texturas | Realista, Cartoon (colores planos) o Estilizado (pintado); cambia también los árboles de la escena |
| Crear materiales clay | Crea `arboles_clay_corteza` y `arboles_clay_hoja` (standardSurface, se ven en el visor y en Arnold) |
| Comprobar instalación | Versión de Maya, Arnold y carpeta de la biblioteca |

## Texturas y materiales

Cada especie trae su corteza (color, relieve y rugosidad, repetible) y su hoja (color, relieve,
rugosidad y trasluz). El desplegable **Material** del editor elige las de qué especie usa tu
árbol, o **Clay**, gris neutro para modelar. En el visor se ven con el modo texturizado
(tecla **6**). Con **Material propio…** puedes usar tus imágenes (la corteza debe ser repetible).

El menú **Estilo de texturas** cambia el aspecto de todos los árboles de la escena:

![Los mismos árboles en estilo realista, cartoon y estilizado](docs/imagenes/estilos.jpg)

Las texturas están en `texturas/<especie>/<resolución>/`; el formato está en
[texturas/LEEME.md](texturas/LEEME.md). Si no necesitas 4K, puedes borrar esas carpetas para
ahorrar espacio: se usa la resolución más cercana que haya.

## Si algo falla

- **Árboles › Comprobar instalación** dice la versión de Maya, si está Arnold y dónde está tu
  biblioteca.
- **No aparece el menú.** Vuelve a arrastrar `instalar.py` y, si sale el aviso de seguridad,
  pulsa **Allow**.
- **Los árboles se ven grises.** Pulsa **6** en el visor. Si siguen grises, mira su **Material**
  en el editor.
- **Las hojas se ven negras en el visor.** Activa **Lighting › Two Sided Lighting** en el visor.

Para cualquier otro problema, abre una [incidencia](https://github.com/adrianmantilla/arboles/issues)
con tu versión de Maya, tu sistema y lo que sale en el Script Editor.

## Idiomas

La interfaz está en español. Todos los textos están en `scripts/arboles/i18n/es.json`: para
traducirla, copia ese archivo como `en.json` (u otro código de idioma), traduce los valores sin
tocar las claves y define la variable de entorno `ARBOLES_IDIOMA=en` antes de abrir Maya. Lo que
falte por traducir sale en español.

## Para docentes

- `python3 herramientas/empaquetar.py` crea `dist/Arboles-<versión>.zip` para repartir (sin
  pruebas ni herramientas), con texturas a 512 y 1K (unos 40 MB). Con `--2k` incluye también
  las de 2K (unos 130 MB). GitHub Actions genera el ZIP ligero en cada cambio, en «Artifacts».
- [GUIA_ALUMNOS.md](GUIA_ALUMNOS.md) sirve como guía rápida para repartir.

## Desarrollo

- Pruebas sin Maya: `python3 -m unittest discover -s tests` (Windows, macOS y Linux).
- Prueba completa en Maya: `mayapy herramientas/prueba_maya.py`.
- Render de comprobación en Arnold: `mayapy herramientas/render_jardin.py <carpeta>`.
- `python3 herramientas/vista_previa.py` dibuja cada especie sin Maya (frente, 3/4 y planta)
  con su número de triángulos.
- `python3 herramientas/miniaturas_ayuda.py` rehace las miniaturas de la ayuda de los
  deslizadores (`iconos/ayuda/`).
- Texturas: las hojas, con `herramientas/texturas_hojas.py` (NumPy y Pillow); las cortezas, con
  `herramientas/texturas_corteza.py` (necesita Substance 3D Designer y Painter instalados); los
  estilos cartoon y estilizado salen de las realistas con `herramientas/texturas_estilos.py`.

### Estructura

```
instalar.py              arrastrar al visor para instalar
GUIA_ALUMNOS.md          guía rápida para alumnos
plug-ins/arboles_plugin.py  plugin de Maya (menú y comando de deshacer)
scripts/arboles/
  modulos.py, arbol.py   tronco y ramas: parámetros y geometría (sin Maya)
  follaje.py             grupos de hojas y dónde se cuelgan
  ejemplos.py            plantillas y frondosidad
  biblioteca.py          árboles guardados, miniaturas y ramas favoritas
  construir_maya.py      crea las mallas en Maya
  editor.py, editor_ui.py   editor en tiempo real
  plantar.py, plantar_ui.py jardín: maestros, copias ligadas y panel
  ajustes.py, materiales.py, interfaz_maya.py, i18n/
herramientas/            pruebas en Maya, capturas, renders y empaquetado
tests/                   pruebas sin Maya
```

## Licencia y créditos

Creado por Adrián Mantilla.

El código se publica con la [licencia MIT](LICENSE): puedes usarlo, modificarlo y
redistribuirlo, también en proyectos comerciales, siempre que conserves el aviso de copyright.
La licencia MIT no cubre las texturas de corteza (ver abajo).

**Texturas.** Las de las hojas se dibujan con un script propio (`herramientas/texturas_hojas.py`).
Las de corteza de las especies de serie, y sus versiones cartoon y estilizada, se generaron a
partir de materiales de muestra incluidos con Adobe Substance 3D Painter (*Wood Bark* y
*Stylized Wood Bark*), así que su uso puede estar sujeto a las condiciones de Adobe para esos
materiales. Si vas a redistribuirlas fuera de tu propio trabajo, revisa esas condiciones o
sustitúyelas por las tuyas (ver [texturas/LEEME.md](texturas/LEEME.md)).

Autodesk, Maya y Arnold son marcas de Autodesk, Inc.; Adobe y Substance son marcas de Adobe.
Árboles es un proyecto independiente, sin relación con esas empresas.

## English

**Árboles** ("trees") is a hand-built tree editor for Autodesk Maya 2026 and 2027, on Windows and
macOS. Start from one of 19 species, shape each branch with live sliders (or by dragging its
curve), save the tree to your library with a thumbnail, and plant it in your scene with a click.
Planted copies are Maya instances linked to the master: edit the master and every copy updates.
Bark and leaf textures for each species come in 512 to 4K and in realistic, cartoon and
stylized looks, ready for Arnold. It needs nothing beyond the Python that ships with Maya.

**Install:** download the repository (**Code → Download ZIP**), unzip it somewhere permanent and
drag `instalar.py` into the Maya viewport. If Maya shows *Untrusted Plugin Loading*, click
**Allow**, then choose a library folder. An **Árboles** menu appears.

**Language:** the interface is in Spanish only for now. It is ready to be translated: copy
`scripts/arboles/i18n/es.json` to `en.json`, translate the values and set the environment
variable `ARBOLES_IDIOMA=en` before starting Maya. Contributions are welcome.

Code under the [MIT license](LICENSE); the bark textures are derived from Adobe Substance sample
materials and are not covered by it (see *Licencia y créditos*).
