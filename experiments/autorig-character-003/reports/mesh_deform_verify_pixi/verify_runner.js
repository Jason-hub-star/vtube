
const fs = require('fs');
const config = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const { chromium } = require(config.pw);
(async () => {
  const browser = await chromium.launch({ headless: true, args: config.launch_args || [] });
  const page = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
  const out = { neutral: {}, hashes: {}, neck: {}, timing: {}, errors: [] };
  try {
    await page.goto(config.base + (config.query || ''), { waitUntil: 'load', timeout: 30000 });
    await page.waitForFunction(() => window.__miniProbe, null, { timeout: 20000 });
    await page.evaluate(() => window.__miniProbe.waitReady(20000));
    await page.evaluate(() => window.__miniClearSelection());
    out.backend = await page.evaluate(() => (window.__miniBackend ? window.__miniBackend() : 'canvas'));
    out.neutral.mesh = await page.evaluate(() => { window.__miniRig().render_mode='mesh'; window.__miniSetParameters({}); return window.__miniProbe.canvasHash(); });
    out.neutral.sprite = await page.evaluate(() => { window.__miniRig().render_mode='sprite'; window.__miniSetParameters({}); return window.__miniProbe.canvasHash(); });
    await page.evaluate(() => { window.__miniRig().render_mode='mesh'; window.__miniSetParameters({}); });
    const reset = { ParamAngleX:0, ParamAngleY:0, ParamAngleZ:0, ParamMouthOpenY:0, ParamEyeLOpen:1, ParamEyeROpen:1, ParamEyeBallX:0 };
    const states = { head_turn:{ParamAngleX:30}, nod:{ParamAngleY:-30}, tilt:{ParamAngleZ:30}, gaze_turn:{ParamAngleX:30,ParamEyeBallX:1}, combo:{ParamAngleX:25,ParamAngleY:-15,ParamMouthOpenY:0.6} };
    for (const [name, vals] of Object.entries(states)) {
      await page.evaluate((v) => window.__miniSetParameters(v), { ...reset, ...vals }); // 워밍업
      const t = await page.evaluate((v) => { const t0=performance.now(); window.__miniSetParameters(v); return performance.now()-t0; }, { ...reset, ...vals });
      out.timing[name] = Math.round(t*10)/10;
      out.hashes[name] = await page.evaluate(() => window.__miniProbe.canvasHash());
      await page.screenshot({ path: config.captures + '/verify_' + name + '.png' });
    }
    await page.evaluate((v) => window.__miniSetParameters(v), { ...reset, ParamAngleX: 30, ParamAngleY: 30 });
    out.neck.head_max = await page.evaluate(() => window.__miniProbe.regionAlphaCount(880, 980, 290, 130, 30));
  } catch (e) { out.errors.push(String(e)); }
  await browser.close();
  fs.writeFileSync(config.out, JSON.stringify(out, null, 2));
})();
