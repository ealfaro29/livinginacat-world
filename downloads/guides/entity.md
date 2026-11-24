# Alfonsito con Entity by Sentient · Alfonsito with Entity by Sentient

[Español](#español) · [English](#english)

## Español

**Alfonsito** es el prototipo V1 de FT412. **Entity by Sentient** es el software que lo controla. La cámara ve el iPhone, el carro coloca la punta sobre el vidrio y el solenoide la baja para tocar. La Raspberry Pi coordina los movimientos con la MKS DLC32. La V2 es el diseño de una segunda máquina con estructura impresa. Las instrucciones de esta página corresponden a Alfonsito. [V1 y componentes](https://livinginacat.world/es/v1/) · [Diseño de la V2](https://livinginacat.world/es/v2/)

### Empezar desde otro equipo

| Dónde | Qué abrir | Qué hacer |
| --- | --- | --- |
| iPhone en la cama | [Alfonsito en Safari](https://entity.livinginacat.world/iphone?lang=es) | Usá **Compartir → Agregar a Inicio**. Abrí ese ícono, desbloqueá el iPhone y dejá visible la página durante la vinculación y calibración. |
| Computadora u otro teléfono | [Panel del operador](https://entity.livinginacat.world/?lang=es) | Iniciá sesión. En el primer uso, abrí **Vincular iPhone** e ingresá el código que aparece en el teléfono de la máquina. |
| Panel del operador | **Conectar equipo** | Comprobá por separado el brazo, la cámara y el iPhone. La etiqueta **En línea** indica que el panel puede comunicarse con Alfonsito. |
| iPhone en la cama | [Atajos del iPhone](https://entity.livinginacat.world/atajos?lang=es) | Seguí las dos tarjetas para configurar **PhysiClaw Upload Screenshot** y **PhysiClaw Clipboard** en AssistiveTouch. Copiá la dirección y la autorización que muestra cada tarjeta. |

Los enlaces son estables. El teléfono y quien opera la máquina pueden estar en redes distintas. Para volver después de apagarla, encendé Alfonsito, abrí el ícono del iPhone y entrá al panel desde el otro equipo.

### Calibrar la cámara y el toque

1. Asentá el teléfono en la cuna. Abrí **Opciones de cámara** en el panel y encuadrá los cuatro bordes del vidrio. La cuadrícula ayuda a centrarlo. Ajustá la luz si tapa alguna marca con un reflejo. [Vista de cámara](https://entity.livinginacat.world/camara?lang=es)
2. Entrá en **Calibrar**. Dejá abierta la página de Entity en el iPhone. El asistente muestra un patrón de 15 puntos para relacionar la imagen con el vidrio y luego pide verificar la precisión.
3. En la prueba de cinco blancos, mirá los dos resultados. El recuento del teléfono indica cuántos toques registró. El de la cámara indica cuántos blancos pudo localizar. Verificá ambos antes de seguir.
4. Cuando el asistente lo pida, arrastrá el botón flotante de AssistiveTouch al círculo indicado. Completá el asistente con el teléfono y la cámara en la misma posición.

Si cambiaste el teléfono, moviste la cámara o desplazaste el carro a mano con la máquina apagada, usá el asistente para restablecer la referencia correspondiente. Entre acciones, el carro puede apartarse a la esquina medida más cercana para despejar el vidrio.

### Enviar o programar una tarea

Abrí **Tarea y cola**. Escribí, por ejemplo, «Abrí la calculadora y multiplicá 89 por 90». **Agregar a la cola** la guarda para el próximo turno disponible. Para otra hora, elegí **Programar para después**, revisá la zona horaria que aparece y pulsá **Programar tarea**. Usá las flechas para subir o bajar una pendiente y **Eliminar** para quitarla. La máquina debe estar en línea para guardar la tarea y lista para ejecutarla. Podés cerrar el navegador después de guardarla. [Abrir Tareas y cola](https://entity.livinginacat.world/tareas?lang=es)

### Ver la actividad y probar la máquina

- En reposo, la pantalla MKS muestra **Entity by Sentient**. Durante una tarea muestra su título y la acción actual. Tocá **Cola** para recorrer las tareas pendientes.
- Para probar la puntería, abrí [Pulso](https://entity.livinginacat.world/jugar?lang=es) en el iPhone y **Abrir Pulso** en el panel del operador. **Jugar a mano** permite comprobar el juego con el dedo. **Jugar con Entity** inicia la ronda física. El iPhone cuenta los aciertos.
- Si el brazo figura desconectado y la cámara sigue en línea, revisá la alimentación de 12 V de la MKS y su USB a la Raspberry. Si la cámara ve los blancos pero faltan toques, revisá primero que el teléfono esté firme y que la punta llegue al vidrio. Si el teléfono sí registra los cinco, revisá el encuadre, los reflejos y la página visible en el iPhone.

Para piezas, herrajes, orden de armado y revisiones de impresión, consultá el [manual ilustrado de montaje](https://livinginacat.world/documentation/assembly/). El software parte de [PhysiClaw](https://github.com/physiclaw/PhysiClaw).

## English

**Alfonsito** is the working V1 FT412 prototype. **Entity by Sentient** operates it. A camera observes the iPhone, a carriage positions the stylus over the glass, and a solenoid lowers it for a tap. The Raspberry Pi coordinates motion through the MKS DLC32. V2 is a separate machine design with a printed frame. These instructions apply to Alfonsito. [V1 and components](https://livinginacat.world/v1/) · [V2 design](https://livinginacat.world/v2/)

### Connect from another device

| Where | What to open | What to do |
| --- | --- | --- |
| Mounted iPhone | [Alfonsito in Safari](https://entity.livinginacat.world/iphone?lang=en) | Use **Share → Add to Home Screen**. Open that icon, unlock the phone, and keep the page visible during pairing and calibration. |
| Operator’s computer | [Dashboard](https://entity.livinginacat.world/?lang=en) | Sign in, choose **Pair iPhone**, then enter the pairing code shown on the device. |
| Operator dashboard | **Connect equipment** | Check the arm, camera and iPhone individually. **Online** indicates that the dashboard can reach Alfonsito. |
| Mounted iPhone | [iPhone shortcuts](https://entity.livinginacat.world/atajos?lang=en) | Follow both cards to configure **PhysiClaw Upload Screenshot** and **PhysiClaw Clipboard** with AssistiveTouch. Copy the URL and authorization displayed on each card. |

The URLs stay the same across restarts. The operator and mounted phone can use different networks. To reconnect after powering down, turn Alfonsito on, open its Home Screen icon on the iPhone and sign in from the other device.

### Calibrate the camera and touch

1. Seat the iPhone in its cradle. Open **Camera settings** on the dashboard and frame all four edges of the glass. Use the grid for alignment and adjust the lighting if reflections obscure a marker. [Camera view](https://entity.livinginacat.world/camara?lang=en)
2. Open **Calibrate**. Leave the Entity page open on the iPhone. The wizard displays a 15-point pattern to map the camera image to the glass, then prompts you to check precision.
3. On the five-target test, read both counts. The phone reports touches it registered. The camera reports targets it located. Check both results before continuing.
4. When prompted, drag the floating AssistiveTouch button onto the indicated circle. Finish setup with the phone and camera in the same position.

If you swap phones, reposition the camera, or move the carriage by hand with power off, use the wizard to re-establish the affected reference. Between actions the arm can park at the nearest measured corner that clears the screen.

### Submit or schedule a task

Open **Task and queue**. For example, enter “Open Calculator and multiply 89 by 90.” **Add to queue** saves it for the next available turn. For a later time, choose **Schedule for later**, check the time zone shown, and select **Schedule task**. Move pending requests up or down with the arrows, or use **Remove**. The Pi must be online to accept a request and the rig must be ready to execute it. You can close the browser once the task is saved. [Open Tasks and queue](https://entity.livinginacat.world/tareas?lang=en)

### Follow a task and test the machine

- When idle, the MKS screen shows **Entity by Sentient**. During a task it shows the title and current action. Tap **Queue** to browse waiting tasks.
- Open [Pulse](https://entity.livinginacat.world/jugar?lang=en) on the iPhone and **Open Pulse** on the operator dashboard to check targeting. **Play by hand** lets you try the game with your finger. **Play with Entity** starts a physical round. The iPhone counts hits.
- If the arm is disconnected while the camera is online, check the MKS 12 V supply and its USB connection to the Pi. If the camera sees the targets but touches are missing, check that the phone is steady and the stylus reaches the glass. If the phone registers all five taps, check framing, reflections and the page visible on the phone.

For print revisions, fasteners and assembly order, see the [illustrated assembly manual in Spanish](https://livinginacat.world/documentation/assembly/). Entity is based on [PhysiClaw](https://github.com/physiclaw/PhysiClaw).
