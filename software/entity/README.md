# Entity by Sentient

[Español](#español) · [English](#english)

## Español

[Continuar el proyecto en Codex](HANDOFF.md) · [Enviar o programar una tarea](https://entity.livinginacat.world/tareas?lang=es) · [Arquitectura y despliegue](guides/operaciones.md#español)

Entity controla un iPhone con el brazo FT412, una cámara y una Raspberry Pi. El panel muestra la tarea actual, la acción en curso y las siguientes tareas. El botón **EN / ES** cambia el idioma. Los títulos de tus tareas conservan el texto que escribiste.

- [Abrir la vista previa interactiva](src/physiclaw/static/entity/index.html?lang=es). También podés abrir el archivo `index.html` directamente en tu navegador. La demo incluye el arranque con el símbolo de Sentient, una tarea de calculadora y la cola.
- [Configurar un teléfono nuevo](guides/telefono.md#español). Incluye la página que se abre en el iPhone, la preparación de AssistiveTouch y la nueva calibración.
- [Pantalla MKS de 2,4 pulgadas](guides/pantalla.md#español). Estado de la integración de la TS24-R y del logo de arranque.
- [Grabar una ronda de Pulso](guides/pulso.md#español). El brazo busca cinco blancos con la cámara y el iPhone lleva el marcador.

**Uso.** Desde este directorio, `uv sync --locked` instala la versión local. `uv run --locked entity preview` abre la demo. En la Raspberry preparada para FT412, `entity mcp` inicia el servicio bajo demanda. El panel del operador está en `http://127.0.0.1:8048/entity/` y el asistente en `/setup-hardware`. El iPhone utiliza el puerto 8049.

**Tareas por MCP.** El cliente MCP llama a `entity_enqueue(title, request_id)` cuando recibe tu orden. `entity_start(task_id)` permite ejecutar las acciones de esa tarea. `entity_finish(task_id, outcome)` registra el resultado y deja la próxima en espera. `entity_status()` y abrir el panel solo leen el estado. Si el servicio se reinicia, conserva la cola y marca interrumpida la tarea que estaba activa.

## English

[Continue the project in Codex](HANDOFF.md) · [Submit or schedule a task](https://entity.livinginacat.world/tareas?lang=en) · [Architecture and deployment](guides/operaciones.md#english)

Entity operates an iPhone using the FT412 arm, a camera and a Raspberry Pi. Its panel shows the current task, the action in progress and upcoming tasks. Use **EN / ES** to change languages. Your task titles stay in the language you wrote them in.

- [Open the interactive preview](src/physiclaw/static/entity/index.html?lang=en). You can also open the local `index.html` directly in a browser. The demo includes the Sentient startup screen, a calculator task and the queue.
- [Set up a new phone](guides/telefono.md#english). This guide covers the iPhone page, AssistiveTouch shortcuts and a fresh calibration.
- [2.4-inch MKS display](guides/pantalla.md#english). Integration status of the TS24-R panel and startup logo.
- [Record a round of Pulse](guides/pulso.md#english). The arm finds five targets with its camera and the iPhone keeps score.

**Use.** Run `uv sync --locked` in this directory to install the local build. Run `uv run --locked entity preview` to open the demo. On the prepared FT412 Pi, `entity mcp` starts the on-demand service. The operator panel is at `http://127.0.0.1:8048/entity/`, with the setup wizard at `/setup-hardware`. The phone uses port 8049.

**MCP tasks.** The MCP client calls `entity_enqueue(title, request_id)` for an explicit operator request. `entity_start(task_id)` permits that task’s actions. `entity_finish(task_id, outcome)` records the result and leaves the next task waiting. Opening the panel or calling `entity_status()` only reads status. A service restart preserves the queue and marks the previously running task as interrupted.

## Origen / Upstream

PhysiClaw v0.11.5 · Qiao Qian · MIT. [Original source and documentation](https://github.com/physiclaw/PhysiClaw/tree/4e10ddf48774f408904a6a23715c24528d719eb5) · [License](LICENSE) · [Third-party notices](THIRD_PARTY_NOTICES.md).
