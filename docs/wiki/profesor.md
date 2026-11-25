# Para el profesor

MantiTools está pensado para un aula: una sola **carpeta de clase**, compartida en red o en la nube, sirve para todo el grupo. Con ella puedes repartir materiales y botones de Radial, desactivar herramientas y fijar ajustes para que todos trabajen igual.

## Montar la carpeta de clase

1. Crea una carpeta compartida a la que todos los alumnos tengan acceso: una unidad de red del aula, OneDrive, Google Drive, Dropbox…
2. Dentro, crea las subcarpetas que vayas a usar (ninguna es obligatoria).
3. Si quieres fijar ajustes, añade un `mantitools_clase.json` (ver abajo).
4. Cada alumno elige esa carpeta en **Ajustes → General → Carpeta de clase**.

```text
Clase/
├── mantitools_clase.json   ← opcional: lo que fijas para todos
├── radial/                 ← botones y radiales compartidos de Radial
└── materials/              ← materiales compartidos de Materials
```

| Subcarpeta | Para qué |
|---|---|
| `radial/` | Radial la usa como su carpeta de clase: botones y radiales que ve todo el grupo. Ver [Radial](radial.md). |
| `materials/` | Materials la usa como biblioteca compartida: los materiales que guardes ahí aparecen a todos. Ver [Materials](materials.md). |

> **Consejo:** Cada vez que arranca Maya, MantiTools pasa a Radial y a Materials su subcarpeta. No hace falta configurarla dentro de cada herramienta: basta con la carpeta de clase de Ajustes → General.

## El archivo mantitools_clase.json

Es opcional. Tiene dos partes, las dos opcionales:

```json
{
  "desactivar": ["radial"],
  "fijar": {
    "muro": {"abrir_con_escena": false},
    "materials": {"destino": "juego", "motor_juego": "unity"},
    "simplesave": {"autoguardado": true, "minutos": 10}
  }
}
```

| Parte | Qué hace |
|---|---|
| `desactivar` | Lista de herramientas (por su `id`) que no se cargan en ningún equipo del grupo. |
| `fijar` | Por herramienta, ajustes con el valor que tú decides. Se aplican cada vez que arranca Maya y aparecen con candado en Ajustes: el alumno los ve pero no los puede cambiar. |

Los `id` de las herramientas son: `muro`, `arboles`, `trepadora`, `grasseditor`, `materials`, `lightmanager`, `renderdesk`, `simplesave` y `radial`.

> **Importante:** Si el JSON tiene un error (una coma de más, comillas que faltan), no se fija nada y **Comprobar instalación** lo avisa. Valídalo en cualquier validador de JSON antes de compartirlo.

### Ejemplos útiles

Autoguardado obligatorio cada 5 minutos y miniaturas en todas las versiones:

```json
{"fijar": {"simplesave": {"autoguardado": true, "minutos": 5, "miniaturas": true}}}
```

Aula de videojuegos con Unity, texturas ligeras para equipos modestos:

```json
{"fijar": {"materials": {"destino": "juego", "motor_juego": "unity"},
           "arboles": {"resolucion_texturas": "512"},
           "trepadora": {"resolucion": "512"}}}
```

Primer día: solo las herramientas de construir, sin Radial ni RenderDesk:

```json
{"desactivar": ["radial", "renderdesk"]}
```

## Ajustes que se pueden fijar

Estas son todas las claves de `fijar`, sacadas de la página de Ajustes de cada herramienta. El valor tiene que ser del tipo indicado: `true`/`false` sin comillas, números sin comillas y textos entre comillas.

