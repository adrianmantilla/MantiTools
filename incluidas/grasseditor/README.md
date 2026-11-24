# GrassEditor

**Hierba ligera para Autodesk Maya: pinta dónde crece, mezcla tipos de hierba y deja que el plugin
mantenga la escena rápida.** Eliges el suelo, la zona (pintando, con curvas o con reglas de pendiente
y altura) y la mezcla de tipos. GrassEditor reparte las matas como instancias, enseña en el visor solo
una parte y, al renderizar con Arnold, calcula únicamente la hierba que ve la cámara, con menos
detalle a lo lejos.

Nació para un aula de 3D, pero lo puede usar cualquiera que trabaje con Maya.

*[English summary below](#english).*

## Qué hace

- **Ocho tipos de hierba** con su altura real: césped de jardín, hierba silvestre, hierba seca,
  trébol, espigas, juncos, flores silvestres (margaritas y amapolas) y mata ornamental. Se mezclan
  por porcentajes dentro de una capa. Cada tipo se puede editar o guardar como tipo propio.
- **Matas generadas**, no modeladas: cada tipo da seis variantes y tres niveles de detalle (mata
  completa, simple y tarjeta de 6 triángulos). El color va en los vértices: no hacen falta texturas.
- **Capas**: cada una con su suelo (o sus caras), su mezcla, su densidad y su semilla.
- **Zonas**: todo el suelo, caras seleccionadas, **pincel** en el visor (poner, borrar, suavizar),
  **curvas** (parterres, huecos y caminos), **reglas** de pendiente y altura, y **apartar de
  objetos** con borde suave. Reconoce los árboles de [Árboles](https://github.com/adrianmantilla/arboles)
  (aclara la hierba bajo las copas) y las piedras de Cantera.
- **Rendimiento**:
  - visor ligero: un porcentaje de las matas, como cajas, tarjetas o matas;
  - recorte por cámara: Arnold no calcula la hierba fuera del encuadre;
  - detalle por distancia y aclarado a lo lejos;
  - hornear: congela el reparto para que no se recalcule al abrir la escena;
  - semáforo, cifras (matas, triángulos, memoria con y sin instancias) y **Analizar escena** con consejos.
- **Acabado**: material «Hierba simple» (con luz que atraviesa las briznas) o clay, instancias
  sueltas, unir en una malla, exportar los puntos a CSV/JSON para un motor de juego y las matas a FBX.
- **Escena de ejemplo**: un jardín con una loma, un camino y un parterre, en tres capas.
- **Todo se deshace** con Ctrl+Z (Cmd+Z en Mac); cada trazo del pincel es un paso.

## Requisitos

| | |
| --- | --- |
| Maya | 2026 o 2027 |
| Sistema | Windows o macOS |
| Render | Arnold (MtoA) para el material de render; en el visor se ve sin él |
| Dependencias | Ninguna: usa el Python que trae Maya |

Las pruebas automáticas (sin Maya) pasan en Windows, macOS y Linux en cada cambio. Si encuentras
algún problema, [cuéntalo](https://github.com/adrianmantilla/GrassEditor/issues).

## Instalar

1. Descarga este repositorio (**Code → Download ZIP**) y descomprímelo en una carpeta que no vayas
   a mover, por ejemplo `Documentos/Plugins/GrassEditor`.
2. Abre Maya y **arrastra el archivo `instalar.py` hasta el visor**.
3. Si Maya avisa de un plug-in no confiable (*Untrusted Plugin Loading*), es el de GrassEditor: pulsa **Allow**.

Aparece el menú **GrassEditor** en la barra de Maya y se cargará solo cada vez que abras Maya.
Si algo falla, usa **GrassEditor › Comprobar instalación**.

**Actualizar:** sustituye la carpeta por la versión nueva y arrastra otra vez `instalar.py`.
**Desinstalar:** borra el archivo `grasseditor.mod` de tu carpeta de módulos de Maya (la ruta sale en
el Script Editor al instalar).

## Empezar

1. Selecciona un suelo (una malla poligonal) o algunas de sus caras.
2. **GrassEditor › Hierba en la selección**. Sale hierba silvestre en todo el suelo.
3. **GrassEditor › Abrir GrassEditor…** para cambiar la zona, la mezcla y el rendimiento.

O prueba **GrassEditor › Escena de ejemplo** para ver una escena ya hecha.

## Tipos de hierba

| Tipo | Altura | Matas por m² | Triángulos por mata (completa / simple / tarjeta) | Para qué |
| --- | --- | --- | --- | --- |
| Césped de jardín | 6 – 10 cm | 100 | 98 / 21 / 6 | Jardines, parterres, campos de deporte |
| Hierba silvestre | 25 – 45 cm | 30 | 154 / 33 / 6 | Prados, lomas, cunetas |
| Hierba seca | 30 – 50 cm | 25 | 126 / 27 / 6 | Verano, secano, ruinas abandonadas |
| Trébol | 5 – 12 cm | 60 | 135 / 75 / 6 | Manchas dentro del césped, sombra |
| Espigas | 40 – 70 cm | 14 | 118 / 33 / 6 | Campos, bordes de camino |
| Juncos | 60 – 120 cm | 8 | 126 / 21 / 6 | Orillas, zonas húmedas |
| Flores silvestres | 20 – 40 cm | 6 | 79 / 22 / 6 | Margaritas y amapolas salpicadas |
| Mata ornamental | 20 – 30 cm | 4 | 280 / 60 / 6 | Jardines de diseño, borduras |

## Cómo ahorra

| Técnica | Qué hace | Dónde ayuda |
| --- | --- | --- |
| Instancias | Cada tipo guarda 6 variantes × 3 niveles; las matas son copias. | Memoria y render |
| Visor ligero | Solo un porcentaje de las matas (10 % por defecto), como tarjetas o cajas. | Visor |
| Recorte por cámara | Se descartan las matas fuera del encuadre de la cámara de render (con margen). | Render |
| Detalle por distancia | Mata completa cerca, simple a media distancia y tarjeta lejos. | Render |
| Aclarar a lo lejos | Quita matas lejanas y agranda las que quedan. | Render |
| Hornear | Guarda el reparto en la escena: no se recalcula al abrirla. | Abrir y animar |

La escena guarda la máscara pintada y la semilla, no las matas: un campo de cientos de miles de
matas ocupa unos pocos KB en el archivo de Maya (salvo que lo hornees).

**Visor y render.** Al lanzar un render, GrassEditor pone toda la hierba en calidad de render (lo hace
el MEL de antes del render, que se añade solo) y vuelve al visor ligero al acabar. El botón
**Vista de render** hace lo mismo a mano. En los renders por lotes (Render Sequence, mayapy) la
hierba sale siempre completa. La escena se puede renderizar en un ordenador sin GrassEditor: el MEL
comprueba antes que el comando existe (aunque, sin el plugin, no habrá hierba).

## Para quien quiera tocar el código

- `scripts/grasseditor/`: `tipos` (preajustes), `matas` (generador), `mascara`, `reparto`
  (candidatas, reglas), `camara` (recorte, niveles, visor), `estadisticas` y `capa` (motor con
  caché y horneado) son Python puro y se prueban sin Maya. `nodo` es el nodo `grassEditorCapa`,
  `escena` lo crea y lo conecta, `ventana` es la interfaz (PySide6/PySide2).
- Textos en `scripts/grasseditor/i18n/es.json`. Para traducir, copia el archivo con otro código de
  idioma (`en.json`) y define la variable de entorno `GRASSEDITOR_IDIOMA=en`.
- Pruebas sin Maya: `python -m unittest discover -s tests -v`.
- Pruebas en Maya: `mayapy herramientas/prueba_maya.py`; renders: `mayapy herramientas/render_grasseditor.py <carpeta>`.
- ZIP para alumnos: `python3 herramientas/empaquetar.py`.

## Licencia

MIT. Ver [LICENSE](LICENSE).

<a id="english"></a>
## English summary

**GrassEditor** is a grass editor for Autodesk Maya 2026 and 2027 (Windows and macOS),
built with performance in mind. You choose a ground mesh (or some of its faces), paint or define
where the grass grows (brush, closed and open curves, slope and height rules, keep-away objects) and
mix eight grass types (lawn, wild grass, dry grass, clover, spikes, rushes, wildflowers, ornamental
tufts). Clumps are generated, not modelled, with six variants and three levels of detail each, and
are scattered as instances through Maya's instancer. The viewport shows only a fraction of the
clumps; at render time (Arnold) only the grass the camera sees is computed, with distance-based
detail and thinning. A traffic light, scene statistics and an *Analyse scene* report help students
learn scene optimisation. Install by dragging `instalar.py` into the Maya viewport. The interface is
in Spanish and ready to translate (`scripts/grasseditor/i18n`). MIT licence.
