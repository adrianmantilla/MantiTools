# GrassEditor · Guía rápida

Con GrassEditor cubres el suelo de hierba sin que Maya se vuelva lento. Tú dices dónde crece y qué
tipos de hierba lleva; GrassEditor reparte las matas y se encarga de que el visor y el render vayan
rápidos.

## 1. Instalar (una vez)

1. Descomprime el ZIP en una carpeta que no vayas a mover, por ejemplo `Documentos/Plugins/GrassEditor`.
2. Abre Maya 2026 o 2027 y arrastra el archivo `instalar.py` hasta el visor.
3. Si Maya pregunta por un plug-in no confiable («Untrusted Plugin Loading»), pulsa **Allow**.

Aparece el menú **GrassEditor** en la barra de Maya.

## 2. Tu primera pradera en tres pasos

1. Selecciona el suelo (o solo algunas caras).
2. **GrassEditor › Hierba en la selección (todo el suelo)**.
3. Abre **GrassEditor › Abrir GrassEditor…** y cambia la mezcla en la pestaña **2 · Hierba**.

¿Quieres pintar dónde crece? Usa **Hierba en la selección (para pintar)**: la capa empieza vacía
y el pincel queda activo. Pinta en el visor sobre el suelo.

## 3. Las cuatro pestañas

| Pestaña | Para qué |
| --- | --- |
| **1 · Zonas** | Dónde crece: pincel (Ctrl borra), todo el suelo o vacío, pendiente máxima, alturas, curvas (parterre, hueco, camino) y objetos de los que se aparta. |
| **2 · Hierba** | Qué crece: la mezcla de tipos y su parte, la densidad, la semilla y el editor de mata. |
| **3 · Rendimiento** | Cuánto pesa: visor ligero, cámara de render, recorte, detalle por distancia, aclarado, cifras y semáforo. |
| **4 · Acabado** | Material (Hierba simple o clay), convertir y exportar. |

## 4. Quiero…

| Quiero… | Cómo |
| --- | --- |
| Césped solo dentro de un parterre | Dibuja una curva cerrada, selecciónala y pulsa **Parterre (solo dentro)**. |
| Un camino sin hierba | Dibuja una curva abierta, ponle **Ancho** y pulsa **Camino**. |
| Que no crezca en las paredes de la loma | Baja la **Pendiente máxima** (30–40°). |
| Que no atraviese piedras ni troncos | **Buscar Árboles y Cantera** o selecciona objetos y **Añadir selección**. |
| Flores salpicadas en el prado | En **2 · Hierba**, **+ Tipo** → Flores silvestres al 10 %. |
| Otro reparto con los mismos ajustes | **Otra** (semilla). |
| Mis propias matas | Ajusta el tipo en el **Editor de mata** y **Guardar como nuevo…** |
| Ver cómo saldrá en el render | **Vista de render** (puede ir lento). |
| Que la escena abra rápido | **Hornear** la capa. |
| Deshacer | Ctrl+Z (Cmd+Z en Mac). Cada trazo del pincel es un paso. |

## 5. El semáforo

Abajo de la ventana verás un punto de color con las cifras de toda la escena:

- **Verde**: la escena va sobrada.
- **Ámbar**: se renderiza, pero cada cuadro tarda.
- **Rojo**: demasiada hierba para el ordenador del aula.

**Analizar escena** te dice qué capa y qué tipo pesan más y qué hacer. Lo primero casi siempre es
activar el **recorte por cámara** y el **detalle por distancia** en la pestaña Rendimiento, y
elegir la **cámara** con la que vas a renderizar.

## 6. Si algo va mal

- **No sale hierba**: comprueba que la capa está **Activa**, que la zona no está vacía y que la
  pendiente máxima no es muy baja.
- **El visor va lento**: baja **Mostrar** al 5 % o pon **Como: Cajas**.
- **En el render falta hierba en los bordes**: sube el **Margen** del recorte.
- **GrassEditor › Comprobar instalación** dice qué falla.