| Herramienta (`id`) | Clave | Ajuste | Valores |
|---|---|---|---|
| Muro (`muro`) | `abrir_con_escena` | Abrir el tablero con la escena | `true` / `false` |
| Muro (`muro`) | `opacidad_fantasma` | Opacidad del fantasma | número 5 – 100 |
| Muro (`muro`) | `unidad_altura` | Unidad | `"m"`, `"cm"`, `"mm"`, `"ft"`, `"in"` |
| Muro (`muro`) | `altura_plano` | Altura por defecto | número 0.01 – 10000.0 |
| Árboles (`arboles`) | `carpeta_biblioteca` | Carpeta de la biblioteca | texto (ruta) |
| Árboles (`arboles`) | `resolucion_texturas` | Resolución de texturas | `"512"`, `"1k"`, `"2k"`, `"4k"` |
| Árboles (`arboles`) | `estilo_texturas` | Estilo de las texturas | `"realista"`, `"cartoon"`, `"estilizado"` |
| Trepadora (`trepadora`) | `resolucion` | Resolución de texturas | `"512"`, `"1k"`, `"2k"`, `"4k"` |
| GrassEditor (`grasseditor`) | `render_automatico` | Pasar la hierba a calidad de render al renderizar | `true` / `false` |
| GrassEditor (`grasseditor`) | `tipo_inicial` | Tipo de hierba | `"cesped"`, `"silvestre"`, `"seca"`, `"trebol"`, `"espigas"`, `"juncos"`, `"flores"`, `"ornamental"` |
| GrassEditor (`grasseditor`) | `densidad_inicial` | Densidad | número 10 – 300 |
| Materials (`materials`) | `destino` | Destino por defecto | `"render"`, `"juego"` |
| Materials (`materials`) | `motor_juego` | Motor de juego | `"unreal"`, `"unity"`, `"gltf"` |
| Materials (`materials`) | `resolucion` | Resolución en Painter | `512`, `1024`, `2048`, `4096` |
| Materials (`materials`) | `ruta_painter` | Programa de Painter | texto (ruta) |
| Materials (`materials`) | `sincronizar` | Recargar las texturas al exportar desde Painter | `true` / `false` |
| Materials (`materials`) | `abrir_painter` | Abrir Painter al enviar | `true` / `false` |
| Materials (`materials`) | `carpeta_complemento` | Carpeta de complementos | texto (ruta) |
| LightManager (`lightmanager`) | `modo` | Modo al abrir | `"auto"`, `"estudio"`, `"escena"` |
| LightManager (`lightmanager`) | `agrupar_estudio` | Agrupar en Estudio | `"papel"`, `"zona"`, `"tipo"`, `"grupo"` |
| LightManager (`lightmanager`) | `agrupar_escena` | Agrupar en Escena | `"papel"`, `"zona"`, `"tipo"`, `"grupo"` |
| LightManager (`lightmanager`) | `ver_arnold` | Ver los valores de Arnold en la ficha | `true` / `false` |
| LightManager (`lightmanager`) | `carpeta_hdri` | Carpeta de HDRI | texto (ruta) |
| LightManager (`lightmanager`) | `carpeta_esquemas` | Carpeta de Mis esquemas | texto (ruta) |
| LightManager (`lightmanager`) | `carpeta_ies` | Carpeta de perfiles IES | texto (ruta) |
| LightManager (`lightmanager`) | `ciudad` | Lugar del sol | `"madrid"`, `"barcelona"`, `"sevilla"`, `"valencia"`, `"bilbao"`, `"santiago"`, `"canarias"`, `"lisboa"`, `"londres"`, `"paris"`, `"roma"`, `"berlin"`, `"oslo"`, `"reikiavik"`, `"nueva_york"`, `"los_angeles"`, `"mexico"`, `"bogota"`, `"lima"`, `"buenos_aires"`, `"santiago_chile"`, `"el_cairo"`, `"dubai"`, `"tokio"`, `"sidney"` |
| LightManager (`lightmanager`) | `norte` | Norte de la escena | número -180 – 180 |
| LightManager (`lightmanager`) | `practicas_auto` | Encender las lámparas al anochecer | `true` / `false` |
| LightManager (`lightmanager`) | `repetir_cantidad` | Copias al repetir | número 1 – 50 |
| RenderDesk (`renderdesk`) | `nivel` | Nivel de la pestaña Calidad | `"sencillo"`, `"detalle"`, `"experto"` |
| RenderDesk (`renderdesk`) | `nucleos` | Núcleos del render en segundo plano | `"menos2"`, `"todos"`, `"mitad"` |
| SimpleSave (`simplesave`) | `autoguardado` | Autoguardado activado | `true` / `false` |
| SimpleSave (`simplesave`) | `minutos` | Cada | número 1 – 120 |
| SimpleSave (`simplesave`) | `copias` | Copias que guarda | número 1 – 50 |
| SimpleSave (`simplesave`) | `pausa_reproduccion` | No guardar mientras se reproduce o renderiza | `true` / `false` |
| SimpleSave (`simplesave`) | `plantilla` | Plantilla de nombre | texto |
| SimpleSave (`simplesave`) | `formato` | Formato | `"ma"`, `"mb"` |
| SimpleSave (`simplesave`) | `miniaturas` | Guardar miniatura con cada versión | `true` / `false` |
| SimpleSave (`simplesave`) | `copia_activada` | Copiar cada versión a otra carpeta | `true` / `false` |
| SimpleSave (`simplesave`) | `copia_carpeta` | Segunda carpeta | texto (ruta) |
| Radial (`radial`) | `forma` | Forma | `"radial"`, `"pill"`, `"pill_vertical"` |
| Radial (`radial`) | `automatico` | Radial automático | `true` / `false` |
| Radial (`radial`) | `buscador` | Buscador bajo el menú | `true` / `false` |
| Radial (`radial`) | `aprendizaje` | Modo aprendizaje | `true` / `false` |
| Radial (`radial`) | `ventana_ms` | Tiempo entre pulsaciones | número 150 – 400 |

## En el aula

- **Instalar en todos los equipos.** Deja la carpeta de MantiTools en el mismo sitio en todos los equipos (o en una unidad compartida de solo lectura) y que cada alumno arrastre `instalar.py` una vez. Ver [Instalación](instalacion.md).
- **El aviso de seguridad.** Añade la carpeta `plug-ins` de MantiTools a las rutas de confianza de Maya (Preferences → Security) para que no salga en cada arranque.
- **Cuando algo falla.** Pide al alumno **Ayuda → Comprobar instalación → Copiar informe** y que te lo pegue en un correo: dice qué herramientas cargan, de dónde y qué avisos hay.
- **Guías para alumnos.** En **Ayuda → Guías y versiones** cada herramienta tiene su guía corta para alumnos (**Abrir guía**) y su página en esta wiki (**Wiki**).

## Ver también

- [Ajustes](ajustes.md)
- [Problemas y preguntas](problemas.md)
