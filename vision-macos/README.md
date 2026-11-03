# Cat Vision · prototipo de observación

Una primera app de macOS para observar un iPhone con una cámara web y mover un cursor **virtual** sobre la imagen. No se conecta a motores, no toca el teléfono y no envía capturas ni texto a ningún servidor.

## Empezar

1. Conecta una cámara web a la Mac y coloca el iPhone con la pantalla encendida frente a ella. Busca una vista lo más perpendicular posible y evita reflejos.
2. Abre `vision-macos/build/Cat Vision.app`. Si aún no existe, compílala desde la raíz del proyecto con `vision-macos/scripts/build.sh`.
3. Selecciona la cámara, pulsa **Iniciar cámara** y permite el acceso cuando macOS lo solicite.
4. Comprueba que el rectángulo verde siga los bordes de la pantalla útil. Si no coincide, pulsa **Marcar 4 esquinas** y haz clic en la pantalla en este orden: superior izquierda, superior derecha, inferior derecha e inferior izquierda. Repite la calibración si el teléfono o la cámara se mueven.
5. Pulsa una esquina, **Recorrer esquinas**, un texto reconocido o cualquier punto dentro de la pantalla del video. El cursor naranja se moverá en la vista previa; no interactúa con el iPhone.

El texto se reconoce en la imagen de la cámara mediante Apple Vision. Sus resultados son candidatos visuales, no una identificación semántica garantizada de botones: algunos textos no son controles, y los botones sin texto, los iconos, reflejos o letras pequeñas pueden no detectarse. La detección automática puede confundirse con otros rectángulos. La calibración manual es fija hasta reiniciarla.

El programa usa AVFoundation y Vision localmente en la Mac. No se guardan imágenes ni registros de lo observado. Requiere macOS 14 o posterior, una cámara compatible y las herramientas de línea de comandos de Apple para compilar. Esta prueba no calibra coordenadas físicas del robot ni establece precisión o seguridad de movimientos mecánicos.

## Pruebas de desarrollo

```sh
swiftc -swift-version 5 -parse-as-library vision-macos/Sources/Geometry.swift vision-macos/Tests/GeometryTests.swift -o /tmp/cat-vision-geometry-test
/tmp/cat-vision-geometry-test
swiftc -target "$(uname -m)-apple-macosx14.0" -sdk "$(xcrun --show-sdk-path)" -swift-version 5 -parse-as-library vision-macos/Tests/VisionSmoke.swift -framework Vision -framework AppKit -o /tmp/cat-vision-smoke
/tmp/cat-vision-smoke
```
