# Alfonsito MCP · Entity by Sentient

[Español](#español) · [English](#english)

## Español

El servidor `alfonsito` conecta Codex a la cola que se ve en el [panel web](https://entity.livinginacat.world/tareas?lang=es) y la MKS. Codex inicia el adaptador en tu computadora. El adaptador inicia sesión por HTTPS en el dominio fijo de Entity. Podés operar desde otra red. La Raspberry debe estar encendida y conectada a Internet.

### Habilitarlo en otra computadora

Necesitás Codex, `uv` y una copia del repositorio. Desde la raíz de Living in a Cat, guardá en privado el usuario y contraseña del panel y registrá la ruta absoluta del adaptador. En la Mac del proyecto el acceso y el registro ya están configurados.

```sh
uv run --script software/entity/remote/mcp/alfonsito.py --login
codex mcp add alfonsito -- "$(command -v uv)" run --script "$(pwd)/software/entity/remote/mcp/alfonsito.py"
codex mcp get alfonsito
```

Abrí un chat del proyecto y pedile que use `alfonsito_estado`. La contraseña se ingresa en la terminal y queda en `~/.config/entity/alfonsito-login.txt` con permisos de propietario. Para una instalación gestionada también podés proporcionar `ENTITY_OPERATOR_USER` y `ENTITY_OPERATOR_PASSWORD` al proceso del adaptador. [Configuración MCP de Codex](https://developers.openai.com/codex/mcp/)

| Herramienta | Qué hace |
| --- | --- |
| `alfonsito_estado` | Lee si el equipo está listo, la tarea activa, las pendientes y el último resultado. Consultarla deja el carro en su sitio. |
| `alfonsito_enviar` | Envía una instrucción para el próximo turno o para una fecha ISO con zona horaria. Conservá el mismo `solicitud_id` si reintentás. |
| `alfonsito_mover` | Sube o baja una tarea pendiente un lugar usando su ID y el de la vecina que se ven en la cola. |
| `alfonsito_eliminar` | Retira una tarea pendiente por su ID. |

Para comenzar, pedí «Consultá el estado de Alfonsito y decime si está listo». Una tarea física se envía cuando el operador la pide. `ready` indica que Entity reconoce el equipo y tiene una calibración de precisión válida. Una tarea aceptada tiene un identificador. El resultado aparece en `last` al terminar, hasta que concluye otra tarea.

## English

The `alfonsito` MCP server connects Codex to the operator queue used by the [web dashboard](https://entity.livinginacat.world/tareas?lang=en) and the physical MKS. Codex launches the adapter locally. The adapter authenticates over HTTPS on Entity’s fixed domain. The operator can be on another network. The Raspberry Pi needs power and internet access.

From the project root, use the three commands above to enter the operator login, register the adapter and inspect its configuration. The project Mac is already configured. Start a project chat and ask it to call `alfonsito_estado`. Credentials stay in `~/.config/entity/alfonsito-login.txt` with owner-only permissions. Managed setups can supply `ENTITY_OPERATOR_USER` and `ENTITY_OPERATOR_PASSWORD` to the adapter process. [Codex MCP configuration](https://developers.openai.com/codex/mcp/)

| Tool | Purpose |
| --- | --- |
| `alfonsito_estado` | Read readiness, the running task, waiting queue and last result without moving the stylus. |
| `alfonsito_enviar` | Submit one instruction for the next available turn or an ISO date with a time-zone offset. Reuse the same request ID on retries. |
| `alfonsito_mover` | Move a waiting task up or down one position using both adjacent IDs from the queue. |
| `alfonsito_eliminar` | Remove a waiting task by ID. |

Start with “Read Alfonsito’s status and tell me whether it is ready.” Physical work starts when the operator requests a task. `ready` covers equipment and saved precision calibration. Acceptance returns a task ID. The last completed task and its outcome remain under `last` until another task finishes.
