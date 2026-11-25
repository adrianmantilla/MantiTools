---
titulo: La carpeta compartida
corto: Carpeta compartida
resumen: Una carpeta en red o en la nube que da a todo un grupo los mismos botones de Radial, las mismas recetas de Materials y, si se quiere, los mismos ajustes.
---

## Para qué sirve

Cuando varias personas trabajan con MantiTools en ordenadores distintos (un aula, un estudio, un equipo), una
carpeta compartida evita configurar cada ordenador a mano:

- **Radial** encuentra en ella los radiales del grupo.
- **Materials** encuentra recetas compartidas, que salen en su biblioteca.
- MantiTools puede **desactivar herramientas** y **fijar ajustes** para todos.

En la interfaz se llama **Carpeta de clase**.

## Elegir la carpeta

En la ventana central, **Ajustes › General › Carpeta de clase**, pulsa «…» y elige la carpeta (una unidad de red,
Google Drive, OneDrive, Dropbox…). Se lee al momento y cada vez que arranca Maya. Debajo verás un resumen de lo
que se ha leído.

## Qué lleva dentro

```
Carpeta/
├── mantitools_clase.json   ← opcional: herramientas desactivadas y ajustes fijados
├── radial/                 ← radiales compartidos de Radial
└── materials/              ← recetas compartidas de Materials (.json)
```

Cada herramienta busca solo su subcarpeta. Si una no existe, no pasa nada.

## Fijar ajustes con mantitools_clase.json

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

- **desactivar**: herramientas que no se cargan en ese grupo. Su tarjeta lo dice.
- **fijar**: por herramienta, clave y valor. Cada página de herramienta de esta wiki termina con la tabla de sus
  ajustes, y la columna **Clave** dice cómo se llama cada uno (por ejemplo, en [SimpleSave](simplesave.md)).

Lo fijado se aplica cada vez que arranca Maya y aparece con 🔒 en Ajustes: se ve, pero no se puede cambiar.

> [!WARNING]
> Si el JSON tiene un error (una coma de más, comillas que faltan), no se fija nada y **Comprobar instalación**
> lo avisa con la línea del error.

## Quitar la carpeta

Deja vacío el campo **Carpeta de clase**. Los ajustes fijados dejan de estar bloqueados y conservan el último
valor.
