# Muro

Muro es un tablero de imágenes de referencia y notas dentro de Maya: un lienzo infinito, acoplable como cualquier panel, donde sueltas tus referencias, las ordenas, las anotas y las llevas al visor como planos de imagen a escala.

![Muro en Maya 2027: un tablero con referencias, marcos, notas y un marcador; desplazar, acercar, encuadrar y añadir una nota](img/muro/muro.gif)

*Un tablero con referencias, marcos, notas y un marcador: desplazar, acercar, encuadrar y añadir una nota.*

## En pocas palabras

- Reúne tus referencias en un **lienzo infinito** dentro de Maya: arrástralas desde el Finder, el Explorador o el navegador, pégalas o captura el visor.
- Ordénalas con **marcos**, **notas**, **listas de tareas**, **marcadores**, **flechas** y **lápiz**, y estúdialas en **gris**, **volteadas** o **recortadas**.
- Lleva una referencia al visor como **plano de imagen a escala real** en `front`, `side` o `top`, o toma colores con el **cuentagotas** y ponlos en el material seleccionado.
- Con el **modo fantasma**, el tablero se vuelve transparente encima del visor y puedes modelar calcando.
- El tablero se guarda **dentro del proyecto de Maya**, con copia de las imágenes: la entrega lleva sus referencias. Se exporta en `.zip` o como PNG.

## Dónde está

Con MantiTools instalado, Muro no tiene menú propio en la barra de Maya: va dentro del menú **MantiTools**.

### En el estante

En el estante **MantiTools**, Muro es el icono amarillo del primer grupo, el de «empezar»: es lo primero que abres cuando empiezas una escena y reúnes referencias.

- **Clic**: **Abrir el tablero**.
- **Clic derecho**: órdenes rápidas:
  - **Nuevo tablero**
  - **Importar tablero**
  - **Capturar visor**
  - **Fantasma**

### En el menú MantiTools

**MantiTools → Muro** tiene estas entradas:

| Entrada | Qué hace |
|---|---|
| **Abrir tablero** | Abre el panel de Muro con el tablero de la escena (o el último) |
| **Nuevo tablero…** | Pide un nombre y crea un tablero vacío en el proyecto |
| **Importar tablero (.zip)…** | Abre un tablero que te han pasado en `.zip` |
| **Capturar el visor al tablero** | Añade una captura de lo que ves en el visor |
| **Modo fantasma** | Pone las referencias encima del visor, transparentes |
| **Abrir el tablero de la escena al abrirla** | Casilla: al abrir una escena, se abre su tablero |
| **Atajos del tablero** | La tabla de atajos del tablero |
| **Muro 1.0.0** | La versión (no hace nada al pulsarlo) |

### Órdenes para tus atajos

En el Editor de atajos de Maya, categoría *Custom Scripts › Muro*, puedes asignar teclas a:

- `MuroAbrir`: mostrar u ocultar el tablero.
- `MuroFantasma`: entrar o salir del modo fantasma.
- `MuroCapturarVisor`: capturar el visor al tablero.
- `MuroNotaNueva`: nota nueva en el tablero.

### En la ventana central

