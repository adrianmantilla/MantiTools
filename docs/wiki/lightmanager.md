# LightManager

LightManager es un panel acoplable para gestionar todas las luces de Arnold de tu escena: las ves agrupadas, las enciendes, las pones en solo y las ajustas en **pasos** y **Kelvin**, que son las unidades con las que se piensa la luz en fotografía.

![Panel de LightManager en modo Estudio: órbita con tres luces, lista agrupada por papel y ficha de la luz clave](img/lightmanager/panel.png)

*El panel en modo Estudio después de aplicar el esquema «Tres puntos»: arriba la órbita, debajo la lista de luces y la ficha de la clave.*

## En pocas palabras

- Ajusta la potencia de cada luz en **pasos** (un paso más es el doble de luz) y su color en **Kelvin**, con atajos como vela, tungsteno o flash.
- Ilumina un objeto en segundos con **esquemas de estudio** (tres puntos, producto, Rembrandt, contraluz…) que se adaptan al tamaño del objeto y a la posición de la cámara.
- Ilumina **interiores y exteriores** por zonas (salón, cocina…), con portales en las ventanas, bombillas dentro de las lámparas y un **sol físico** colocado por lugar, fecha y hora.
- Guarda **escenarios** (fotos del estado de las luces) y compáralos manteniendo pulsado un botón.
- Antes de renderizar, la pestaña **Comprobar** te avisa de errores típicos (solo olvidado, render negro, sombras negras…) y casi todos se arreglan con un clic.

## Dónde está

LightManager forma parte del grupo de herramientas de look y render de MantiTools, junto a [Materials](materials.md) y [RenderDesk](renderdesk.md).

- **Estante MantiTools**: el icono naranja **LightManager**. Un clic abre o muestra el **Panel de luces**.
- **Clic derecho en el icono**: órdenes rápidas sin abrir el panel:
  - **Tres puntos en lo seleccionado**
  - **Comprobar la iluminación**
  - **Quitar todos los solos**
- **Menú MantiTools → LightManager**:
  - **Panel de luces**
  - **Tres puntos en lo seleccionado**
  - **Comprobar la iluminación**
  - **Quitar todos los solos**
  - **Guía de uso** (abre la guía de la herramienta)
  - **LightManager** con el número de versión (solo informativo)
