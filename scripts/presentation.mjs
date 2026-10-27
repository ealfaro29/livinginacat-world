import { esc, money, date } from "./lib.mjs";

export function articleCover(post, ledger) {
  if (post.number === 1)
    return `<figure class="entry-cover sketch-cover"><img src="/assets/prototype-rough-v1.png" alt="Rough ink and red-pencil concept of the iPhone robot" width="1536" height="1024" loading="lazy"><figcaption>CONCEPT SKETCH / NOT A COMPLETED BUILD</figcaption></figure>`;
  if (post.number === 3)
    return `<figure class="entry-cover sketch-cover"><img src="/assets/printed-parts.png" alt="CAD preview of parts planned for the robot" width="2400" height="2850" loading="lazy"><figcaption>OPEN CAD / PHYSICAL TESTS AHEAD</figcaption></figure>`;
  return `<div class="receipt-cover" aria-label="Illustrated order ledger"><span class="cover-kicker">FOLLOW THE PAPER TRAIL</span><div class="receipt-slip"><span class="receipt-title">ORDER RECORD</span>${ledger.amazonOrders.map((o) => `<div><span>${o.id}</span><b>${money(o.orderTotalCents)}</b></div>`).join("")}<div class="receipt-total"><span>AMAZON ORDERS</span><b>${money(ledger.amazonOrders.reduce((n, x) => n + x.orderTotalCents, 0))}</b></div><small>Order amounts. Bank payments not reconciled.</small></div><span class="rubber-stamp">OPEN BOOKS</span></div>`;
}

export function postCard(p, ledger) {
  return `<a class="post-card" href="/journal/${p.slug}/"><div class="post-visual">${articleCover(p, ledger)}<span class="post-index" aria-hidden="true">0${p.number}</span></div><div class="post-card-body"><div class="card-meta"><span>FIELD NOTE / ${String(p.number).padStart(2, "0")}</span><time datetime="${p.date}">${date(p.date)}</time></div><h3>${esc(p.title)}</h3><p>${esc(p.excerpt)}</p><span class="text-link">Read the field note <span aria-hidden="true">↗</span></span></div></a>`;
}

