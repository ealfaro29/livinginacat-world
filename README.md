# living in a cat world

FT412 is an open hardware robot that physically operates an iPhone. [Meet Alfonsito, the working V1 prototype](https://livinginacat.world/v1/), or [inspect the V2 console in 3D](https://livinginacat.world/v2/). [Leer en español](https://livinginacat.world/es/).

## Design and assembly

- [V1 project guide](docs/PROJECT.md) and [illustrated assembly manual](docs/ASSEMBLY-ES.md).
- [Original print files](hardware/ft412/PUBLIC-RELEASE.md), [revised cradle](hardware/ft412-cradle-rev01/README.md) and [revised tip coupler](hardware/ft412-coupler-rev01/README.md).
- The V1 parts list, quantities and whole-build estimate are maintained in `data/v1-catalog.json`. Each language has a searchable list and a downloadable CSV.
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

Open `http://127.0.0.1:4173`. `scripts/build.mjs` generates the public editions from an explicit list of sources. `scripts/guides.mjs` renders the technical manuals. The [backend](backend/README.md) maintains a separate authenticated workspace.

## Publish

Commit the source and push to `main`. From a clean checkout, run `npm run publish`. The script tests and builds the site, checks links and privacy, and pushes the generated files to `gh-pages`. Verify the deployment on [the custom domain](https://livinginacat.world/).
