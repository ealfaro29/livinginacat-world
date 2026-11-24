# Continuar con Alfonsito y Entity · Continue working on Alfonsito and Entity

[Español](#español) · [English](#english)

## Español

Abrí **Living in a Cat World** en Codex. Este repositorio reúne el prototipo V1 **Alfonsito**, el diseño de una segunda máquina V2, el sitio público y el código de **Entity by Sentient** que corre en la Raspberry. La carpeta de software conserva el fork de PhysiClaw con su licencia e historial de atribución. El punto de partida de upstream es `4e10ddf48774f408904a6a23715c24528d719eb5`. Para desarrollar continuá sobre la versión de este repositorio. [Instrucciones del proyecto](../AGENTS.md) · [Código de Entity](../software/entity/) · [Atribuciones](ATTRIBUTION.md)

### Prompt para un chat nuevo

> Continuemos con Alfonsito y Entity by Sentient en el repositorio ealfaro29/livinginacat-world. Leé AGENTS.md y docs/CONTINUITY.md. Usá el MCP alfonsito y llamá primero a alfonsito_estado. Decime si la máquina está lista, qué tarea está ejecutando y qué hay en la cola. Esperá mi instrucción antes de enviar una tarea o mover el carro. Respondeme en español y mantené la interfaz y la documentación en español e inglés.

### Dónde trabajar

| Si querés… | Abrí… |
| --- | --- |
| Mandar instrucciones, programarlas o cambiar su prioridad | [Tareas y cola](https://entity.livinginacat.world/tareas?lang=es) · [Guía del operador](ENTITY.md#español) · [Adaptador MCP y configuración en otra computadora](../software/entity/remote/mcp/README.md#español) |
| Cambiar el comportamiento de Entity o del portal | [Mapa de código, pruebas y despliegue](../software/entity/guides/operaciones.md#español) · [Pi y túnel](../software/entity/remote/pi/) · [Worker y autenticación](../software/entity/remote/edge/) · [Interfaz web](../software/entity/remote/pages/site/ui/) |
| Calibrar o revisar un toque | [Teléfono y calibración](../software/entity/guides/telefono.md) · [Controles de cámara](https://entity.livinginacat.world/camara?lang=es) · [Recorrido](../software/entity/src/physiclaw/entity/travel.py) · [Juego Pulso](../software/entity/guides/pulso.md) |
| Cambiar la pantalla física de 320 × 240 | [Firmware, parche Makerbase, compilación y recuperación](../software/entity/firmware/entity-panel/) · [Pantallas y uso](../software/entity/guides/pantalla.md) |
| Revisar piezas de Alfonsito | [CAD original V1](../hardware/ft412/) · [Cuna revisada](../hardware/ft412-cradle-rev01/) · [Acoplador revisado](../hardware/ft412-coupler-rev01/) · [Placas Bambu y accesorios](../hardware/ft412-accessories/) · [Guía ilustrada](ASSEMBLY-ES.md) |
| Continuar con la V2 impresa | [Diseños CAD, fuentes y primeras placas](../hardware/ft412-v2/) · [Compras y alimentación](../data/v2-catalog.json) · [Visor](https://livinginacat.world/es/v2/#viewer) |
| Modificar y publicar el sitio | [Desarrollo y publicación](../README.md#development) · [Plantillas](../scripts/presentation.mjs) · [Guías](../scripts/guides.mjs) |

### Qué quedó comprobado

El 24 de noviembre de 2026, desde la web autenticada de producción se programaron dos tareas, se cambió su orden, se volvió a abrir la página y se retiraron ambas. La MKS y el portal leyeron la misma cola. Una tarea de texto enviada desde la web devolvió **72** para 8 × 9. El adaptador MCP también leyó el estado real, envió una tarea repetida con la misma clave conservando su ID, cambió prioridades y retiró las tareas de verificación. Estas pruebas se hicieron con el carro quieto. Consultá el estado actual en cada sesión. [Panel](https://entity.livinginacat.world/?lang=es)

Un cambio de posición de la cámara o del iPhone requiere revisar la calibración. En precisión se miden por separado los blancos reconocidos por la cámara y los toques que recibe el teléfono. Conservá el origen establecido y las cuatro esquinas de estacionamiento de cada máquina. Calibración, credenciales, base de datos de tareas y capturas reales se guardan en la instalación privada. Un clon nuevo dispone de código, ejemplos de servicios y herramientas de configuración. [Guía de operación y despliegue](../software/entity/guides/operaciones.md#español)

La **V2** tiene un ensamble STEP editable y dos piezas de fabricación de la primera tanda, frente y cama. El diseño fija 100 mm entre el vidrio y el lente por la medida física de Alfonsito. Para la V2 se deben comprobar el montaje real, los cables, la temperatura y la libertad de los patines en todo el recorrido. [Tanda de fabricación](../hardware/ft412-v2/Fabricacion/01-Frente-y-cama-R01/)

## English

Open **Living in a Cat World** in Codex. This repository contains the working Alfonsito V1, a separate V2 console design, the public website, and Entity by Sentient for the Raspberry Pi. The complete Entity fork carries its upstream licenses and starts from PhysiClaw commit `4e10ddf48774f408904a6a23715c24528d719eb5`. Continue development here. [Project instructions](../AGENTS.md) · [Entity source](../software/entity/)

### Prompt for a new chat

> Continue work on Alfonsito and Entity by Sentient in ealfaro29/livinginacat-world. Read AGENTS.md and docs/CONTINUITY.md. Use the alfonsito MCP server and call alfonsito_estado first. Tell me whether the machine is ready, what is running and which tasks are waiting. Wait for my instruction before submitting a task or moving the carriage. Reply in English and keep the interface and documentation in English and Spanish.

### Project map

| Work area | Entry points |
| --- | --- |
| Sending and scheduling work | [Tasks and queue](https://entity.livinginacat.world/tareas?lang=en) · [Operator guide](ENTITY.md#english) · [Codex MCP adapter and setup](../software/entity/remote/mcp/README.md#english) |
| Pi, web gateway and task execution | [Service map, verification and deployment](../software/entity/guides/operaciones.md#english) · [Cloud edge](../software/entity/remote/edge/) · [Web interface](../software/entity/remote/pages/site/ui/) |
| Phone, vision and physical controls | [Phone setup](../software/entity/guides/telefono.md#english) · [Camera settings](https://entity.livinginacat.world/camara?lang=en) · [Pulse](../software/entity/guides/pulso.md#english) · [Touchscreen firmware and recovery](../software/entity/firmware/entity-panel/) |
| Mechanical source | [V1 release](../hardware/ft412/) · [Alfonsito accessories and print plates](../hardware/ft412-accessories/) · [V2 editable models and print preparation](../hardware/ft412-v2/) |
| Website | [Templates](../scripts/presentation.mjs) · [Guide renderer](../scripts/guides.mjs) · [Build and publish](../README.md#development) |

On November 24, 2026 the production operator portal successfully added, scheduled, reordered and removed tasks. The MKS read the same order. A real, text-only agent task returned **72** for 8 × 9. The registered MCP adapter also read the live state, submitted a task twice with the same ID, reordered and removed its future test tasks. The carriage stayed still. Request live state at the start of a session. After moving the phone or camera, check calibration. The phone touch count and camera target count measure different things. Calibration, the task database, credentials and phone captures belong to the private installation. [Dashboard](https://entity.livinginacat.world/?lang=en)

The V2 assembly STEP and the printable front and phone bed are available. The 100 mm glass-to-lens height comes from a V1 measurement. Physical V2 fit, cable clearance, temperature and full carriage travel still need to be tested. [V2 manufacturing batch](../hardware/ft412-v2/Fabricacion/01-Frente-y-cama-R01/)

## Verificación local / Local verification

Sitio público desde la raíz. Public site from the repository root.

```sh
npm ci
npm test
npm run build
npm run check
```

Software desde una copia limpia. Software from a clean checkout.

```sh
cd software/entity
uv sync --locked --group dev
uv run --locked pytest -q tests/entity tests/core/server
node --test remote/edge/*.test.mjs remote/pages/*.test.mjs
```

El firmware se compila por separado con la revisión Makerbase documentada. La guía del MCP explica el transporte HTTPS que usa Codex para llegar al operador. The firmware builds separately against the documented Makerbase revision. The MCP guide explains how the adapter reaches the operator portal over HTTPS. [Firmware](../software/entity/firmware/entity-panel/README.md) · [MCP](../software/entity/remote/mcp/README.md)
