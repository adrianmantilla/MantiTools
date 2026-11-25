# Instalación

MantiTools se instala arrastrando un archivo al visor de Maya. No hace falta copiar carpetas a mano ni tocar `Maya.env`.

## Antes de empezar

- Maya **2026 o 2027**, en Windows o macOS.
- La carpeta de MantiTools descargada y **descomprimida** en un sitio fijo, por ejemplo `Documentos/maya/MantiTools`.

> **Importante:** No muevas ni renombres la carpeta después de instalar. Maya la busca siempre en el mismo sitio. Si tienes que moverla, vuelve a arrastrar `instalar.py` desde su sitio nuevo.

## Instalar paso a paso

1. Abre Maya.
2. Desde el explorador de archivos (Finder en Mac), **arrastra `instalar.py` hasta el visor** de Maya y suéltalo.
3. Si Maya pregunta por un plugin sin firmar («Untrusted Plugin Loading»), pulsa **Allow**. Más abajo se explica cómo evitar que vuelva a salir.
4. Aparecen el menú **MantiTools** en la barra de Maya, el estante **MantiTools** y la ventana central.
5. Si tenías herramientas instaladas por separado, un mensaje te dice cuáles se han apartado.

![El estante MantiTools después de instalar](img/mantitools/estante.png)

### Qué hace el instalador

| Paso | Detalle |
|---|---|
| Escribe `mantitools.mod` | En tu carpeta de módulos de Maya. Un solo archivo da a Maya MantiTools y las nueve herramientas de la carpeta `incluidas`. |
| Aparta las herramientas sueltas | Si había un `radial.mod`, `materials.mod`, `lightmanager.mod`… lo mueve a la carpeta `mantitools_apartadas`, junto a `modules`, y quita su carga automática. No borra nada. |
| Instala el complemento de Painter | Copia el complemento de Substance 3D Painter de Materials a su carpeta de complementos (se cambia en **Ajustes → Materials**). |
| Carga MantiTools | Carga el plugin, lo marca para que se cargue siempre al abrir Maya y crea el estante. |

> **Nota:** Los ajustes, bibliotecas, tableros y radiales de las herramientas que ya usabas se conservan: MantiTools usa las mismas preferencias que las versiones sueltas.

### Dónde está la carpeta de módulos

| Sistema | Carpeta |
|---|---|
| Windows | `Documentos\maya\modules` |
| macOS | `~/Library/Preferences/Autodesk/maya/modules` |

Después de instalar, en esa carpeta solo debería quedar `mantitools.mod`. Las herramientas sueltas apartadas están en `mantitools_apartadas`, al lado.

## El aviso de seguridad de Maya

Maya avisa cada vez que carga un plugin sin firmar fuera de una ruta de confianza. Para no verlo en cada arranque:

1. **Windows → Settings/Preferences → Preferences**.
2. Categoría **Security**.
3. Añade la carpeta `plug-ins` de MantiTools a las rutas de confianza (Trusted locations).
4. Guarda las preferencias.

> **Nota:** Mientras ese diálogo espera respuesta, Arnold todavía no ha cargado y Maya puede escribir «Warning: Arnold renderer not loaded». No es un error: Arnold carga en cuanto aceptas. Con la ruta de confianza añadida no vuelve a salir ninguno de los dos.

## Reinstalar, actualizar o desinstalar

Arrastra otra vez `instalar.py` al visor. Como MantiTools ya está instalado, Maya pregunta qué quieres hacer:

| Opción | Qué hace |
|---|---|
| **Reinstalar** | Vuelve a escribir el `.mod`, el estante y el complemento de Painter. Úsalo después de actualizar la carpeta o si algo se ha estropeado. |
| **Desinstalar** | Quita el `.mod`, el estante y el complemento de Painter, y **devuelve** las herramientas sueltas que se apartaron al instalar. |
| **Cancelar** | No cambia nada. |

### Actualizar a una versión nueva

1. Cierra Maya.
2. Sustituye la carpeta de MantiTools por la nueva (en el mismo sitio). Si la tienes clonada con Git, basta con `git pull`.
3. Abre Maya y arrastra `instalar.py` → **Reinstalar**.
4. Si el estante no cambia de orden o de iconos, usa **MantiTools → Recrear estante**.

## Comprobar que todo está bien

**MantiTools → Comprobar instalación** revisa cada herramienta y escribe un informe:

- si está cargada y desde dónde (del pack o de otra copia),
- su versión,
- si queda algún `.mod` suelto activo que pueda chocar con el pack,
- y la comprobación propia de las herramientas que la tienen (Árboles, Radial, GrassEditor).

Las líneas que empiezan por «!» son avisos. **Copiar informe** lo deja en el portapapeles para pegarlo en un correo. Más en [Problemas y preguntas](problemas.md).

## Ver también

- [Primeros pasos](primeros-pasos.md)
- [Problemas y preguntas](problemas.md)
- [Para el profesor](profesor.md): instalar en un aula con carpeta de clase.
