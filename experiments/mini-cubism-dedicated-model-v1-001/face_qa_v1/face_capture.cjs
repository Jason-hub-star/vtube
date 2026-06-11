
const fs = require("fs");
const path = require("path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");

const config = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));

async function metrics(page) {
  return await page.evaluate(() => {
    const canvas = document.querySelector("#preview-canvas");
    const ctx = canvas.getContext("2d");
    const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    let hash = 2166136261 >>> 0;
    let nonBackground = 0;
    for (let i = 0; i < data.length; i += 16) {
      hash ^= data[i];
      hash = Math.imul(hash, 16777619) >>> 0;
    }
    for (let i = 0; i < data.length; i += 4) {
      const isBackground = Math.abs(data[i] - 32) <= 2 && Math.abs(data[i + 1] - 33) <= 2 && Math.abs(data[i + 2] - 36) <= 2;
      if (!isBackground && data[i + 3] > 0) nonBackground += 1;
    }
    return { hash: hash.toString(16).padStart(8, "0"), nonBackground };
  });
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 980, height: 860 } });
  const results = [];
  try {
    await page.goto(config.url, { waitUntil: "networkidle" });
    await page.waitForSelector("#preview-canvas");
    for (const label of ["Mesh", "Deformers"]) {
      const button = page.getByRole("button", { name: label });
      if (await button.count()) await button.first().click();
    }
    for (const pose of config.poses) {
      await page.evaluate(() => window.__miniResetPhysics && window.__miniResetPhysics());
      await page.evaluate((values) => window.__miniSetParameters(values), pose.parameters);
      await page.waitForTimeout(60);
      const screenshot = path.join(config.framesDir, `${pose.name}.png`);
      await page.locator("#preview-canvas").screenshot({ path: screenshot });
      results.push({
        name: pose.name,
        parameters: pose.parameters,
        screenshot,
        metrics: await metrics(page),
        snapshot: await page.evaluate(() => window.__miniSnapshot()),
      });
    }
  } finally {
    await browser.close();
  }
  fs.writeFileSync(config.resultPath, JSON.stringify({ ok: true, results }, null, 2));
})().catch((error) => {
  fs.writeFileSync(config.resultPath, JSON.stringify({ ok: false, error: String(error.stack || error) }, null, 2));
  process.exit(1);
});
