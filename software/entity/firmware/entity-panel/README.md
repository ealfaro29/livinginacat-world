# Entity · TS24-R

## Español

Este módulo dibuja el arranque, la tarea y la cola de Entity en un lienzo LVGL de **320 × 240**. Usa fondo negro, texto blanco y acentos amarillo neón. Incluye el símbolo de Sentient, Space Grotesk y textos en español e inglés. La cola muestra tres tareas por página. Los toques devuelven una acción de navegación al programa que incorpora el módulo. Los títulos se muestran tal como los escribió el operador.

Con el equipo listo y sin tarea activa, la vista principal muestra el logo y **Entity by Sentient**. La cola sigue accesible aunque haya tareas esperando. Al recibir un cambio de estado, el programa que incorpora el módulo llama a `entity_panel_follow_task` con el último estado conectado y el nuevo. Cuando cambia la vista, vuelve a la primera página. Tras dibujar la vista de arranque, selecciona `ENTITY_TASK` para seguir el estado del equipo. [Vista de reposo renderizada](../../guides/pantalla-reposo.webp).

La prueba de escritorio enlaza el código con el LVGL 6.1 de Makerbase. Verifica el reposo en español e inglés, las transiciones, el acceso a la cola y la visibilidad del símbolo después del arranque. El firmware de Entity para la DLC32 V2.x integra la TS24-R y recibe por USB la tarea, la acción actual y la página de la cola seleccionada. Si la Raspberry se desconecta, el encabezado lo indica.

## English

This module draws Entity's startup, current task and queue on a **320 × 240** LVGL canvas. It uses a black background, white text and neon yellow accents. It includes the Sentient mark, Space Grotesk and Spanish and English controls. Each queue page shows three tasks. Hit testing returns a navigation action to the embedding program. Task titles retain the operator's wording.

When the rig is ready with no active task, the home view shows the logo and **Entity by Sentient**. The queue stays accessible while tasks wait. On state changes, the host calls `entity_panel_follow_task` with the last online state and the new state. Reset pagination when switching views. After drawing the startup screen, select `ENTITY_TASK` to follow the rig. [Rendered idle screen](../../guides/pantalla-reposo.webp).

The desktop check links against Makerbase’s LVGL 6.1 and verifies idle in both languages, transitions, queue access and the visibility of the logo after startup. The Entity firmware for the DLC32 V2.x drives the TS24-R and receives the active task, current action and selected queue page over USB. The header indicates when the Raspberry Pi disconnects.

## Prueba de escritorio / Desktop check

Con una copia del [firmware de Makerbase](https://github.com/makerbase-mks/MKS-DLC32-FIRMWARE/tree/e3edf9292f511ee44223021b2b8853e31b1aabe7), ejecutá el comando desde el proyecto. With that Makerbase firmware checkout available, run from the project root:

```sh
python3 firmware/entity-panel/host/render.py /path/to/MKS-DLC32-FIRMWARE /tmp/entity-frames
```

El comando genera imágenes PPM de cada vista en el directorio indicado. The command writes PPM images of each view to the output directory. [Capturas nativas / Native renders](../../guides/pantallas-nativas.png) · [Licencia de la fuente / Font license](../../src/physiclaw/static/entity/OFL.txt).

## Firmware de la DLC32 / DLC32 firmware

Con PlatformIO Core 6.1.18 y la copia oficial de Makerbase, este comando compila una imagen de aplicación para el ESP32. With PlatformIO Core 6.1.18 and an official Makerbase checkout, this command builds the ESP32 application image.

```sh
python3 firmware/entity-panel/esp32/build.py /path/to/MKS-DLC32-FIRMWARE firmware/output/entity-ts24-corexy.bin
```

**Instalación.** Para esta DLC32, la partición de aplicación empieza en `0x10000` y mide `0x300000` bytes. Antes de escribir, registrá la posición estacionada, la configuración GRBL y la calibración. Detené el servicio que ocupa el USB, guardá los 8 MiB completos de la memoria y verificá la copia y la tabla de particiones. Escribí únicamente la imagen de aplicación en su partición y verificá la lectura. La copia completa del mismo dispositivo permite recuperar su programa y sus ajustes anteriores. El servicio de Entity activa el envío de estado con `ENTITY_MKS_PANEL=1`. La ruta local `/entity/display/state` informa la última vista dibujada, los refrescos completados y los toques de navegación.

**Installation.** On this DLC32 the application partition starts at `0x10000` and is `0x300000` bytes long. Record the parked position, GRBL settings and calibration. Stop the service using USB, back up all 8 MiB of flash and verify the backup and partition table. Write the application image into its partition and verify readback. The complete backup from the same device restores its previous program and settings. The Entity service enables the status feed with `ENTITY_MKS_PANEL=1`. The local `/entity/display/state` endpoint reports the last rendered view, completed flushes and navigation touches.

[Base CoreXY de Makerbase / Makerbase CoreXY source](https://github.com/makerbase-mks/MKS-DLC32-FIRMWARE/tree/e3edf9292f511ee44223021b2b8853e31b1aabe7) · [Pantalla TS24-R y controlador táctil / TS24-R display and touchscreen](https://github.com/MarlinFirmware/Marlin/blob/22831028e75b19d9c53b213ce7757172ac137f6b/Marlin/src/pins/esp32/pins_MKS_DLC32_V2_1.h).
