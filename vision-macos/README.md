# Cat Vision · vista de pantalla

App de macOS para mostrar la pantalla de un iPhone vista por una cámara web. Detecta el contorno, lo recorta y corrige la perspectiva para presentar la pantalla en posición vertical. La cámara funciona localmente; no se envían ni guardan imágenes.

## Usar

1. Conecta la webcam y coloca el iPhone encendido frente a ella, procurando que se vean las cuatro esquinas y evitando reflejos.
2. Abre `vision-macos/build/Cat Vision.app` y acepta el permiso de cámara de macOS. La app prefiere una webcam externa; el panel permite escoger otra.
3. La detección de las esquinas se hace una vez. El encuadre y la orientación se guardan localmente para esa cámara y resolución y se reutilizan al volver a abrir la app. Para ajustarlo manualmente, pulsa **Marcar 4 esquinas** y haz clic en cada esquina en el orden indicado. Puedes deshacer el último punto o cancelar para conservar el encuadre anterior. Si cambias la posición de la cámara o el teléfono, vuelve a marcar las esquinas.
4. La detección coloca la pantalla en vertical. Si el iPhone está invertido o deseas otra orientación, usa **Girar**.
5. El panel permite ajustar **Enfoque** y **Brillo** en webcams UVC compatibles. Al mover el enfoque se desactiva el enfoque automático; pulsa **Auto** para recuperarlo. Los controles no compatibles se desactivan.

Con una Logitech C922 compatible, la app intenta apagar su luz y permite volver a enviar el comando. La respuesta del control no garantiza que la luz física esté apagada: compruébala visualmente. La app intenta recuperar el modo anterior al cerrar o cambiar de cámara. Un punto naranja indica que la cámara está activa. Tras una interrupción inesperada, podría ser necesario desconectar y reconectar la cámara para restablecer su luz. Otras cámaras conservan su comportamiento habitual. El control de la C922 sigue la [documentación del control de su LED](https://github.com/solareonk/logitech-c922-led-windows).

Un clic sobre la pantalla coloca un cursor virtual. Los cuatro botones de flechas o las teclas 1–4 apuntan a las esquinas; la barra espaciadora inicia o detiene el recorrido. El cuadro **Elementos detectados** enumera el texto reconocido. Cuando detecta filas alineadas de nombres, estima la posición del icono encima del texto y marca el elemento como **Icono**; al seleccionarlo, el cursor apunta al centro estimado del icono y muestra un clic simulado. Para otros textos apunta al texto. Los recuadros muestran el destino y se pueden ocultar. El reconocimiento es visual y aproximado: puede equivocarse, un texto no siempre corresponde a un botón y los iconos sin texto pueden no detectarse. No se envían acciones al teléfono ni a motores.

Requiere macOS 14 o posterior. Compilar desde la raíz con `vision-macos/scripts/build.sh`; requiere las herramientas de línea de comandos de Apple. La detección visual, la orientación inicial y la compatibilidad de foco pueden variar según el teléfono, iluminación y webcam. Un rectángulo detectado no demuestra calibración mecánica ni precisión de movimiento.

## Pruebas

```sh
swiftc -swift-version 5 -parse-as-library vision-macos/Sources/Geometry.swift vision-macos/Tests/GeometryTests.swift -o /tmp/cat-vision-geometry-test && /tmp/cat-vision-geometry-test
swiftc -target "$(uname -m)-apple-macosx14.0" -sdk "$(xcrun --show-sdk-path)" -swift-version 5 -parse-as-library vision-macos/Sources/Geometry.swift vision-macos/Sources/CameraModel.swift vision-macos/Tests/PerspectiveTests.swift -framework Vision -framework AVFoundation -framework AppKit -framework CoreImage -o /tmp/cat-perspective-test && /tmp/cat-perspective-test
swiftc -target "$(uname -m)-apple-macosx14.0" -sdk "$(xcrun --show-sdk-path)" -swift-version 5 -parse-as-library vision-macos/Sources/Geometry.swift vision-macos/Sources/CameraModel.swift vision-macos/Tests/ElementTests.swift -framework Vision -framework AVFoundation -framework AppKit -framework CoreImage -o /tmp/cat-elements-test && /tmp/cat-elements-test
```

El acceso a los controles UVC usa [uvc-util](https://github.com/jtfrey/uvc-util), revisión `8110da7025c95eea3096a7181af9a46c0cc7ac37`, bajo licencia MIT. Su licencia se conserva en `vendor/uvc-util/LICENSE` y en la aplicación compilada.
