
const fs = require('fs');
const config = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const { chromium } = require(config.pw);
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
  await page.goto(config.url, { waitUntil: 'load', timeout: 30000 });
  await page.waitForFunction(() => window.__miniProbe, null, { timeout: 20000 });
  await page.evaluate(() => window.__miniProbe.waitReady(20000));
  await page.evaluate(() => window.__miniClearSelection());
  const out = { backend: await page.evaluate(() => window.__miniBackend?.() || 'canvas'), captures: [] };
  for (const v of config.values) {
    await page.evaluate((v) => window.__miniSetParameters({ ParamEyeLOpen: v, ParamEyeROpen: v }), v);
    for (const [side, region] of Object.entries(config.regions)) {
      const b64 = await page.evaluate((r) => window.__miniProbe.regionPixelsBase64(r[0], r[1], r[2], r[3]), region);
      out.captures.push({ v, side, region, b64 });
    }
  }
  await browser.close();
  fs.writeFileSync(config.out, JSON.stringify(out));
})();
