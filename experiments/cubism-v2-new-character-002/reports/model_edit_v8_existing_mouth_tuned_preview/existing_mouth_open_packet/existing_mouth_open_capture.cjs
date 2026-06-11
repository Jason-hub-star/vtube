
const fs = require("fs");
const path = require("path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");

const config = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));

function hashData(data) {
  let hash = 2166136261 >>> 0;
  const step = 16;
  for (let i = 0; i < data.length; i += step) {
    hash ^= data[i];
    hash = Math.imul(hash, 16777619) >>> 0;
  }
  return hash.toString(16).padStart(8, "0");
}

async function canvasMetrics(page) {
  return await page.evaluate(() => {
    const canvas = document.querySelector("#preview-canvas");
    const ctx = canvas.getContext("2d");
    const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    return { width: canvas.width, height: canvas.height, hash: hashData(data) };

    function hashData(data) {
      let hash = 2166136261 >>> 0;
      const step = 16;
      for (let i = 0; i < data.length; i += step) {
        hash ^= data[i];
        hash = Math.imul(hash, 16777619) >>> 0;
      }
      return hash.toString(16).padStart(8, "0");
    }
  });
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1100, height: 900 } });
  const frames = [];
  try {
    await page.goto(config.url, { waitUntil: "networkidle" });
    await page.waitForSelector("#preview-canvas");
    await page.waitForFunction(() => Boolean(window.__miniSetParameters && window.__miniSnapshot));
    await page.evaluate(() => window.__miniClearSelection && window.__miniClearSelection());
    for (const frame of config.frames) {
      const values = {
        ParamAngleX: 0,
        ParamEyeLOpen: 1,
        ParamEyeROpen: 1,
        ParamMouthOpenY: frame.mouthOpen,
        ParamHairFront: 0,
      };
      await page.evaluate(() => window.__miniResetPhysics && window.__miniResetPhysics());
      await page.evaluate((parameters) => window.__miniSetParameters(parameters), values);
      await page.waitForTimeout(80);
      const screenshot = path.join(config.framesDir, `${frame.id}.png`);
      await page.locator("#preview-canvas").screenshot({ path: screenshot });
      frames.push({
        ...frame,
        parameters: values,
        screenshot,
        metrics: await canvasMetrics(page),
        snapshot: await page.evaluate(() => window.__miniSnapshot()),
      });
    }
  } finally {
    await browser.close();
  }
  fs.writeFileSync(config.resultPath, JSON.stringify({ ok: true, frames }, null, 2));
})().catch((error) => {
  fs.writeFileSync(config.resultPath, JSON.stringify({ ok: false, error: String(error.stack || error) }, null, 2));
  process.exit(1);
});
