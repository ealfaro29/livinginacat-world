# living in a cat world

An open build journal about creating an AI that can perceive and act in the real world. The first project is a robot that physically uses an iPhone. Plans, decisions, purchases, shipments and hardware files are documented openly.

**Website:** https://livinginacat.world · **Initial stage:** CAD prepared; no physical assembly or testing. Purchases in progress, one store at a time.

## Contents

- `content/posts/`: English journal entries in Markdown with front matter.
- `data/ledger.json`: public quotes, orders, payments and shipments; integer USD cents.
- `data/hardware-release.json`: public CAD version and archive hash.
- `hardware/ft412/`: STL, STEP, coupons and CAD records; read the [release scope](hardware/ft412/PUBLIC-RELEASE.md) first.
- `docs/PROJECT.md`: architecture, planned assembly and acceptance tests.
- `public/`: original visuals, styles and CAD download.
- `scripts/`: static generator, checks and publication.
- `backend/`: authenticated, synchronized dispatch room; private PDFs and records stay outside Git.

## Read the guides

Project documentation is available as native site pages at [Documentation](https://livinginacat.world/documentation/), including the [project guide](https://livinginacat.world/documentation/project-guide/), [parts list](https://livinginacat.world/documentation/shopping-list/) and [hardware guide](https://livinginacat.world/documentation/hardware/). Each guide keeps its downloadable Markdown source. `scripts/guides.mjs` defines the catalogue, internal links and section navigation; the build reads the original Markdown files and generates the pages.

## Development

Node.js 22 or newer is required.

```sh
npm ci
npm test
npm run build
npm run check
npm run dev
```

Preview: `http://127.0.0.1:4173`. Public production files are generated in `dist/` and remain static, without cookies, analytics or API keys. The separate [private dispatch room](backend/README.md) uses authenticated cloud storage for orders, PDFs, prealerts and locker arrivals. The public ledger displays its review date; email reconciliation runs separately.

## Regenerate the CAD preview image

Optional: create a Python virtual environment, install `scripts/preview-requirements.txt`, then run `python scripts/render-hardware-preview.py`. This renders the published STL geometry only; it does not regenerate or validate the CAD models.

The shopping-list graphic is generated from the ledger with `node scripts/render-shopping-svg.mjs`. Export the SVG to PNG at exactly 1080×1440 and visually inspect it before publishing.

## Update and publish

1. Edit Markdown or JSON, keeping quoted, ordered, paid, shipped and delivered distinct.
2. Read `docs/DATA.md`, run tests, build and inspect in a browser on desktop and mobile.
3. Commit and push source to `main`.
4. Run `npm run publish`. It verifies, builds and publishes `dist/` to `gh-pages`, retaining that branch’s history. Git write access is required.
5. Wait for GitHub Pages deployment and verify the live pages and data.

Pages serves the root of `gh-pages`. The generator writes `CNAME` and `.nojekyll`. No additional workflow permission is needed. DNS uses the four GitHub Pages A records and a `www` CNAME to `ealfaro29.github.io`; preserve unrelated records. See [GitHub’s custom-domain documentation](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site).

## Transparency and limits

Original invoices, emails, addresses, real order IDs and full tracking numbers do not belong in this repository. Publish only verified, anonymized extracts. `null` means unknown, never zero. Expenses already included in an order are not counted twice. Order totals do not prove bank charges. Contributions and balance require reconciliation.

CAD publication does not certify physical compatibility, safety or performance. Complete robot software and regeneration scripts will be added as developed; this initial release does not present them as finished.

## License

MIT. Mechanics derived from PhysiClaw hardware v0.51 by Qiao Qian, under MIT. Original notice retained. See [attribution and scope](docs/ATTRIBUTION.md) and [contributing](CONTRIBUTING.md).

## Visual identity

The palette, typography and rough hardware-illustration style are defined in [docs/BRAND.md](docs/BRAND.md). Raw concept sketches and exact manufacturing CAD are separate artifacts.
