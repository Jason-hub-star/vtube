
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
  const grab = () => page.evaluate((bands) => {
    const out = { __snapshot: window.__miniSnapshot() };
    for (const [name, r] of Object.entries(bands)) {
      out[name] = window.__miniProbe.regionPixelsBase64(r[0], r[1], r[2], r[3]);
    }
    return out;
  }, config.bands);
  const result = { backend: await page.evaluate(() => window.__miniBackend?.() || 'canvas') };
  await page.evaluate((n) => {
    window.__miniResetPhysics();
    for (let i = 0; i < n; i += 1) window.__miniStepPhysics(1 / 30);
  }, config.settle_steps);
  result.neutral = await grab();
  await page.evaluate((n) => {
    window.__miniProbe.setParameterValues({ ParamBodyTrackX: 1 });
    for (let i = 0; i < n; i += 1) window.__miniStepPhysics(1 / 30);
  }, config.settle_steps);
  result.displaced = await grab();
  await browser.close();
  fs.writeFileSync(config.out, JSON.stringify(result));
})();
