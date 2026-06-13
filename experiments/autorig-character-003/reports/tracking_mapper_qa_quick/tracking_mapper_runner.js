
const fs = require("fs");
const config = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const { chromium } = require(config.playwright);
(async () => {
  const browser = await chromium.launch({ headless: true, args: config.launch_args || [] });
  const page = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
  const out = { generated_at: new Date().toISOString(), renderer_requested: config.renderer, renderer_backend: null, report: null, samples: [], errors: [] };
  try {
    await page.goto(config.url, { waitUntil: "load", timeout: 30000 });
    await page.waitForFunction(() => window.__driveReport && window.__driveReport.frames_applied > 0, null, { timeout: 40000 });
    for (const sample of config.samples) {
      await page.waitForFunction((minFrames) => window.__driveReport.frames_applied >= minFrames || window.__driveReport.done, sample.min_frames, { timeout: sample.timeout_ms || 60000 });
      const path = `${config.captures_dir}/${sample.name}.png`;
      await page.screenshot({ path });
      out.samples.push(await page.evaluate((payload) => ({
        name: payload.name,
        screenshot: payload.path,
        drive_report: { ...window.__driveReport },
        canvas_hash: document.querySelector("#model")?.contentWindow?.__miniProbe?.canvasHash?.() ?? null,
        backend: document.querySelector("#model")?.contentWindow?.__miniBackend?.() ?? null,
      }), { name: sample.name, path }));
    }
    await page.waitForFunction(() => window.__driveReport.done === true, null, { timeout: config.done_timeout_ms || 120000 });
    out.report = await page.evaluate(() => ({ ...window.__driveReport }));
    out.renderer_backend = await page.evaluate(() => document.querySelector("#model")?.contentWindow?.__miniBackend?.() ?? null);
  } catch (error) {
    out.errors.push(String(error && error.stack ? error.stack : error));
  } finally {
    await browser.close();
    fs.writeFileSync(config.out, JSON.stringify(out, null, 2));
  }
})();
