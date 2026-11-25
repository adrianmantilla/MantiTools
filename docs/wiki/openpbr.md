---
titulo: Materiales OpenPBR
corto: OpenPBR
resumen: Trepadora, Árboles y Materials crean el mismo tipo de material, openPBRSurface. Cómo convertir escenas hechas con versiones anteriores.
---

## Qué es OpenPBR

**OpenPBR** es un modelo de material abierto que Maya y Arnold traen como `openPBRSurface`. Sustituye a
`aiStandardSurface` y `standardSurface` con parámetros parecidos (color base, rugosidad, metal, transmisión,
subsuperficie, barniz, pelusa, emisión), y se entiende igual en otros programas.

En MantiTools:

| Herramienta | Material que crea |
|---|---|
| [Materials](materials.md) | `openPBRSurface` para todas sus recetas |
| [Trepadora](trepadora.md) | `openPBRSurface` para tallos y hojas, con color por hoja y luz a contraluz |
| [Árboles](arboles.md) | `openPBRSurface` para corteza y hojas de cada especie |

Así todos los objetos de la escena responden igual a la luz y se pueden retocar con Materials.

## Convertir escenas antiguas

Las escenas hechas con versiones anteriores de Trepadora y Árboles usan `aiStandardSurface`. Para pasarlas:

1. Abre la escena.
2. Menú **MantiTools › Convertir materiales a OpenPBR**.
3. Un aviso dice cuántos materiales se han convertido.

La conversión cambia solo los materiales de Trepadora y de Árboles: conserva texturas, colores y conexiones, y
el material nuevo se llama igual que el viejo. Se puede deshacer con <kbd>Ctrl</kbd>+<kbd>Z</kbd>. También está en
el submenú de cada herramienta y en el clic derecho de sus iconos.

Para convertir otros materiales (Standard Surface, aiStandardSurface o Lambert), usa la pestaña **Escena** de
[Materials](materials.md).

> [!NOTE]
> En pruebas con Arnold, los árboles convertidos se ven prácticamente iguales. En Trepadora, el brillo de las hojas
> a contraluz es algo más suave que con el material antiguo.

## Equivalencias

| aiStandardSurface | openPBRSurface |
|---|---|
| base | baseWeight |
| baseColor | baseColor |
| metalness | baseMetalness |
| specular | specularWeight |
| specularRoughness | specularRoughness |
| transmission | transmissionWeight |
| subsurface | subsurfaceWeight |
| coat | coatWeight |
| sheen | fuzzWeight |
| emission | emissionLuminance |
| thinWalled | geometryThinWalled |
