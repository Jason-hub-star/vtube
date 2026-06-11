
const fs = require('fs');
const config = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const { chromium } = require(config.pw);

const STATES = {
  neutral: {},
  head_turn: { ParamAngleX: 30 },
  nod: { ParamAngleY: -30 },
  tilt: { ParamAngleZ: 30 },
  gaze_turn: { ParamAngleX: 30, ParamEyeBallX: 1 },
  blink: { ParamEyeLOpen: 0.27, ParamEyeROpen: 0.27 },
  mouth: { ParamMouthOpenY: 0.85 },
  combo: { ParamAngleX: 25, ParamAngleY: -15, ParamAngleZ: 10, ParamMouthOpenY: 0.6, ParamBodyAngleX: 8 },
};
const RESET = { ParamAngleX:0, ParamAngleY:0, ParamAngleZ:0, ParamEyeBallX:0, ParamEyeLOpen:1, ParamEyeROpen:1, ParamMouthOpenY:0, ParamBodyAngleX:0 };

async function measureScale(browser, base, scale) {
  const page = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
  await page.goto(base + '/?render_scale=' + scale, { waitUntil: 'load', timeout: 30000 });
  await page.waitForFunction(() => window.__miniProbe, null, { timeout: 20000 });
  await page.evaluate(() => window.__miniProbe.waitReady(20000));
  await page.evaluate(() => window.__miniClearSelection());
  const result = {};
  for (const [name, vals] of Object.entries(STATES)) {
    const times = await page.evaluate(async ({ reset, vals }) => {
      const samples = [];
      for (let i = 0; i < 6; i += 1) {
        window.__miniSetParameters(reset);
        const t0 = performance.now();
        window.__miniSetParameters({ ...reset, ...vals });
        samples.push(performance.now() - t0);
        await new Promise((r) => setTimeout(r, 30));
      }
      samples.sort((a, b) => a - b);
      return samples;
    }, { reset: RESET, vals });
    result[name] = Math.round(times[Math.floor(times.length / 2)] * 10) / 10; // 중앙값
  }
  // 물리 스텝 비용 (드로우 포함)
  result.physics_step = await page.evaluate(async () => {
    window.__miniSetParameters({ ParamAngleX: 30 });
    const t0 = performance.now();
    for (let i = 0; i < 10; i += 1) window.__miniStepPhysics(1 / 30);
    return Math.round(((performance.now() - t0) / 10) * 10) / 10;
  });
  await page.close();
  return result;
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const out = { scales: {}, replay: {}, errors: [] };
  try {
    out.scales['1.0'] = await measureScale(browser, config.preview, 1);
    out.scales['0.55'] = await measureScale(browser, config.preview, 0.55);
    // 재생 실효 FPS (드라이브, 0.55 내장)
    const drive = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
    await drive.goto(config.drive + '/drive?replay=1&auto=1&speed=1', { waitUntil: 'load', timeout: 30000 });
    await drive.waitForFunction(() => window.__driveReport?.frames_applied > 0, null, { timeout: 60000 });
    const t0 = Date.now();
    await drive.waitForFunction(() => window.__driveReport.done === true, null, { timeout: 90000 });
    const wall = (Date.now() - t0) / 1000;
    const frames = await drive.evaluate(() => window.__driveReport.frames_applied);
    out.replay = { frames, wall_s: Math.round(wall * 100) / 100, effective_fps: Math.round(frames / Math.max(wall, 0.1)) };
    await drive.close();
  } catch (e) { out.errors.push(String(e)); }
  await browser.close();
  fs.writeFileSync(config.out, JSON.stringify(out, null, 2));
})();
