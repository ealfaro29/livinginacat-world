# living in a cat world

FT412 is an open hardware robot that physically operates an iPhone. [Meet Alfonsito, the working V1 prototype](https://livinginacat.world/v1/), or [inspect the V2 console in 3D](https://livinginacat.world/v2/). [Leer en español](https://livinginacat.world/es/).

## Continue the project · Continuar el proyecto

Open the [Codex handoff with a ready-to-copy prompt / Guía para retomar en Codex](docs/CONTINUITY.md). The public site, Alfonsito and V2 share this repository.

- [Entity by Sentient source and software guide / Código y operación](software/entity/HANDOFF.md).
- [Send tasks to Alfonsito / Enviar tareas](https://entity.livinginacat.world/tareas) and [connect Codex through MCP / conectar Codex](software/entity/remote/mcp/README.md).
- [V1 accessories, Bambu plates and camera frame / Accesorios y placas](hardware/ft412-accessories/).
- [V2 console designs, CAD generators and printable pieces / Diseños y piezas](hardware/ft412-v2/).

## Design and assembly

- [Use Alfonsito with Entity by Sentient · Guía pública de operación (ES/EN)](docs/ENTITY.md).
- [V1 project guide](docs/PROJECT.md) and [illustrated assembly manual](docs/ASSEMBLY-ES.md).
- [Original print files](hardware/ft412/PUBLIC-RELEASE.md), [revised cradle](hardware/ft412-cradle-rev01/README.md) and [revised tip coupler](hardware/ft412-coupler-rev01/README.md).
- The V1 parts list, quantities and whole-build estimate are maintained in `data/v1-catalog.json`. Each language has a searchable list and a downloadable CSV.
- The [V2 shopping list and landed estimate](https://livinginacat.world/v2/#budget), the interactive planner and both CSV downloads use `data/v2-catalog.json`. They cover a second complete machine, including its shared 12 V supply and the separate converters for the Pi and iPhone.
- The V2 viewer and STEP download live in `public/assets/v2/visor/`. Its source is in `tools/console-viewer/`.
- [Credits and licenses](docs/ATTRIBUTION.md).

## Development

Use Node.js 22 or newer.

```sh
npm ci
npm test
npm run build
npm run check
npm run dev
```

Open `http://127.0.0.1:4173`. `scripts/build.mjs` generates the public editions from an explicit list of sources. `scripts/guides.mjs` renders the technical manuals. For the same shopping planner in chat, `node scripts/shopping-planner.mjs es` or `en` writes the current fragment to standard output. The [backend](backend/README.md) maintains a separate authenticated workspace.

## Publish

Commit the source and push to `main`. From a clean checkout, run `npm run publish`. The script tests and builds the site, checks links and privacy, and pushes the generated files to `gh-pages`. Verify the deployment on [the custom domain](https://livinginacat.world/).
