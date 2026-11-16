// Raster companions for the print PDF; renders the exact published SVGs.
// PLAYWRIGHT_MODULE can point at the bundled runtime's playwright/index.mjs.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({headless:true,channel:'chrome'});
try {
  const page = await browser.newPage({viewport:{width:1200,height:1000},deviceScaleFactor:1.5});
  const dir = path.join(root,'public/assets/assembly');
  for (const file of (await fs.readdir(dir)).filter(x=>/^(paso|inicio)-.*\.svg$/.test(x)).sort()) {
    await page.goto(pathToFileURL(path.join(dir,file)).href);
    await page.evaluate(()=>document.fonts.ready);
    await page.locator('svg').screenshot({path:path.join(dir,file.replace('.svg','.png'))});
  }
} finally {await browser.close();}
