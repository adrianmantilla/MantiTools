---
titulo: Si algo no funciona
corto: Si algo no funciona
resumen: Cómo comprobar la instalación, los problemas más comunes y cómo pedir ayuda con un informe.
---

## Comprobar la instalación

1. Menú **MantiTools › Comprobar instalación**, o en la ventana central **Ayuda › Comprobar instalación**.
2. Las líneas con **✓** están bien; las que empiezan por **!** dicen qué falla y cómo arreglarlo.
3. **Copiar informe** lo deja en el portapapeles para pegarlo en un correo o en una incidencia.

La comprobación revisa, para cada herramienta:

- si está activa y cargada, y con qué versión;
- si viene del pack o de otra copia (por ejemplo, una instalación suelta que no se apartó);
- la comprobación propia de la herramienta, si la tiene;
- si queda algún `.mod` suelto activo en la carpeta de módulos;
- si la [carpeta compartida](carpeta-compartida.md) se ha leído bien.

## Problemas comunes

### Al abrir Maya sale «Untrusted Plugin Loading»

Maya avisa porque los plugins de MantiTools no están firmados. Pulsa **Allow**. Para que no vuelva a salir, añade la
carpeta `plug-ins` de MantiTools en **Preferences › Security** como ruta de confianza.

### Sale «Arnold renderer not loaded» al arrancar

Aparece detrás del aviso anterior: mientras Maya espera tu respuesta, Arnold aún no ha cargado. En cuanto pulsas
**Allow**, Arnold carga y el aviso no importa. Con la ruta de confianza desaparecen los dos.

### No aparece el estante, o le faltan iconos

Menú **MantiTools › Recrear estante**. El estante también se rehace solo al arrancar si no coincide con las
herramientas activas.

### No aparece el menú MantiTools

El plugin no se cargó. Abre **Windows › Settings/Preferences › Plug-in Manager**, busca `mantitools_plugin.py` y
marca **Loaded** y **Auto load**. Si no está en la lista, arrastra otra vez `instalar.py`.

### Moví la carpeta y ya no carga

Arrastra otra vez `instalar.py` desde la carpeta nueva y elige **Reinstalar**.

### Una herramienta no carga

Su tarjeta dice «No se pudo cargar». En la comprobación, su línea explica por qué. Lo más común:

- otra copia suelta de esa herramienta en la carpeta de módulos (la comprobación la señala): vuelve a instalar
  MantiTools para apartarla;
- la herramienta está desactivada en **Ajustes › General** o por la [carpeta compartida](carpeta-compartida.md).

### Los árboles o la hiedra se ven grises

Pulsa <kbd>6</kbd> en el visor (modo con texturas). En el render, comprueba que Arnold está cargado.

### Texturas rosas al abrir en otro ordenador

En [Materials](materials.md), **Texturas › Reparar rutas**. Las texturas de Trepadora y Árboles se recolocan solas
al abrir la escena.

### Escenas antiguas con materiales aiStandardSurface

**MantiTools › Convertir materiales a OpenPBR**. Ver [OpenPBR](openpbr.md).

### Maya va lento con mucha vegetación

- [GrassEditor](grasseditor.md): mira el semáforo y usa **Analizar rendimiento**.
- [Árboles](arboles.md): planta en calidad baja o media y mira el semáforo del editor.
- [Trepadora](trepadora.md): baja la densidad de hojas o usa resolución de texturas 512 o 1K.

### Perdí trabajo porque Maya se cerró

Abre Maya otra vez: [SimpleSave](simplesave.md) te ofrece recuperar el autoguardado. Si no lo ofrece, clic derecho
en su icono › **Recuperar autoguardado**.

## Quitar MantiTools

Arrastra `instalar.py` al visor y elige **Desinstalar**. Si tenías herramientas sueltas, vuelven como estaban. Tu
carpeta y tus ajustes no se borran.

## Pedir ayuda

Copia el informe de la comprobación y abre una incidencia en
[github.com/adrianmantilla/mantitools/issues](https://github.com/adrianmantilla/mantitools/issues), con la versión
de Maya, el sistema y qué estabas haciendo. Si el problema es de una herramienta concreta, su página de esta wiki
enlaza a su repositorio.