**MantiTools → Ajustes… → Muro** tiene sus ajustes (abrir con la escena, opacidad del fantasma y valores del plano de referencia). Lo explicamos en [Ajustes](muro.md#ajustes).

## Primeros pasos

1. Define tu proyecto de Maya (**File → Set Project**). Muro guarda los tableros en `sourceimages/muro` del proyecto.
2. Haz clic en el icono de **Muro** del estante. La primera vez se crea un tablero llamado **referencias** y se abre en una ventana flotante.
3. Arrastra dos o tres imágenes desde tu carpeta o desde el navegador hasta el tablero. También puedes copiarlas y pulsar **Ctrl+V** (**⌘V** en Mac) con el ratón encima.
4. Mueve las imágenes arrastrándolas. La esquina blanca escala y el punto de arriba gira.
5. Selecciona varias y pulsa **Ctrl+G**: quedan dentro de un **marco**. Haz doble clic en su título y escribe, por ejemplo, «Silueta».
6. Pulsa **N** para crear una nota y escribe qué te gusta de esas referencias. Haz doble clic para editarla.
7. Pulsa **A** para verlo todo y **F** para encuadrar lo seleccionado.
8. Guarda la escena. Desde ahora, la escena recuerda su tablero y lo abre cuando la abres.
9. Acopla el panel donde quieras, como cualquier panel de Maya, o déjalo flotante en otro monitor.

## El tablero

El tablero es un panel de Maya llamado **Muro · «nombre del tablero»**. Se puede acoplar o dejar flotante. Cuando está vacío te recuerda lo básico: suelta imágenes, pégalas o usa los botones de arriba, y doble clic para escribir una nota.

### Moverte

| Qué | Cómo |
|---|---|
| Acercar y alejar | **Rueda** del ratón, o pellizcar en el trackpad |
| Desplazar | **Alt + botón central**, **Espacio + arrastrar**, o dos dedos en el trackpad |
| Acercar arrastrando | **Alt + botón derecho**, como en los visores de Maya |
| Encuadrar la selección | **F** |
| Encuadrar todo | **A** |
| Volver al 100 % | Clic en el porcentaje del zoom |

Abajo tienes los botones **−** y **+** para alejar y acercar, y el porcentaje del zoom.

### La barra de herramientas

Arriba hay una barra flotante con estos botones (pasa el ratón por encima para ver su nombre):

| Botón | Qué hace |
|---|---|
| **Abrir imágenes** | Elige imágenes de tu disco |
| **Nota (N)** | Nota nueva |
| **Lista de tareas (L)** | Lista de tareas nueva |
| **Marco (Ctrl+G)** | Agrupa la selección en un marco |
| **Capturar el visor de Maya** | Añade una captura del visor |
| **Flecha (W)** | Arrastra de un elemento a otro para unirlos |
| **Lápiz (P)** | Dibuja encima |
| **Recortar (C)** | Arrastra un rectángulo sobre la imagen |
| **Cuentagotas (I)** | Toma un color de una imagen |
| **Gris (G)** | Pasa la imagen a gris |
| **Voltear en horizontal (H)** | Espeja la imagen |
| **Encuadrar todo (A)** | Encuadra todo el tablero |
| **Modo fantasma** | Las referencias encima del visor |
| **Tablero** (☰) | Menú del tablero: nuevo, abrir, plantillas, exportar… |

## Traer imágenes

- **Arrastrar** desde el Finder, el Explorador o el navegador. Si sueltas una carpeta, entran todas las imágenes que tiene.
- **Pegar** con **Ctrl+V** (**⌘V**). Si lo que pegas es texto, se convierte en una nota.
- **Abrir imágenes** (botón de la barra o clic derecho en el fondo → **Abrir imagen**).
- **Capturar el visor**: el botón de la cámara, el clic derecho en el fondo → **Capturar visor**, o **MantiTools → Muro → Capturar el visor al tablero**. La captura se llama «captura del visor · hora».

Las imágenes **se copian dentro del proyecto**: aunque borres el original, el tablero las conserva. Las fotos enormes (más de 2048 píxeles de lado) se ven con una miniatura y el original solo se carga al acercarte, para que el tablero vaya fluido.

> **Nota:** si una imagen del navegador no se puede bajar, guárdala primero en tu ordenador y suéltala desde allí.

## Ordenar

- **Mover**: arrastra. Con las **flechas** del teclado se mueve de 1 en 1; con **Mayús**, de 10 en 10.
- **Escalar**: arrastra la esquina blanca.
- **Girar**: arrastra el punto de arriba. Con **Mayús**, de 15 en 15°.
- **Duplicar**: **Ctrl+D**.
- **Al frente** y **Al fondo**: en el clic derecho → **Más…**.
- **Alinear** (con varias seleccionadas): **A la izquierda**, **Arriba**, **Centrar en vertical** y **Centrar en horizontal**.
- **Ordenar en rejilla**: coloca la selección (o lo de un marco) en filas ordenadas.
- **Bloquear**: el elemento ya no se mueve sin querer. **Desbloquear** lo libera.
- **Borrar**: **Supr**.

### Marcos

Un **marco** agrupa referencias con un título. Al moverlo se mueve lo de dentro. Créalo con **Ctrl+G** sobre la selección. Desde su clic derecho puedes **Renombrar**, **Ordenar en rejilla**, **Encuadrar**, **Exportar PNG** solo ese marco y **Quitar marco** (deshace el grupo sin borrar lo de dentro).

> **Consejo:** usa un marco por tema (silueta, materiales, detalles, color). Luego exporta cada marco como PNG para la memoria del proyecto.

## Ver mejor

- **Gris (G)**: pasa la imagen a gris para estudiar los valores (luces y sombras) sin que el color te engañe.
- **Voltear (H)**: espeja la imagen. Con la imagen volteada se notan mucho más los fallos de proporción.
- **Recortar (C)**: arrastra un rectángulo sobre la imagen. No destruye nada: **Quitar recorte** la devuelve entera.
- **Opacidad** por imagen (clic derecho → **Más…** → **Opacidad**): 100 %, 75 %, 50 % o 25 %.

## Anotar

### Notas y listas de tareas

- **N**: nota nueva. **L**: lista de tareas nueva. **Doble clic** en el fondo también crea una nota.
- **Doble clic** en una nota para escribir. Puedes usar `**negrita**`, `*cursiva*` y listas.
- En una **lista de tareas**, un clic en una línea la tacha.
- **Tono**: cada nota puede tener uno de **cinco tonos** discretos. El clic derecho → **Tono** pasa al siguiente.
- **Lista o texto** convierte una nota en lista de tareas o al revés.

### Marcadores

Clic derecho en una imagen → **Marcador aquí**: pone un número sobre ese punto de la imagen, unido a su nota por una línea fina. Sirve para señalar detalles: «1: el remate de la columna», «2: el desgaste de la esquina».

### Flechas y lápiz

- **Flecha (W)**: arrastra desde un elemento hasta otro para unirlos. La flecha sigue a los elementos cuando los mueves.
- **Lápiz (P)**: dibuja con el botón izquierdo. Si empiezas el trazo encima de una imagen, el trazo se mueve con ella.
- **Color del lápiz y las flechas** (clic derecho → **Más…**): **Blanco**, **Rojo**, **Amarillo**, **Verde** o **Azul**.
- **Esc** deja la herramienta.

### Notas ligadas a objetos

Una nota puede ir **ligada a un objeto de la escena**:

1. Selecciona el objeto en Maya.
2. Clic derecho en la nota → **Ligar a la selección**.
3. Desde entonces, un clic en la cabecera de la nota (o **Ir al objeto**) selecciona el objeto en Maya, aunque lo hayas renombrado.

**Desligar del objeto** (en **Más…**) quita la relación.

> **Consejo:** liga a cada pieza del modelo la nota con sus correcciones pendientes. Al revisar, un clic te lleva a la pieza.

## El menú de clic derecho

El clic derecho abre un **menú de seis puntos**, el mismo de [Radial](radial.md), con acciones distintas según dónde hagas clic. El sexto punto, **Más…**, abre la lista completa.

| Dónde | Acciones del menú de puntos |
|---|---|
| **Fondo** | Pegar, Nota, Abrir imagen, Capturar visor, Encuadrar todo, Más… |
| **Imagen** | Gris, Voltear, Marcador aquí, Plano de imagen, Cuentagotas, Más… |
| **Nota** | Tono, Lista o texto, Ligar a la selección (o Ir al objeto), Duplicar, Borrar, Más… |
| **Marco** | Renombrar, Ordenar en rejilla, Encuadrar, Exportar PNG, Quitar marco, Más… |
| **Varios elementos** | Ordenar en rejilla, Enmarcar, Duplicar, Encuadrar, Borrar, Más… |
| **Flecha o trazo** | Tono, Al frente, Borrar, Más… |

En **Más…** encuentras además Recortar, Quitar recorte, Opacidad, **Copiar imagen**, **Abrir con otra aplicación**, Editar texto, Alinear, Enmarcar, Al frente, Al fondo, Bloquear, Exportar PNG, Lista de tareas, Marco, **Seleccionar todo**, el color del lápiz, **Deshacer** y **Rehacer**.

## Llevarlo a Maya

### Plano de imagen a escala

Clic derecho en una imagen → **Plano de imagen**. Se abre la ventana **Plano de imagen · «nombre de la imagen»**:

1. Pon el **punto A** arriba (la cabeza) y el **punto B** abajo (los pies), haciendo clic o arrastrándolos.
2. Escribe la **Altura real de A a B** y su unidad (**m**, **cm**, **mm**, **ft** o **in**). La ventana te dice cuánto medirá el plano.
3. Elige la **Cámara**: **front**, **side** o **top**.
4. Ajusta la **Opacidad** y marca **En gris** si quieres.
5. Deja marcada **En la capa «muro_referencias», bloqueada** para no seleccionarlo sin querer.
6. Pulsa **Crear**.

El plano aparece a escala real con los pies en el suelo. Es un plano libre colocado detrás de la escena mirando a esa cámara, así que también se ve en la perspectiva. Para ocultarlo, apaga la capa **muro_referencias**.

Muro recuerda la última altura y unidad que usaste (por defecto, **1.8 m**, la altura de una persona).

### Cuentagotas

1. Pulsa **I** (o el botón del cuentagotas) y haz clic en un color de una imagen.
2. Si tienes un objeto o un material seleccionado en Maya, su **color base** toma ese color. Funciona con Arnold, Standard Surface, OpenPBR, Lambert, Blinn y otros.
3. El color queda en la **tira de muestras** de abajo a la izquierda (las 12 últimas). Clic en una muestra la aplica al material seleccionado; clic derecho la quita.

Si la gestión de color de Maya está activa, el color se pone en espacio lineal, para que se vea igual que en la imagen.

> **Nota:** si el material tiene una textura conectada al color, Muro no lo cambia y te avisa.

### Modo fantasma

![Modo fantasma: el render de referencia, transparente sobre el visor de Maya](img/muro/fantasma.jpg)

*Modo fantasma: el render de referencia, transparente sobre el visor. Arriba a la izquierda, la pastilla con la opacidad y Ajustar.*

Con el botón del fantasma (o **MantiTools → Muro → Modo fantasma**, o el clic derecho del icono del estante → **Fantasma**), el tablero se vuelve **transparente encima del visor** y **deja pasar los clics a Maya**: puedes seguir modelando mientras calcas la referencia.

Aparece una pastilla pequeña con:

- **Salir del modo fantasma** (el fantasma).
- **opacidad**: un deslizador para ver más o menos la referencia.
- **Ajustar**: mientras está activo puedes mover y acercar las referencias con el ratón para colocarlas sobre tu modelo. Mientras tanto, los clics no llegan a Maya. Vuelve a pulsarlo para seguir modelando.

> **Consejo:** encuadra en el tablero solo la referencia que quieres calcar antes de entrar en el modo fantasma, y alinea la cámara de Maya con ella (por ejemplo, `front` para una vista frontal).

## Tableros, proyecto y escena

### Dónde se guarda

```text
mi_proyecto/
  scenes/robot_v03.ma          recuerda su tablero
  sourceimages/muro/
    robot.muro/
      tablero.json             posiciones, notas, marcos, flechas…
      imagenes/                copias de las referencias
      miniaturas/              versiones pequeñas de las imágenes grandes
      planos/                  imágenes usadas en planos de imagen
```

Muro guarda solo, **segundo y medio después de cada cambio**, al cambiar de tablero y al guardar la escena. No tienes que pulsar nada.

La escena recuerda su tablero en cuanto la guardas. Si **Abrir el tablero de la escena al abrirla** está activado, al abrir la escena se abre también su tablero.

### El menú del tablero

El botón **Tablero** (☰) de la barra tiene:

- **Nuevo tablero…**: pide un nombre y crea uno vacío.
- **Abrir**: la lista de tableros de este proyecto, y **Abrir otro tablero…** para elegir una carpeta `.muro` de otro sitio.
- **Renombrar…** el tablero.
- **Ligar a esta escena**: hace que la escena abierta recuerde este tablero.
- **Plantillas**: **Nuevo desde «…»** a partir de una plantilla, **Guardar como plantilla…** y **Abrir la carpeta de plantillas**.
- **Exportar imagen PNG…**: una imagen del tablero entero.
- **Exportar tablero (.zip)…** e **Importar tablero (.zip)…**.
- **Mostrar la carpeta del tablero**.
- **Borrar imágenes sin usar**: limpia de la carpeta las imágenes que ya no están en el tablero.
- **Atajos del tablero**.

### Deshacer

**Ctrl+Z** deshace y **Ctrl+Shift+Z** rehace, **solo dentro del tablero**: no tocan tu escena de Maya.

## Para clase

- **Entregar**: **Exportar tablero (.zip)…** crea un solo archivo con el tablero y sus imágenes. También vale entregar el proyecto entero: el tablero ya está dentro de `sourceimages/muro`.
- **Repartir referencias**: el profesor exporta un tablero en `.zip` y cada alumno lo abre con **Importar tablero (.zip)…** (en el menú del tablero, en **MantiTools → Muro** o en el clic derecho del icono del estante).
- **Plantillas**: el profesor puede preparar un tablero con marcos vacíos (Silueta, Materiales, Detalles…) y guardarlo como plantilla. Las plantillas están en la carpeta `muro/plantillas` de las preferencias de Maya.
- **Exportar PNG**: del tablero entero o de un marco (clic derecho en el marco → **Exportar PNG**), para memorias y presentaciones.

## Ajustes

En la ventana central, **MantiTools → Ajustes… → Muro** tiene dos secciones.

### Tablero

- **Abrir el tablero con la escena** (activado de serie): al abrir una escena, se abre el tablero que tenía. Es la misma casilla que **MantiTools → Muro → Abrir el tablero de la escena al abrirla**.
- **Opacidad del fantasma** (5–100 %, de serie 50 %): con qué opacidad empieza el modo fantasma. Cuando mueves el deslizador de la pastilla del fantasma, ese valor se guarda aquí.

### Plano de referencia

- **Unidad** (m, cm, mm, ft o in; de serie **m**) y **Altura por defecto** (de serie **1.8**): los valores con los que se abre la ventana **Plano de imagen**. Ponlos a la altura habitual de lo que modelas (1.8 m para personajes, por ejemplo) y te ahorrarás escribirla cada vez. Muro los actualiza con lo último que usas en esa ventana.

El profesor puede fijar estos ajustes para todo el grupo en `mantitools_clase.json`, con las claves `abrir_con_escena`, `opacidad_fantasma` (en %), `unidad_altura` y `altura_plano`. Lo fijado sale con candado. Más en [Carpeta de clase](profesor.md).

## Atajos

Funcionan solo con el ratón encima del tablero.

| Atajo | Qué hace |
|---|---|
| Rueda · **Alt** + botón central · **Espacio** + arrastrar | Acercar · desplazar · desplazar |
| **Alt** + botón derecho | Acercar arrastrando |
| **F** · **A** | Encuadrar la selección · encuadrar todo |
| **Ctrl/⌘ + V** · **Ctrl/⌘ + C** | Pegar imagen o texto · copiar la imagen seleccionada |
| **N** · **L** | Nota nueva · lista de tareas nueva |
| **Ctrl + D** · **Ctrl + G** | Duplicar · enmarcar la selección |
| **G** · **H** | Gris · voltear |
| **W** · **P** · **C** · **I** | Flecha · lápiz · recortar · cuentagotas (**Esc** para salir) |
| **Ctrl + Z** · **Ctrl + Shift + Z** | Deshacer · rehacer (solo dentro del tablero) |
| **Supr** · flechas | Borrar · mover (con **Mayús**, de 10 en 10) |
| Clic derecho | Menú de puntos |
| Doble clic | Escribir en una nota o un título; en el fondo, nota nueva |

## Consejos

- Abre Muro **antes de modelar**: reunir y ordenar referencias es la primera fase del trabajo, y por eso Muro es el primer icono del estante.
- Usa **Gris** y **Voltear** a menudo: son dos trucos clásicos de ilustración para ver la forma y los valores sin distracciones.
- Para modelar a escala, crea primero el **plano de imagen** con la altura real y modela encima. Así tu modelo tendrá el tamaño correcto desde el principio.
- Usa el **cuentagotas** para sacar la paleta de una referencia y aplicarla directamente a tus materiales de prueba.
- Liga notas a objetos para tus **listas de correcciones**: el profesor deja una nota por pieza y tú vas tachando.
- Si el tablero pesa mucho, usa **Borrar imágenes sin usar** de vez en cuando.

## Problemas frecuentes

**¿Dónde está mi tablero? No sale al abrir la escena.**
La escena recuerda su tablero solo después de **guardarla** con el tablero abierto (o con **Ligar a esta escena**). Comprueba también que **Abrir el tablero con la escena** está activado. Si no, ábrelo desde **Tablero (☰) → Abrir**.

**El tablero se ha guardado en otro proyecto.**
Muro guarda en `sourceimages/muro` del **proyecto activo**. Define el proyecto (**File → Set Project**) antes de crear el tablero. Puedes abrir un tablero de otro sitio con **Abrir otro tablero…**.

**Arrastro una imagen desde el navegador y no aparece.**
Algunas webs no dejan bajar la imagen. Guárdala primero en tu ordenador y suéltala desde allí, o cópiala y pega con Ctrl+V.

**En modo fantasma no puedo mover las referencias.**
Pulsa **Ajustar** en la pastilla. Mientras está activo, los clics van al tablero y no a Maya; vuelve a pulsarlo para seguir modelando.

**En modo fantasma no puedo hacer clic en Maya.**
Probablemente tienes **Ajustar** activado. Desactívalo, o sal del modo fantasma con el fantasma de la pastilla.

**El plano de imagen no aparece en la cámara que elegí.**
Si la escena no tiene esa cámara (`front`, `side` o `top`), Muro te avisa y no crea el plano. Si existe pero no lo ves, mira si la capa **muro_referencias** está visible.

**El cuentagotas no cambia el color del material.**
Selecciona antes un objeto o un material en Maya. Si el material tiene una textura conectada al color, Muro no lo cambia a propósito.

**Ctrl+Z no deshace lo que hice en el tablero (o deshace algo de la escena).**
El Ctrl+Z del tablero solo funciona con el ratón encima del tablero. Fuera de él, Ctrl+Z es el de Maya.

**No veo Muro en el estante ni en el menú MantiTools.**
Puede estar desactivado en **Ajustes → General → Herramientas activas** o por el profesor. Mira **MantiTools → Comprobar instalación**.

## Ver también

- [Primeros pasos](primeros-pasos.md)
- [Flujo de trabajo](flujo-de-trabajo.md): Muro es el primer paso de una escena
- [Ajustes](ajustes.md)
- [Carpeta de clase](profesor.md)
- [Radial](radial.md), el mismo menú de puntos, para las órdenes de Maya
- [Materials](materials.md), que también tiene un cuentagotas para materiales
- [Problemas](problemas.md)
