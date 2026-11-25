# Materiales OpenPBR

Trepadora, Árboles y Materials crean sus materiales como **openPBRSurface**, el material de superficie estándar de Maya 2026 y 2027. Esta página explica qué es, qué cambia respecto a los materiales de antes y cómo convertir escenas viejas.

## Qué es OpenPBR

OpenPBR es un modelo de material abierto (de la Academy Software Foundation) que reúne lo mejor de Autodesk Standard Surface y de Adobe Standard Material. En Maya es el nodo **openPBRSurface**:

- lo renderiza **Arnold** sin cargar nada más,
- se ve en el **visor** de Maya (Viewport 2.0),
- y lo entienden también otros motores y programas, como Substance 3D Painter.

Por eso el pack lo usa en todas sus herramientas: un mismo tipo de material de principio a fin, desde la biblioteca de [Materials](materials.md) hasta la hiedra de [Trepadora](trepadora.md) o los árboles de [Árboles](arboles.md).

## Qué herramienta crea qué

| Herramienta | Materiales | Antes eran |
|---|---|---|
| [Trepadora](trepadora.md) | `trepadora_*_ai`: hojas, tallos y rabillos de cada planta, para el render. El visor sigue usando su lambert con colores de vértice. | aiStandardSurface |
| [Árboles](arboles.md) | `arboles_<especie>_corteza` y `arboles_<especie>_hoja`, y los de clay. | standardSurface |
| [Materials](materials.md) | Todos los de la biblioteca. | (ya era OpenPBR) |

> **Nota:** En un Maya sin OpenPBR (anterior a 2025.3) Trepadora y Árboles crean los materiales de antes. MantiTools es para Maya 2026 y 2027, así que lo normal es OpenPBR.

## Equivalencia de atributos

Si tocas los materiales a mano, estos son los nombres que cambian. Los demás (`baseColor`, `specularRoughness`, `subsurfaceColor`, `emissionColor`, `normalCamera`…) se llaman igual.

| Standard Surface | OpenPBR | Notas |
|---|---|---|
| `base` | `baseWeight` | |
| `metalness` | `baseMetalness` | |
| `diffuseRoughness` | `baseDiffuseRoughness` | |
| `specular` | `specularWeight` | |
| `thinWalled` | `geometryThinWalled` | Hojas: finas, la luz las atraviesa. |
| `subsurface` | `subsurfaceWeight` | La translucidez de las hojas. |
| `transmission` | `transmissionWeight` | |
| `coat` | `coatWeight` | |
| `sheen`, `sheenColor`, `sheenRoughness` | `fuzzWeight`, `fuzzColor`, `fuzzRoughness` | |
| `emission` | `emissionLuminance` | En **nits**: 1 de Standard Surface son 1000 nits. |

> **Consejo:** La emisión del estilo cartoon de Árboles pasa de `emission` 0,35 a `emissionLuminance` 350. El brillo que se ve en el render es el mismo.

## Convertir escenas viejas

Las escenas hechas con versiones anteriores de Trepadora o Árboles tienen los materiales de antes. Funcionan igual, pero para tenerlo todo en OpenPBR:

1. Abre la escena.
2. **MantiTools → Convertir materiales a OpenPBR** (también está en el clic derecho de Trepadora y de Árboles en el estante, y en sus submenús).
3. Un mensaje dice cuántos materiales se han convertido.

La conversión:

- crea un openPBRSurface por cada material viejo, con el **mismo nombre**,
- copia sus valores traduciendo los nombres (tabla de arriba) y la emisión a nits,
- conecta las **mismas texturas** (color, rugosidad, mapa de normales, translucidez),
- pasa sus salidas a los mismos grupos de sombreado (también la conexión `aiSurfaceShader` de Trepadora),
- y borra el material viejo.

No toca mallas, texturas, colores de vértice ni el material del visor. Se puede deshacer con **Ctrl+Z** de una vez. Si la escena ya estaba en OpenPBR, dice que no había nada que convertir.

## Qué cambia en el render

En las pruebas de comparación (Maya 2027, MtoA 5.6.2, misma escena y cámara) la diferencia media por píxel entre antes y después es pequeña:

| Escena | Diferencia media (0-255) | Tiempo de render |
|---|---|---|
| Trepadora, vista general | 2,96 | 97,5 s → 100,8 s |
| Trepadora, de cerca | 1,94 | 83,0 s → 83,7 s |
| Trepadora, a contraluz | 3,15 | 109,9 s → 116,7 s |
| Árboles, jardín realista | 1,28 | 22,5 s → 23,9 s |
| Árboles, jardín cartoon | 1,38 | 23,6 s → 24,1 s |

Lo que se nota a simple vista:

- **Hiedra menos brillante.** OpenPBR da reflejos algo más suaves en las hojas.
- **Contraluz más apagado.** Las hojas finas de Trepadora dejan pasar menos luz cuando el sol está detrás. Si quieres recuperar ese verde brillante, sube un poco `subsurfaceWeight` de `trepadora_hoja_*_ai`.
- Una escena convertida con la orden sale **idéntica** a una creada directamente en OpenPBR.

## Ver también

- [Materials](materials.md)
- [Trepadora](trepadora.md)
- [Árboles](arboles.md)
- [RenderDesk](renderdesk.md)
