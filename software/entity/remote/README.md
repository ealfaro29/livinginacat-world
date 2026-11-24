# Alfonsito en línea · Alfonsito online

## Español

1. Encendé Alfonsito y dale conexión a Internet a la Raspberry. Los servicios se inician solos.
2. En el iPhone que va en la cama, abrí [la página del iPhone](https://entity.livinginacat.world/iphone) en Safari y tocá **Compartir → Agregar a Inicio → Agregar**. Abrí el ícono **Alfonsito** y dejalo visible. Podés usar Wi-Fi o datos móviles. El QR del asistente abre esta misma página.
3. Desde cualquier otro teléfono o computadora, iniciá sesión en [el panel](https://entity.livinginacat.world/). La primera vez, elegí **Vincular iPhone** e ingresá el código de ocho dígitos que muestra el ícono. En las siguientes sesiones, abrí el ícono y usá **Conectar equipo** y **Calibrar** en el panel.

Los dos atajos de AssistiveTouch usan direcciones fijas incluso después de reiniciar Alfonsito o cambiar de red. En el iPhone, cada tarjeta abre el atajo existente y permite copiar su dirección y su autorización. [Atajos del iPhone](https://entity.livinginacat.world/atajos)

Para jugar, abrí [Pulso](https://entity.livinginacat.world/jugar) en el iPhone de la máquina y dirigí la ronda desde **Abrir Pulso** en el panel.

En **Opciones de cámara** podés ver el encuadre en vivo, mostrar la cuadrícula y ajustar la imagen. Cada control muestra lo que admite la cámara conectada. Alfonsito guarda los ajustes de las cámaras USB identificadas y los recupera al reconectarlas. El enlace de los pasos 7 y 8 abre la vista en otra pestaña. [Opciones de cámara](https://entity.livinginacat.world/camara)

Desde **Tarea y cola**, escribí una instrucción y elegí el próximo turno o una fecha. Las flechas cambian la prioridad y **Eliminar** retira una pendiente. [Tareas y cola](https://entity.livinginacat.world/tareas?lang=es)

## English

1. Power on Alfonsito and give the Pi internet access. Its services start automatically.
2. In Safari on the mounted iPhone, open [the iPhone page](https://entity.livinginacat.world/iphone?lang=en), tap **Share → Add to Home Screen → Add**. Open the **Alfonsito** icon and leave it visible. Wi-Fi and mobile data both work. The setup QR opens the same page.
3. On any other phone or computer, sign in to [the dashboard](https://entity.livinginacat.world/?lang=en). The first time, choose **Pair iPhone** and enter the eight-digit code shown on the mounted phone. On later visits, open its icon and use **Connect equipment** and **Calibrate** on the dashboard.

Both AssistiveTouch shortcuts keep the same URLs when Alfonsito restarts or changes networks. On the iPhone, each card opens the existing shortcut and lets you copy its URL and authorization. [iPhone shortcuts](https://entity.livinginacat.world/atajos?lang=en)

To play, open [Pulse](https://entity.livinginacat.world/jugar?lang=en) on the mounted iPhone and use **Open Pulse** on the dashboard to direct the round.

Open **Camera settings** to see the live view, show the grid, and adjust the image. The controls reflect the connected camera’s capabilities. Alfonsito remembers your adjustments for identified USB cameras and restores them on reconnect. The link in setup steps 7 and 8 opens the view in a separate tab. [Camera settings](https://entity.livinginacat.world/camara?lang=en)

In **Task and queue**, enter an instruction and choose the next available turn or a date. Use the arrows to reorder pending work and **Remove** to take it off the queue. [Tasks and queue](https://entity.livinginacat.world/tareas?lang=en)

## Deployment

Use the existing outbound tunnel and private Worker service binding. Apply the schema in `edge/schema.sql` to a new D1 database. For an existing installation without `sessions.scope`, run `edge/migrations/0001_phone_scope.sql` once, then apply `edge/migrations/0002_phone_pairing.sql`. The Worker secrets are `RELAY_KEY` (shared only with the private Pi proxy) and `SHORTCUT_KEY` (an independent random key used to derive method-specific shortcut credentials). Install `pi/entity-online.conf` and `pi/entity-pulse-online.conf` as drop-ins on the Pi’s user services `entity.service` and `entity-pulse.service` respectively. Reload the user systemd manager and restart idle services after updating Entity. The operator gateway, phone bridge, Pulse and tunnel origin listen on loopback. Deploy the edge Worker and the Pages front end. The shortcut settings page requires a session. Only the matching shortcut credential can upload an expected image or read queued text.