- **Ajustes**: en la [ventana central](ventana-central.md) de MantiTools, **Ajustes → LightManager** (ver [Ajustes](#ajustes) más abajo).
- **Atajos**: en el **Hotkey Editor** de Maya, categoría *Custom Scripts › LightManager*, tienes cinco órdenes a las que puedes poner tecla: abrir o cerrar el panel, poner tres puntos en lo seleccionado, comprobar la iluminación, quitar todos los solos y apuntar la luz seleccionada con un clic.

> **Nota:** LightManager necesita Arnold (MtoA) cargado. Todo lo que hace se deshace con un solo `Ctrl+Z` por acción.

## Primeros pasos

Vamos a iluminar un objeto con un esquema de estudio y a afinar la luz principal.

1. Selecciona el objeto que quieres iluminar (por ejemplo, una taza o una escultura).
2. Haz clic en el icono **LightManager** del estante. Se abre el panel.
3. Arriba, comprueba que está marcado el modo **Estudio**.
4. Ve a la pestaña **Esquemas**, elige la familia **Estudio** en el desplegable y pulsa **Aplicar** en **Tres puntos**. Aparecen tres luces (clave, relleno y contra) mirando al objeto desde el lado de la cámara de render.
5. Abre el render interactivo en [RenderDesk](renderdesk.md) (botón **▶ Probar**) para ver la luz real de Arnold.
6. En la pestaña **Luces**, elige **Clave** en la lista. Debajo aparece su ficha.
7. Pulsa **2×** para doblar su luz o **½×** para dejarla en la mitad. Mira cómo cambia el render.
8. En **Color**, despliega la flecha **▾** y elige **Tungsteno · 3200 K** para una luz cálida de bombilla.
9. En la órbita de arriba, arrastra el punto de la clave para girarla alrededor del objeto. Con la rueda del ratón encima de la órbita la subes o la bajas.
10. Para colocar un brillo exacto, con la clave elegida pulsa **Reflejo** (en **Apuntar en el visor**) y haz clic en el visor de Maya donde quieres el brillo. Pulsa `Esc` para terminar.
11. Antes del render final, abre la pestaña **Comprobar** y arregla lo que salga en rojo.

## Conceptos: pasos y Kelvin

LightManager no te enseña los números de Arnold tal cual, sino dos unidades más intuitivas. Los valores reales siguen ahí: si quieres verlos, aparecen en la última línea de la ficha.

### Pasos de exposición (stops)

En fotografía, un **paso** (en inglés *stop*) es doblar o dividir a la mitad la cantidad de luz. El ojo no percibe la luz de forma lineal: pasar de 1 a 2 se nota tanto como pasar de 100 a 200. Por eso es más cómodo pensar en pasos.

Arnold calcula la potencia de una luz como `intensity × 2^exposure`. LightManager lo junta en un solo número, la **Potencia** en pasos:

```text
pasos = log2(intensity) + exposure
```

Al cambiar los pasos, LightManager respeta la `intensity` que ya tenga la luz y solo toca la `exposure`. Así una luz que hiciste a mano no cambia de aspecto por abrirla en el panel.

| Pasos | Cuánta luz (respecto a 0 pasos) | Qué significa |
|---|---|---|
| −1 | ½× | La mitad de luz |
| 0 | 1× | Referencia |
| +1 | 2× | El doble |
| +2 | 4× | Cuatro veces más |
| +3 | 8× | Ocho veces más |
| 6,5 | ~90× | Luz de área nueva (valor por defecto) |
| 8 | 256× | Clave del esquema «Tres puntos» |
| 10 | 1024× | Mil veces más que 0 pasos |

Reglas prácticas:

- **2×** y **½×** de la ficha suman o restan exactamente un paso.
- Medio paso (0,5) es un cambio suave; un paso entero ya se nota mucho.
- La relación entre clave y relleno se mide en pasos: en «Tres puntos» la clave está a 8 y el relleno a 6,5, es decir, la clave da 1,5 pasos más (casi el triple de luz).
- La potencia de una luz va de −4 a 24 pasos. El cielo se mueve entre −6 y 8, y el sol entre −2 y 10.

> **Consejo:** si dos luces directas se separan más de 8 pasos, la débil casi no se nota (es 256 veces más floja). La pestaña Comprobar te avisa de ello.

### Temperatura de color en Kelvin

La **temperatura de color** describe el tono de una luz «blanca» comparándolo con un cuerpo que se calienta: a pocos grados brilla naranja (como una vela) y a muchos, azulado (como el cielo). Se mide en **Kelvin (K)**. Cuanto más bajo, más cálida; cuanto más alto, más fría.

Las luces de Arnold tienen su propio atributo de temperatura y LightManager lo usa directamente. La barra **Color** de la ficha es un degradado de 1500 K a 12000 K (con más espacio para los tonos cálidos, que es donde más se elige). Al lado ves el valor exacto y la flecha **▾** con estos atajos:

| Atajo | Kelvin | Para qué |
|---|---|---|
| **Vela** | 1900 K | Velas, fuego, luz muy íntima |
| **Halógena** | 3000 K | Focos halógenos, lámparas de casa |
| **Tungsteno** | 3200 K | Bombilla clásica, luz de cine de interior |
| **Flash / día** | 5600 K | Sol de mediodía, flash de estudio |
| **Nublado** | 6500 K | Día cubierto, luz neutra |
| **Cielo azul** | 10000 K | Sombra a pleno sol, luz de relleno fría |

Otros valores que usa LightManager: las bombillas que crea en las lámparas van a 2700 K; las luces de punto nuevas a 2700 K; los focos nuevos a 3200 K; las áreas nuevas a 5600 K; la clave de «Tres puntos» a 4800 K y su relleno a 6500 K.

> **Consejo:** mezclar una clave cálida con un relleno frío (o al revés) da mucho volumen y sensación de realismo. Es lo que hacen los esquemas «Atardecer» y «Retrato Rembrandt».

## El panel

El panel tiene tres partes:

- **Cabecera**: los botones de modo **Estudio** y **Escena**, y el desplegable **Agrupar:** (**Por papel**, **Por zona**, **Por tipo** o **Por grupo de luz**). Cada modo recuerda su forma de agrupar.
- **Vista**: en Estudio, la órbita; en Escena, un visor de Maya desde arriba.
- **Pestañas**: **Luces**, **Esquemas**, **Cielo**, **Enlaces**, **Escenarios** y **Comprobar**. Abajo del todo, una línea de estado te dice qué acaba de pasar o qué tienes que hacer (por ejemplo, «Haz clic en el visor donde quieres el brillo. Esc para terminar.»).

### Estudio o Escena

- **Estudio** sirve para luces alrededor de un objeto: esquemas de estudio y vista de órbita.
- **Escena** sirve para interiores y exteriores: zonas, ventanas, lámparas, sol por hora y lugar.

Las dos comparten la lista, la ficha, los escenarios y las comprobaciones. Cada escena recuerda el último modo que usaste. Si no hay ninguno guardado, LightManager propone **Escena** cuando hay zonas, portales, un sol físico activo o cuatro o más lámparas; si no, **Estudio**.

## La lista de luces

La pestaña **Luces** muestra todas las luces de Maya y de Arnold de la escena, agrupadas según el desplegable **Agrupar:**. Cada grupo lleva entre paréntesis cuántas luces tiene.

Columnas:

- **Luz**: casilla para encender o apagar, un punto con el color de la luz y su nombre. La casilla del grupo enciende o apaga todo el grupo.
- **Solo**: haz clic en el punto para ver solo esa luz. La «S» naranja marca las que están en solo.
- **Pasos**: la potencia de la luz.

Las luces que no cuentan en el render (apagadas o tapadas por un solo) salen en gris.

Con **clic derecho** sobre una luz tienes: **Solo**, **Quitar todos los solos**, **Encender solo este grupo** (enciende todo el grupo si alguna está apagada; si están todas encendidas, las apaga), **Duplicar** y **Borrar**.

Encima de la lista están los botones:

- **+ Nueva ▾**: crea una luz nueva de tipo **Área**, **Foco**, **Punto**, **Fotométrica (IES)**, **Sol** o **Cielo**. Las luces nuevas se colocan alrededor de lo seleccionado (o de toda la escena), mirándolo, con una potencia ajustada a su tamaño.
- **Duplicar**: copia la luz elegida y la gira 30° alrededor del objeto.
- **Borrar**: borra las luces elegidas (`Ctrl+Z` para deshacer).

La lista y la selección de Maya van sincronizadas: si eliges una luz en el Outliner, se elige en el panel, y al revés. Si cambias algo en el Attribute Editor, el panel lo recoge al volver a pasar el ratón por encima.

> **Nota:** las luces que crea LightManager se llaman `LM_<nombre>` y van al grupo `LM_luces`. En la lista se ven sin el prefijo.

### Ficha de la luz

Al elegir una luz aparece su ficha. Solo salen los controles que tienen sentido para ese tipo de luz:

- **Nombre**: renómbrala aquí. Al lado ves su tipo (Área, Foco, Sol…).
- **Papel**: **Clave**, **Relleno**, **Contra**, **Ambiente**, **Prácticas**, **Ventanas**, **Efecto** o **Sin papel**. Sirve para agrupar la lista y para algunas comprobaciones.
- **Zona** (solo en Escena): **Automática** (la zona en la que está la luz) o una zona fija. Si la fijas, no cambia aunque muevas la luz.
- **Grupo de luz**: escribe o elige un nombre. Las luces del mismo grupo salen juntas en un AOV para mezclarlas después del render (ver [Enlaces y grupos de luz](#enlaces-y-grupos-de-luz)).
- **Potencia**: en pasos, con **½×** y **2×**.
- **Color**: barra de Kelvin con los atajos de la flecha **▾**. No sale en el cielo ni en los portales, que no tienen temperatura propia.
- **Giro** (solo cielo): gira el HDRI de 0° a 360°.
- **Tamaño**, **Radio** o **Ángulo (°)**: según el tipo. En las áreas es su tamaño; en focos, puntos y fotométricas, el radio; en el sol, el ángulo que ocupa en el cielo. Una luz más grande da sombras más suaves.
- **Perfil IES** (solo fotométricas): el reparto de la luz de una lámpara real (ver [Colocar](#colocar-y-perfiles-ies)).
- **Muestras**: de 1 a 10. Déjalo bajo; más de 4 hace el render mucho más lento.
- **Se ve en cámara**: si la luz aparece en la imagen. En un área suele estar desactivado (si no, sale un rectángulo blanco).
- **Alrededor**, **Altura** y **Distancia** (solo en Estudio): la posición de la luz en la órbita, en grados y en múltiplos del tamaño del objeto.
- **Gemela de N luces** y **Separar**: si la luz es parte de una fila de gemelas, cambian juntas; **Separar** hace que esta deje de cambiar con las demás.
- **Arnold · …**: la última línea dice los valores reales (potencia como multiplicador, Kelvin, tipo de nodo y AOV de su grupo). Se puede ocultar en los Ajustes.

Si eliges varias luces, los cambios de la ficha se aplican a todas.

## Estudio: órbita y Apuntar

### La órbita

En modo Estudio, la vista de arriba es un esquema visto desde arriba: el objeto en el centro, la cámara de render abajo (el triángulo) y cada luz como un punto de su color, con una línea hacia el objeto. Los círculos de guía marcan distancias de 1, 2, 3, 4, 6 y 8 veces el tamaño del objeto.

- **Arrastra un punto** para girar la luz alrededor del objeto (y acercarla o alejarla). Al soltar, la luz se recoloca mirando al objeto.
- **Rueda del ratón** sobre la órbita: sube o baja 5° la altura de las luces elegidas.
- **Clic en un punto**: elige esa luz.

Los puntos de las luces apagadas salen transparentes y los de las luces más altas, un poco más grandes.

### Apuntar en el visor

Con una luz elegida, los botones **Luz**, **Reflejo** y **Sombra** te dejan colocarla con un clic en el visor de Maya. La luz mantiene su distancia a lo que ilumina. Puedes hacer varios clics seguidos; pulsa `Esc` para terminar.

- **Luz**: haz clic en el objeto y la luz se coloca para iluminar ese punto de frente.
- **Reflejo**: haz clic donde quieres ver el brillo y la luz se coloca para que su reflejo caiga ahí visto desde la cámara. Ideal para productos brillantes.
- **Sombra**: haz clic donde quieres que caiga la sombra del objeto.

Con el **sol** solo cambia la dirección (su posición no importa). Con el **cielo**, Apuntar gira el HDRI para que su sol caiga donde has hecho clic.

## Esquemas

La pestaña **Esquemas** tiene un desplegable con cuatro familias: **Estudio**, **Interior**, **Exterior** y **Mis esquemas**. Cada esquema lleva su nombre, una descripción y un botón **Aplicar**.

La casilla **Reemplazar el esquema anterior** (marcada por defecto) borra las luces que puso el último esquema antes de poner las nuevas. Desmárcala si quieres sumar esquemas.

### Esquemas de estudio

Crean luces alrededor de lo seleccionado (o de toda la escena si no hay nada seleccionado), con el ángulo medido desde la cámara de render. Se adaptan a cualquier escala: una taza de 10 cm y un coche de 4 m quedan igual de iluminados, porque la distancia va en múltiplos del tamaño del objeto y la potencia se compensa (la luz cae con el cuadrado de la distancia).

| Esquema | Luces | Para qué |
|---|---|---|
| **Tres puntos** | Clave (8 pasos, 4800 K), Relleno (6,5, 6500 K), Contra (7,5, 5600 K) | El punto de partida clásico |
| **Producto en estudio** | Cenital, Lateral izq, Lateral der y un cielo de estudio | Caja de luz para productos |
| **Retrato Rembrandt** | Clave alta y cálida (3800 K) y un rebote suave | Mucho volumen en retratos |
| **Contraluz** | Dos contras y un relleno muy bajo | Silueta con borde brillante |
| **Exterior día** | Sol (5600 K) y cielo azul | Sol nítido alrededor del objeto |
| **Atardecer** | Sol bajo a 2600 K y cielo frío | Sombras largas y cálidas |
| **Noche** | Luna fría (9500 K), farola cálida (2200 K) y cielo muy tenue | Ambiente nocturno |

Los esquemas con cielo usan un HDRI del pack inicial (ver [Cielo](#cielo-hdri-y-sol)). Si no lo has descargado, el cielo se crea igual pero sin imagen.

> **Consejo:** también puedes poner «Tres puntos» sin abrir el panel: clic derecho en el icono del estante → **Tres puntos en lo seleccionado**.

### Esquemas de interior y exterior

No ponen luces alrededor de nada: ajustan el sol, el cielo y las lámparas de toda la escena de una vez, y pasan el panel al modo Escena.

| Familia | Esquema | Qué hace |
|---|---|---|
| Interior | **Interior de día** | Sol a mediodía y cielo físico, con portales en las ventanas seleccionadas |
| Interior | **Interior al atardecer** | Sol una hora antes de la puesta, portales y lámparas encendidas |
| Interior | **Interior de noche** | Sin sol, cielo muy tenue (−4 pasos) y todas las lámparas encendidas |
| Exterior | **Exterior de día** | Sol y cielo físico a mediodía en tu ciudad |
| Exterior | **Primera hora** | Sol una hora después de la salida, sombras largas |
| Exterior | **Atardecer** | Media hora antes de la puesta: sol naranja y rasante |
| Exterior | **Nublado** | Sin sol directo, solo un HDRI de cielo suave |
| Exterior | **Noche urbana** | HDRI nocturno, farolas y lámparas encendidas |

Las horas se calculan con la salida y la puesta de sol reales del lugar y la fecha que tengas en la pestaña **Cielo**.

### Mis esquemas

Coloca unas luces a tu gusto y pulsa **Guardar las luces como esquema…**. Escribe un nombre y se guarda como un archivo `.json` en tu carpeta de *Mis esquemas*. Se guarda como esquema de estudio: posiciones relativas al objeto y a la cámara, así que lo puedes reutilizar en otras escenas y con objetos de otro tamaño.

**Abrir la carpeta** te lleva a esa carpeta, por si quieres copiar esquemas a otro ordenador o compartirlos.

## Escena: interiores y exteriores

En modo **Escena**, la vista de arriba es un visor de Maya de verdad metido en el panel (Viewport 2.0), con tres botones:

- **Arriba**: la escena vista desde arriba con una cámara ortográfica (`LM_camara_cenital`), para colocar luces y dibujar zonas.
- **Cámara**: mirar por la cámara de render.
- **Encuadrar**: encuadra toda la escena en la vista de arriba.

En la pestaña **Luces** aparece además una fila de herramientas: **Colocar ▾**, **Ventanas → portales**, **Lámparas**, **Malla → luz**, **Repetir** y **Zonas ▾**.

### Zonas

Maya no sabe qué es una cocina, así que una zona es una caja con nombre: un nodo `LM_zona_<nombre>` (una caja de curvas que no sale en el render) dentro del grupo `LM_zonas`. Cada luz pertenece a la zona más pequeña que la contiene; si no está en ninguna, a **Escena**. El cielo y el sol siempre van a **Escena**.

El menú **Zonas ▾** tiene:

- **Zona con los objetos seleccionados…**: selecciona, por ejemplo, el suelo y las paredes de una habitación, y escribe el nombre (cocina, salón…).
- **Dibujar un rectángulo en la vista…**: arrastra un rectángulo en la vista de arriba para marcar la zona.
- **Una zona por grupo del Outliner**: si tienes la casa organizada en grupos por habitación, crea una zona por cada grupo de golpe.
- **Revisar a qué zona va cada luz**: recoloca en su zona las luces que has movido.
- **Borrar zona**: un submenú con las zonas que existen.

Con **Agrupar: Por zona** la lista queda ordenada por habitaciones, y con la casilla de cada grupo enciendes o apagas una habitación entera.

### Colocar y perfiles IES

**Colocar ▾** pone una luz pegada a una pared, al techo o al suelo con un clic en el visor (haz clic varias veces para poner varias; `Esc` para terminar). La luz toma la zona en la que cae y se llama, por ejemplo, «Downlight salón».

Un **perfil IES** describe cuánta luz sale de una lámpara en cada dirección: es lo que dibuja el típico abanico de un downlight en la pared. LightManager trae ocho perfiles genéricos, hechos con fórmulas propias (no copian datos de ningún fabricante):

| Perfil | Cómo reparte la luz |
|---|---|
| **Bombilla** | Casi igual en todas direcciones |
| **Downlight de techo** | Hacia abajo, con un corte marcado (abanico en la pared) |
| **Foco estrecho** | Un haz muy cerrado |
| **Foco ancho** | Un haz abierto |
| **Aplique de pared** | Hacia arriba y hacia abajo |
| **Lámpara de pantalla** | Sobre todo hacia abajo, algo hacia arriba y un poco a los lados |
| **Farola** | Hacia abajo y en ángulo, para iluminar la calle |
| **Tira LED** | Hacia arriba, muy abierta |

Además de los perfiles, **Colocar ▾** tiene **Punto** y **Área** sin perfil. Puedes cambiar el perfil de una luz fotométrica en su ficha (**Perfil IES**) y añadir tus propios archivos `.ies` desde los Ajustes.

### Ventanas → portales

En un interior, casi toda la luz del cielo entra por las ventanas y Arnold tarda en encontrarla, lo que da ruido. Un **portal** guía la luz del cielo a través de la ventana y baja el ruido.

1. Selecciona las mallas de las ventanas (los cristales o los huecos).
2. Pulsa **Ventanas → portales**.

Se crea un portal en cada ventana, mirando hacia dentro, con papel **Ventanas** y la zona que le toca. Además, el cielo pasa a modo portal. Los portales no emiten luz por sí mismos: solo funcionan si hay un cielo.

### Lámparas

Selecciona las pantallas de tus lámparas (o una farola) y pulsa **Lámparas**. Se pone una bombilla fotométrica (perfil de lámpara de pantalla, 2700 K, papel **Prácticas**) en el centro de cada objeto, y el objeto deja de hacerle sombra para que la luz no se quede atrapada dentro.

### Malla → luz

Convierte las mallas seleccionadas en luces de malla. Sirve para tiras LED, pantallas o neones que tienen una forma concreta.

### Repetir: luces gemelas

Para una fila de downlights en un pasillo:

1. Elige la luz de partida.
2. Pulsa **Repetir** y di cuántas copias quieres (por defecto, las de los Ajustes).
3. Haz clic en el visor donde debe acabar la fila.

Las copias son **gemelas**: si cambias la potencia o el color de una, cambian todas. En la ficha lo verás como «Gemela de N luces: cambian juntas». Con **Separar**, una luz deja de cambiar con las demás.

## Cielo: HDRI y sol

### HDRI

La sección **HDRI** muestra en miniatura las imágenes de tu carpeta de HDRI (`.hdr`, `.exr`, `.tx`, `.tif`, `.jpg`, `.png`). Haz clic en una para ponerla en el cielo (si no hay cielo, se crea).

- **Carpeta de HDRI…**: elige otra carpeta.
- **Descargar pack (CC0)**: descarga ocho HDRI de [Poly Haven](https://polyhaven.com) a 2K, con licencia CC0 (uso libre). Necesitas conexión a internet. Si falla, te dice dónde bajarlos a mano y en qué carpeta dejarlos.

| HDRI del pack | Para qué |
|---|---|
| studio_small_09 | Estudio neutro |
| brown_photostudio_02 | Estudio cálido |
| kloofendal_48d_partly_cloudy_puresky | Cielo de mediodía |
| venice_sunset | Atardecer |
| rural_asphalt_road | Exterior despejado |
| lebombo | Interior con ventanas |
| potsdamer_platz | Ciudad |
| dikhololo_night | Noche |

Debajo tienes **Giro** (0° a 360°), **Potencia** en pasos y **Se ve en cámara** (si el fondo del HDRI sale en la imagen).

- **Sol desde el HDRI**: busca el sol en la imagen y pone una luz direccional alineada con él, para tener sombras nítidas. Si el HDRI no tiene un sol claro (cielo nublado o de estudio), te lo dice.
- **Cielo físico**: cambia el HDRI por un cielo de Arnold que sigue al sol de la hora y el lugar elegidos.

### Sol físico (modo Escena)

En modo Escena aparece la sección **Sol**, que coloca el sol real según:

- **Lugar**: 25 ciudades, entre ellas Madrid, Barcelona, Sevilla, Valencia, Bilbao, Santiago de Compostela, Las Palmas de Gran Canaria, Lisboa, Londres, París, Roma, Berlín, Oslo, Reikiavik, Nueva York, Los Ángeles, Ciudad de México, Bogotá, Lima, Buenos Aires, Santiago de Chile, El Cairo, Dubái, Tokio y Sídney. Tiene en cuenta el horario de verano europeo y estadounidense.
- **Fecha**: con calendario.
- **Hora**: de 0 a 24 h en cuartos de hora. Debajo ves a qué hora sale y se pone el sol ese día y su altura actual, por ejemplo «Sale a las 06:45 · se pone a las 21:49 · ahora a 62°».
- **Potencia**: los pasos del sol a mediodía (por defecto, 3).
- **Norte**: cuántos grados hay que girar la escena para que su norte quede hacia −Z (arriba en la vista Top de Maya).
- **Encender las lámparas al anochecer**: con el sol por debajo de 3° de altura, las luces prácticas (focos, puntos, fotométricas y mallas) se encienden solas; de día se apagan.

Pulsa **Poner el sol** para crearlo la primera vez. Después, cada cambio de hora, fecha o lugar lo recoloca al momento.

El sol no solo cambia de dirección: también de color y de fuerza según su altura, porque cerca del horizonte la luz atraviesa más atmósfera. Con una potencia de 3 pasos a mediodía:

| Altura del sol | Color | Potencia |
|---|---|---|
| 0° (horizonte) | 2000 K | −5 pasos (8 menos que a mediodía) |
| 5° | 3050 K | 0,5 pasos |
| 10° | 3550 K | 1,2 pasos |
| 20° | 4400 K | 1,9 pasos |
| 30° | 5050 K | 2,3 pasos |
| 40° o más | 5600 K | de 2,5 a 3 pasos |

Si el sol está bajo el horizonte, se apaga.

> **Consejo:** para un atardecer de interior, usa el esquema **Interior al atardecer** y luego mueve la **Hora** poco a poco: verás cómo la luz entra cada vez más rasante y naranja por la ventana.

## Enlaces y grupos de luz

### Enlaces

La pestaña **Enlaces** es una tabla de luces (filas) por objetos (columnas) que dice qué ilumina cada luz. Haz clic en una casilla para cambiarla entre tres estados:

- **●** Ilumina y hace sombra.
- **◐** Ilumina sin hacer sombra.
- **○** No le afecta.

Es el *light linking* y *shadow linking* de Arnold, pero a la vista. Si tienes luces elegidas en la lista, solo salen esas filas. Con **Usar los objetos seleccionados** la tabla muestra solo los objetos que tengas seleccionados en Maya; **Todos los objetos** vuelve a mostrarlos todos (hasta 40 columnas).

### Grupos de luz y AOV

Debajo, la sección **Grupos de luz** lista los grupos que has puesto en las fichas. **Crear los AOV de grupos** activa los grupos de luz en el AOV `RGBA` de Arnold, de forma que cada grupo sale en su propio AOV `RGBA_<grupo>`. Así puedes subir o bajar cada grupo de luces después del render, en composición, sin volver a renderizar.

> **Nota:** el texto de ayuda del panel dice que la mezcla se hace en RenderDesk, pero la versión de RenderDesk incluida en el pack aún no tiene mezclador de luces: por ahora, mezcla los AOV `RGBA_<grupo>` en tu programa de composición.

## Escenarios

Un **escenario** es una foto del estado de la iluminación: de cada luz, si está encendida, su potencia, su color, su posición, su tamaño y su HDRI; y además el estado del sol (hora, fecha y lugar). Se guardan dentro de la propia escena.

- **Guardar como está**: pide un nombre (por defecto «Escenario 1», «Escenario 2»…) y guarda la foto. En la lista verás el nombre y la fecha y hora en que lo guardaste.
- **Recuperar**: vuelve al escenario elegido (`Ctrl+Z` para deshacer).
- **Comparar**: mantén pulsado para ver el escenario elegido; al soltar vuelves a como estabas. Muy útil con el render interactivo abierto.
- **Borrar**: borra el escenario elegido.

Las luces que crees después de guardar un escenario no se tocan al recuperarlo.

## Comprobar

La pestaña **Comprobar** revisa la iluminación y muestra un semáforo: **rojo** hay que arreglarlo (render negro, solo olvidado…), **ámbar** conviene mirarlo y **verde** está bien. Arriba, un resumen («3 cosas que mirar» o «Todo en orden.»). Casi todos los avisos tienen un botón que lo arregla y otro, **Seleccionar**, que elige las luces afectadas.

| Aviso | Nivel | Por qué importa | Arreglo |
|---|---|---|---|
| No hay ninguna luz | Rojo | Arnold no usa la luz por defecto de Maya: el render sale negro | **Poner tres puntos** |
| Solo activo en… | Rojo | Las demás luces están apagadas en el render | **Quitar el solo** |
| Todas las luces están apagadas | Rojo | El render sale negro | **Encender todas** |
| Sombras negras | Ámbar | Solo hay una luz directa, sin cielo ni relleno | **Añadir cielo** |
| «…» casi no se nota | Ámbar | Está más de 8 pasos por debajo de la más fuerte | Súbela o apágala |
| Áreas estiradas | Ámbar | Escala no uniforme: el brillo se reparte en un rectángulo | Revisa la escala |
| Sin caída cuadrática | Rojo | Las luces de Maya sin caída cuadrática no se comportan como luces reales | **Poner cuadrática** |
| HDRI sin .tx | Ámbar | Arnold lo convierte en cada render | **Convertir a .tx** |
| No se encuentra el HDRI | Rojo | El cielo sale de un color plano | Elige otro HDRI en Cielo |
| Portales sin cielo | Rojo | Los portales solo guían la luz de un cielo | **Añadir cielo** |
| El cielo no usa los portales | Ámbar | Sin modo portal, el ruido no baja | **Usar portales** |
| «…» está dentro de «…» | Ámbar | La pantalla tapa la bombilla | **Quitar la sombra** |
| Muestras altas | Ámbar | Más de 4 muestras en una luz hace el render mucho más lento | **Bajar a 1** |
| Luces sin nombrar | Ámbar | Nombres de fábrica como `aiAreaLight1` | **Nombrar por papel** |
| Áreas visibles en cámara | Ámbar | Salen en la imagen como rectángulos blancos | **Ocultar en cámara** |

Pulsa **Comprobar otra vez** después de hacer cambios a mano. También puedes abrir esta pestaña directamente con clic derecho en el icono del estante → **Comprobar la iluminación**.

## Ajustes

En la [ventana central](ventana-central.md) de MantiTools, **Ajustes → LightManager**. Se guardan en `<preferencias de Maya>/lightmanager/ajustes.json` y el panel los recoge al momento.

### Panel

- **Modo al abrir**: **Según la escena** (propone Escena si hay zonas, portales, sol o muchas lámparas), **Estudio** o **Escena**. Aun así, cada escena recuerda el último modo usado.
- **Agrupar en Estudio**: cómo se agrupa la lista en Estudio (por defecto, **Por papel**).
- **Agrupar en Escena**: cómo se agrupa en Escena (por defecto, **Por zona**).
- **Ver los valores de Arnold en la ficha**: muestra u oculta la línea «Arnold · …» al pie de la ficha (activado por defecto).

### Bibliotecas

- **Carpeta de HDRI**: dónde están tus HDRI y dónde se descarga el pack. Vacía: dentro de las preferencias de LightManager.
- **Carpeta de Mis esquemas**: dónde se guardan tus esquemas. Vacía: dentro de las preferencias de LightManager.
- **Carpeta de perfiles IES**: tus propios archivos `.ies`, además de los ocho incluidos.

### Sol y escena

- **Lugar del sol**: la ciudad por defecto para el sol físico (Madrid si no lo cambias).
- **Norte de la escena**: grados que hay que girar la escena para que su norte quede hacia −Z (de −180° a 180°).
- **Encender las lámparas al anochecer**: activado por defecto.
- **Copias al repetir**: cuántas copias propone **Repetir** (de 1 a 50; por defecto, 3).

## Consejos

- Empieza siempre por un esquema y ajusta desde ahí: es más rápido que colocar luces una a una.
- Trabaja con el render interactivo de [RenderDesk](renderdesk.md) abierto y en **Borrador**: verás cada cambio de pasos o Kelvin casi al instante.
- Usa **Solo** para ver qué aporta cada luz y luego **Quitar todos los solos**. Si se te olvida, Comprobar te avisa.
- Ponle un **Papel** y un **Grupo de luz** a cada luz desde el principio. Te ahorra trabajo en la lista, en las comprobaciones y en composición.
- Para productos brillantes, usa **Apuntar → Reflejo**: colocar un brillo a ojo cuesta mucho más.
- Antes de un cambio grande, **Guardar como está** un escenario. Así puedes **Comparar** el antes y el después.
- Puedes seguir moviendo las luces con las herramientas de Maya: el panel lo recoge al volver a él.
- En interiores, pon portales en las ventanas aunque no veas ruido en las pruebas: en el render final se nota mucho.

## Problemas frecuentes

**El render sale negro.**
Abre **Comprobar**. Lo más habitual es que no haya ninguna luz (Arnold no usa la luz por defecto de Maya), que estén todas apagadas o que haya un solo olvidado. Los tres se arreglan con un botón.

**He movido una luz con el manipulador de Maya y el panel no se entera.**
Pasa el ratón por encima del panel: vuelve a leer la escena al entrar. Si la luz ha cambiado de habitación, usa **Zonas ▾ → Revisar a qué zona va cada luz**.

**El esquema me ha borrado luces.**
Con **Reemplazar el esquema anterior** marcado, se borran las luces que puso el último esquema. Pulsa `Ctrl+Z` y desmarca la casilla si quieres sumar los esquemas.

**El cielo del esquema sale de un color plano, sin imagen.**
El esquema usa un HDRI del pack inicial que no has descargado. Ve a **Cielo** y pulsa **Descargar pack (CC0)**, o elige otro HDRI de tu carpeta.

**La descarga del pack falla.**
Puede que la red del aula bloquee la descarga. El aviso te dice la web de donde bajarlos a mano y la carpeta en la que dejarlos.

**El interior tiene mucho ruido.**
Pon portales en las ventanas (**Ventanas → portales**) y comprueba que el cielo está en modo portal (Comprobar te avisa si no). Si sigue habiendo ruido, sube la calidad en [RenderDesk](renderdesk.md).

**Las lámparas no dan luz.**
Si creaste las bombillas a mano, la pantalla de la lámpara puede estar tapándolas. Comprobar lo detecta («… está dentro de …») y **Quitar la sombra** lo arregla. Las bombillas creadas con **Lámparas** ya vienen sin esa sombra.

**El sol sale por el lado equivocado.**
Ajusta el **Norte**: cuántos grados hay que girar la escena para que su norte quede hacia −Z. También puedes fijarlo en los Ajustes para todas tus escenas.

**Sol desde el HDRI dice que no hay un sol claro.**
El HDRI es nublado o de estudio y no tiene un punto mucho más brillante que el resto. Pon el sol a mano (**+ Nueva ▾ → Sol**) o usa el sol físico.

**No aparece la vista de arriba en modo Escena.**
Esa vista es un visor de Maya metido en el panel. Si sale el texto «Aquí se ve la escena desde arriba (visor de Maya)», cierra y vuelve a abrir el panel.

## Ver también

- [RenderDesk](renderdesk.md): render interactivo, calidad y render final para ver tu iluminación con Arnold.
- [Materials](materials.md): los materiales que reciben la luz.
- [Flujo de trabajo](flujo-de-trabajo.md): en qué orden usar las herramientas del pack.
- [Ajustes](ajustes.md) y [Ventana central](ventana-central.md): dónde se cambian las preferencias.
- [Problemas](problemas.md): soluciones a problemas generales del pack.