export function renderHome({ posts, ledger, finances, hardware }) {
  return `
<section class="workshop-hero wrap" aria-label="living in a cat world">
  <div class="hero-intro">
    <p class="eyebrow"><span class="red-dash"></span> AI IN THE PHYSICAL WORLD</p>
    <h1>living in the<br><em>real world<span class="red-period">.</span></em></h1>
    <p class="hero-deck">Building an AI that can live in the real world.<br>See, decide and act beyond the screen.</p>
    <a class="round-link" href="/journal/project-begins/"><span class="round-arrow">↗</span><span>Start with<br><b>the first project</b></span></a>
    <div class="hero-side-note"><span>01—</span><p>First step: a camera, a robot, an iPhone.<br>From seeing the screen to touching it.</p></div>
  </div>
  <div class="hero-workbench" id="prototype">
    <div class="workbench-top"><span>ON THE WORKBENCH</span><span>PROJECT / 001</span></div>
    <div class="paper-stack"><figure class="drawing-sheet">
      <div class="sheet-topline"><span>AI × IPHONE / CONCEPT STUDY</span><span>REV. ${hardware.version}</span></div>
      <div class="sketch-canvas">
        <img src="/assets/prototype-rough-v1.png" alt="Raw graphite and red-pencil sketch of a robot, with an iPhone in its frame and a stylus touching the screen" width="1536" height="1024" fetchpriority="high">
        <button class="sketch-pin active" style="--x:53%;--y:21%" data-sketch="eyes" aria-label="Camera: explore feature 1" aria-pressed="true" aria-controls="sketch-note"><span>01</span><b>See</b></button>
        <button class="sketch-pin" style="--x:81%;--y:48%" data-sketch="motion" aria-label="Motion: explore feature 2" aria-pressed="false" aria-controls="sketch-note"><span>02</span><b>Move</b></button>
        <button class="sketch-pin" style="--x:47%;--y:58%" data-sketch="touch" aria-label="iPhone and touch: explore feature 3" aria-pressed="false" aria-controls="sketch-note"><span>03</span><b>Touch</b></button>
      </div>
      <figcaption>CONCEPT ILLUSTRATION / NOT A COMPLETED MACHINE</figcaption>
    </figure></div>
    <div class="sketch-note" id="sketch-note" aria-live="polite"><b>01 / THE EYES</b><p>A camera observes the screen before and after each action. Its view must be calibrated to the real machine.</p></div>
    <span class="hand-note">a real phone. a real touch.</span>
  </div>
</section>
<div class="build-status wrap"><span class="status-heading"><span class="status-dot"></span> THE CURRENT STATE</span><span>CAD prepared</span><span>${ledger.purchasesPaused ? "Purchases paused" : "Purchases in progress"}</span><span>Physical tests ahead</span><a href="/documentation/">Open the project ↗</a></div>

<section class="wrap journal-section">
  <div class="section-heading"><div><p class="eyebrow">01 / FIELD NOTES</p><h2>The notebook<span class="red-period">.</span></h2></div><a class="text-link" href="/journal/">All entries ↗</a></div>
  <div class="post-grid">${[...posts]
    .sort((a, b) => a.number - b.number)
    .map((p) => postCard(p, ledger))
    .join("")}</div>
</section>

<section class="fabrication-section wrap">
  <div class="parts-contact-sheet"><div class="contact-top"><span>THE PRINT QUEUE</span><span>STL / STEP</span></div><img src="/assets/printed-parts.png" width="2400" height="2850" alt="Actual CAD preview showing the individual printable robot parts, not fabricated parts" loading="lazy"><span class="cad-stamp">CAD FILES<br><small>NOT PRINTED YET</small></span><p>${hardware.stlDesigns} designs + ${hardware.coupons} fit coupons / REV. ${hardware.version}</p></div>
  <div class="fabrication-copy"><p class="eyebrow">02 / FROM FILE TO WORKBENCH</p><h2>${hardware.installedPrintedParts} parts.<br><em>One first build.</em></h2><p>Print the mounts. Assemble the frame. Calibrate the camera. Then test tap accuracy and swipe reliability.</p><div class="build-sequence"><span><b>01</b> Print</span><i>↗</i><span><b>02</b> Assemble</span><i>↗</i><span><b>03</b> Test</span></div><a class="button" href="/downloads/${hardware.filename}" download>Get the open CAD files <span>↓</span></a><a class="under-link" href="/documentation/">Read the design, checks and limits ↗</a><p class="small-note">Geometry reviewed. Physical fit, touch and motion still need testing.</p></div>
</section>

<section class="ledger-section"><div class="wrap"><div class="section-heading"><div><p class="eyebrow">03 / THE OPEN BOOKS</p><h2>Here’s where<br><em>the money goes.</em></h2></div><div class="ledger-aside"><p>Parts, orders, receipts.<br>Nothing swept under the workbench.</p><a class="text-link" href="/purchases/">Explore the full ledger ↗</a></div></div>${finances}<div class="ledger-bottom"><p>Quotes ≠ orders ≠ verified payments.<br>The records keep those distinctions.</p><a class="text-link" href="/shipments/">Track the packages ↗</a></div></div></section>

<section class="wrap closing-note"><span class="hand-star" aria-hidden="true">✳</span><div><p class="eyebrow">THE OPEN BUILD JOURNAL</p><h2>The whole process,<br>in the open.</h2><p>Design decisions, purchases and test results, shared openly with everyone supporting the build. Progress and lessons learned, documented as the project develops.</p><a class="text-link" href="/documentation/#transparency">How this journal stays transparent ↗</a></div><span class="closing-number" aria-hidden="true">001</span></section>`;
}
