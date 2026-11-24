# Teléfono y cámara / Phone and camera

## Español

1. Colocá el nuevo iPhone en la cama, desbloqueado y con el vidrio hacia arriba. Conectalo a Internet.
2. En Safari del **iPhone**, abrí `https://entity.livinginacat.world/iphone?lang=es`. En un teléfono nuevo, usá **Vincular iPhone** en el panel del operador e ingresá el código que muestra el teléfono. Dejá esa página abierta.
3. En la **Mac** con tu sesión de operador, abrí `https://entity.livinginacat.world/setup-hardware?lang=es`. En el primer paso debe aparecer **Teléfono conectado**. Si el teléfono o la cámara cambiaron, empezá en modo manual.
4. En **Atajos** del iPhone, prepará los dos atajos de abajo. En **Configuración → Accesibilidad → Tocar → AssistiveTouch**, activá AssistiveTouch. Asigná el atajo de captura a **Tocar una vez** y el de portapapeles a **Presión larga**. En [Atajos del iPhone](https://entity.livinginacat.world/atajos?lang=es), copiá la autorización de cada tarjeta en el encabezado Authorization de su propio atajo, incluso si lo recuperaste de iCloud.
5. Seguí el asistente. Encuadrá las cuatro esquinas del vidrio. Dejá cámara y teléfono fijos durante las mediciones. El brazo empieza las pruebas de toque en el paso que lo indica. El resultado de precisión y la confirmación final corresponden a este teléfono.

Entre toques, Alfonsito elige la esquina alcanzable más cercana que deja la punta fuera de la pantalla. En un apagado normal vuelve a la esquina superior izquierda, que sirve de referencia al encender. Si se corta la corriente en otra posición, usá el modo manual y alineá la punta con el círculo central.

| Atajo | Acciones en orden |
|---|---|
| Captura | **Tomar captura de pantalla** → **Obtener contenido de URL** con `https://entity.livinginacat.world/api/bridge/screenshot`, método **POST**, cuerpo **Archivo**, usando la captura anterior. |
| Portapapeles | **Obtener contenido de URL** con `https://entity.livinginacat.world/api/bridge/clipboard`, método **GET** → **Copiar al portapapeles** usando el resultado de la URL. |

## English

1. Set the new iPhone in the holder with the screen facing up and unlocked. Give it an internet connection.
2. In Safari **on the iPhone**, open `https://entity.livinginacat.world/iphone?lang=en`. For a new phone, choose **Pair iPhone** on the operator dashboard and enter the code displayed on the phone. Keep the page open.
3. On the **Mac**, signed in as the operator, open `https://entity.livinginacat.world/setup-hardware?lang=en`. The first step should say **Phone connected**. Use manual mode for a new phone or camera position.
4. In **Shortcuts** on the iPhone, prepare the two shortcuts below. In **Settings → Accessibility → Touch → AssistiveTouch**, enable AssistiveTouch. Assign the screenshot shortcut to **Single-Tap** and the clipboard shortcut to **Long Press**. Open [iPhone shortcuts](https://entity.livinginacat.world/atajos?lang=en) and copy each card’s authorization into the Authorization header of its matching shortcut, including ones restored from iCloud.
5. Follow the wizard. Frame all four corners of the glass. Keep the phone and camera fixed while it measures. The arm starts its tap tests at the indicated step. The accuracy result and final confirmation apply to this phone.

Between taps, Alfonsito picks the nearest reachable corner that clears the screen. A clean shutdown returns it to the upper-left reference corner. If power is lost elsewhere, use manual setup and align the tip with the center dot.

| Shortcut | Actions in order |
|---|---|
| Screenshot | **Take Screenshot** → **Get Contents of URL** at `https://entity.livinginacat.world/api/bridge/screenshot`, method **POST**, request body **File**, using the screenshot output. |
| Clipboard | **Get Contents of URL** at `https://entity.livinginacat.world/api/bridge/clipboard`, method **GET** → **Copy to Clipboard** using the URL action’s output. |


## Medir el recorrido / Measure travel

**Español.** Con el brazo calibrado, abrí [Recorrido de Alfonsito](https://entity.livinginacat.world/entity/travel?lang=es) en la Mac. Mirá la máquina desde el frente. Con la punta levantada, acercate a cada esquina con las flechas, de 1 mm en 1 mm junto al borde. Dejá 2–3 mm antes del tope y comprobá en la cámara que el carro despejó el vidrio. Pulsá el nombre de esa esquina para leer y guardar la posición real de la MKS. Tras marcar las cuatro, **Usar estas esquinas** activa el área medida y el estacionamiento en la esquina más próxima. Una nueva calibración del brazo requiere volver a medir el recorrido.

**English.** After calibrating the arm, open [Alfonsito travel](https://entity.livinginacat.world/entity/travel?lang=en) on the Mac. Face the front of the machine. With the tip raised, jog to each corner, using 1 mm steps near the edge. Leave 2–3 mm before the stop and check the live camera to confirm that the carriage clears the glass. Press the corner name to capture the MKS work position. After recording all four, **Use these corners** enables the measured area and nearest-corner parking. Measure it again after a new arm calibration.
