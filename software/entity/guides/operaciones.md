# Continuar Entity / Continue working on Entity

## Español

Alfonsito es la V1 operativa. La Raspberry ejecuta Entity sobre PhysiClaw v0.11.5, recibe la imagen de la Logitech C922 y coordina por USB la controladora MKS DLC32 V2.2. Los dos TMC2209 mueven el sistema CoreXY y el controlador Adafruit acciona el solenoide de la punta. La pantalla TS24-R ofrece la tarea actual y la cola. La consola V2 tiene un diseño mecánico y una alimentación propios. Los ensayos de la V1 solo describen esa máquina.

**Primera sesión.** Abrí el panel como operador y la página de vinculación en el iPhone. Para cámara nueva o posición nueva, recorré el asistente con el teléfono en la cuna. Una apertura del panel sirve para consultar el estado. Para los botones, los dos atajos, la prueba de precisión y Pulso, seguí la [guía de acceso remoto](../remote/README.md#español), la [guía de calibración](telefono.md#español), la [guía de pantalla](pantalla.md#español) y la [guía de Pulso](pulso.md#español).

### Seguir una tarea desde el código

1. El operador abre **Tarea y cola** en el panel y envía la instrucción o elige la hora. El navegador muestra su zona horaria y envía la hora en UTC. Conserva el borrador en esa pestaña si se pierde la conexión. El panel necesita alcanzar a la Raspberry para guardar un pedido.
2. El Worker valida sesión y origen. El gateway privado entrega la petición a `/entity/api/tasks`. El proceso de Entity añade una fila a la base SQLite del perfil activo. El identificador de solicitud permite reintentar un envío sin crear dos trabajos.
3. La Raspberry toma la primera tarea disponible al llegar su hora, siempre que el equipo esté listo y la calibración de precisión sea válida. Una tarea futura deja pasar a las que pueden empezar hoy. Las flechas mueven una posición y **Eliminar** retira una pendiente. El agente y la pantalla comparten el registro que está en curso. El resultado se guarda en el historial.
4. Un reinicio conserva las pendientes. Un trabajo que se interrumpe durante la ejecución queda marcado como interrumpido para que el operador decida si lo repite. Los clientes MCP externos siguen iniciando y terminando sus propias órdenes.

### Dónde cambiar cada cosa

| Parte | Entrada |
| --- | --- |
| Panel web, sesión de operador, vinculación del iPhone | [Worker y vistas](../remote/edge/worker.mjs) · [Interfaz del panel](../remote/edge/views.mjs) |
| Formulario, hora local y prioridad | [Cliente de tareas](../remote/pages/site/ui/tasks.js) · [API de la cola](../src/physiclaw/entity/task_routes.py) |
| Persistencia y ejecución con el proveedor configurado | [SQLite y permisos de movimiento](../src/physiclaw/entity/tasks.py) · [Ejecución de una tarea](../src/physiclaw/entity/dispatcher.py) |
| Operaciones sobre el teléfono | [Herramientas de visión y gestos](../src/physiclaw/core/server/tools.py) · [Control del equipo](../src/physiclaw/core/orchestration/rig.py) |
| Cámara, marcas y estacionamiento | [Cámara](../src/physiclaw/entity/camera.py) · [Recorrido](../src/physiclaw/entity/travel.py) · [Selección de esquina](../src/physiclaw/core/calibration/parking.py) |
| Pantalla física y firmware | [Publicador de estado](../src/physiclaw/entity/panel.py) · [Firmware, compilación y recuperación](../firmware/entity-panel/README.md) |
| Acceso desde Internet | [Redirección privada de rutas](../remote/pi/origin.py) · [Entrada de Pages](../remote/pages/site/_worker.js) |

### Comprobar y desplegar

Desde la carpeta de Entity, ejecutá los comandos de la sección final. El visor local funciona sin hardware. Para editar la cola en producción, se necesita una sesión de operador. Una comprobación de publicación puede programar dos tareas para una fecha futura, moverlas, recargar, comparar la cola del panel con la MKS y eliminar solo esas dos. Un ensayo de movimientos requiere que el teléfono, la referencia y la calibración estén en posición.

En la Raspberry, el perfil activo contiene `entity/tasks.sqlite3` y `calibration/bundle.json`. Los servicios de usuario `entity.service` y `entity-pulse.service` mantienen el control y el juego. Los servicios de sistema `entity-online-origin.service` y `entity-online-tunnel.service` publican las rutas autorizadas. El puerto de control es 8048, el puente del teléfono 8049, Pulso 8050 y el gateway local 8052. La URL pública permanece fija al reiniciar.

Antes de actualizar la Pi, comprobá si hay una tarea en marcha y conservá la versión anterior, los ajustes del equipo y una copia consistente de SQLite. Un cierre normal de Entity puede llevar el carro al fondo izquierdo con la punta levantada. Si alguien movió el carro a mano o se perdió la referencia, recuperala con el asistente. Publicá primero los cambios de la Pi compatibles con la web vigente, después Pages y el Worker. Para volver atrás, restaurá el código de esa capa y verificá que siga leyendo la cola del operador y la calibración. [Configuración de despliegue](../remote/README.md#deployment)

## English

Alfonsito is the working V1. The Pi runs Entity on PhysiClaw v0.11.5, receives the Logitech C922 camera feed and talks over USB to the MKS DLC32 V2.2. Two TMC2209 drivers operate the CoreXY system and the Adafruit driver switches the stylus solenoid. The TS24-R shows the active task and queue. V2 is a separate console design with its own mechanical and power layout. V1 tests describe the V1 machine.

**First session.** Sign in on the operator dashboard and open the pairing page on the mounted iPhone. After changing the phone or moving the camera, use the calibration wizard. See the [remote operator guide](../remote/README.md#english), [phone and calibration](telefono.md#english), [physical screen](pantalla.md#english) and [Pulse](pulso.md#english).

**Task lifecycle.** The operator enters an instruction, chooses the next available turn or sets a local date and time. The app sends a UTC timestamp to the Pi through the authenticated Worker. The profile’s SQLite database stores the full instruction, due time and priority. A due task starts when the equipment and precision calibration are ready. Future dates leave earlier eligible work free to run. Move pending requests up or down by one place, or remove them. The web app and the native screen read the same record. The tab preserves a draft on loss of connectivity. The Pi must be reachable to accept a new submission. Pending jobs survive a restart. An interrupted job requires an operator decision before replay. External MCP clients continue to start and finish their own orders.

**Source map.** Follow an instruction from the [browser](../remote/pages/site/ui/tasks.js) through the [gateway](../remote/pi/origin.py), [task API](../src/physiclaw/entity/task_routes.py), [queue](../src/physiclaw/entity/tasks.py) and [dispatcher](../src/physiclaw/entity/dispatcher.py). Read the [phone tools](../src/physiclaw/core/server/tools.py) for gesture behavior. The [camera](../src/physiclaw/entity/camera.py), [travel controls](../src/physiclaw/entity/travel.py), [parking geometry](../src/physiclaw/core/calibration/parking.py) and [MKS state feed](../src/physiclaw/entity/panel.py) serve separate purposes. The [firmware guide](../firmware/entity-panel/README.md) covers building and recovering the touchscreen.

**Deployment.** On the Pi, the active profile contains `entity/tasks.sqlite3` and `calibration/bundle.json`. User services `entity.service` and `entity-pulse.service` own the hardware and the game. System services `entity-online-origin.service` and `entity-online-tunnel.service` connect the gateway. Local ports are 8048 for control, 8049 for the bridge, 8050 for Pulse and 8052 for the private gateway. Before updates, check for active work and back up the installed code, calibration and SQLite. A normal shutdown can park the raised stylus at the rear-left reference. Use manual setup after a power cut or manual movement. Deploy backwards-compatible Pi changes first, then Pages and the Worker. Verify that the queue and calibration survive the update. Use two future tasks to test persistence, ordering and removal without phone gestures. [Deployment settings](../remote/README.md#deployment)

### Comandos / Commands

Run from the Entity source directory. Ejecutá desde la carpeta del código de Entity.

```sh
uv sync --locked --group dev
uv run --locked pytest -q tests/entity tests/core/server
node --test remote/edge/*.test.mjs remote/pages/*.test.mjs
uv run --locked entity preview
```

On the Pi / En la Raspberry, para consultar los servicios:

```sh
systemctl --user is-active entity.service entity-pulse.service
systemctl is-active entity-online-origin.service entity-online-tunnel.service
```
