import test from "node:test";
import assert from "node:assert/strict";
import {
  guides,
  resolveGuideLink,
  renderGuideMarkdown,
} from "../scripts/guides.mjs";

const context = {
  repo: "https://github.com/ealfaro29/livinginacat-world",
  siteUrl: "https://livinginacat.world",
};

test("Markdown references stay inside the site, including nested sources and download aliases", () => {
  const source = "hardware/ft412/README.md";
  assert.equal(
    resolveGuideLink("MOTOR-MOUNTS.md#interfaces", source, context),
    "/documentation/motor-mounts/#interfaces",
  );
  assert.equal(
    resolveGuideLink("../../docs/PROJECT.md#goal", source, context),
    "/documentation/project-guide/#goal",
  );
  assert.equal(
    resolveGuideLink(
      context.repo + "/blob/main/docs/BRAND.md",
      source,
      context,
    ),
    "/documentation/visual-identity/",
  );
  assert.equal(
    resolveGuideLink("/downloads/shopping-list.md", source, context),
    "/documentation/shopping-list/",
  );
  assert.equal(
    resolveGuideLink(context.siteUrl + "/purchases/", source, context),
    "/purchases/",
  );
});

test("Data files and external references retain their intended destinations", () => {
  assert.equal(
    resolveGuideLink(
      "qa/print-manifest.json",
      "hardware/ft412/README.md",
      context,
    ),
    context.repo + "/blob/main/hardware/ft412/qa/print-manifest.json",
  );
  assert.equal(
    resolveGuideLink(
      "https://www.adafruit.com/product/412",
      "docs/PROJECT.md",
      context,
    ),
    "https://www.adafruit.com/product/412",
  );
  assert.equal(
    resolveGuideLink("public/assets/printed-parts.png", "README.md", context),
    "/assets/printed-parts.png",
  );
});

test("Section navigation uses unique anchors and keeps heading text readable", () => {
  const guide = guides.find((g) => g.slug === "project-guide");
  const rendered = renderGuideMarkdown(
    "# Original title\n\n## Goal\n\nThe plan.\n\n### Fit & motion\n\n## Goal\n\nAnother stage.",
    guide,
    context,
  );
  assert.ok(!rendered.html.includes("<h1"));
  assert.deepEqual(
    rendered.headings.map((h) => [h.id, h.text]),
    [
      ["goal", "Goal"],
      ["fit-motion", "Fit & motion"],
      ["goal-2", "Goal"],
    ],
  );
  for (const heading of rendered.headings)
    assert.ok(rendered.html.includes('id="' + heading.id + '"'));
});

test("Hardware cross-references in inline code become guide links while tables and code remain intact", () => {
  const guide = guides.find((g) => g.slug === "hardware");
  const rendered = renderGuideMarkdown(
    "# Hardware\n\nRead `MOTOR-MOUNTS.md`.\n\n| Part | Qty |\n|---|---:|\n| Mount | 2 |\n\n```sh\nnpm run build\n```",
    guide,
    context,
  );
  assert.ok(rendered.html.includes('href="/documentation/motor-mounts/"'));
  assert.ok(rendered.html.includes("<table>"));
  assert.ok(rendered.html.includes("npm run build"));
});
