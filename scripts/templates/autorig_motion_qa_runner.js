const fs = require("fs");
const config = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const { chromium } = require(config.playwright);

const slug = (text) => String(text).replace(/[^a-zA-Z0-9._-]/g, "_");
function decodeBase64(raw) {
  const bin = atob(raw);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i += 1) out[i] = bin.charCodeAt(i);
  return out;
}
async function sampleTiles(page) {
  return await page.evaluate((tiles) => {
    const out = [];
    for (const tile of tiles) {
      out.push({ tile, raw: window.__miniProbe.regionPixelsBase64(tile.x, tile.y, tile.w, tile.h) });
    }
    return out;
  }, config.tiles);
}
function tileDelta(a, b) {
  let total = 0, count = 0, changed = 0;
  for (let i = 0; i < a.length && i < b.length; i += 16) {
    const d = Math.abs(a[i] - b[i]) + Math.abs(a[i + 1] - b[i + 1]) + Math.abs(a[i + 2] - b[i + 2]) + Math.abs(a[i + 3] - b[i + 3]);
    total += d / 4;
    count += 1;
    if (d > 12) changed += 1;
  }
  return { mean_abs: count ? total / count : 0, changed_ratio: count ? changed / count : 0 };
}

(async () => {
  const out = { generated_at: new Date().toISOString(), renderer_requested: config.renderer, backend: null, frames: [], errors: [] };
  let browser = null;
  try {
    browser = await chromium.launch({ headless: true, args: config.launch_args || [] });
    const page = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
    await page.goto(config.url, { waitUntil: "load", timeout: 30000 });
    await page.waitForFunction(() => window.__miniProbe, null, { timeout: 20000 });
    await page.evaluate(() => window.__miniProbe.waitReady(20000));
    await page.evaluate(() => window.__miniClearSelection && window.__miniClearSelection());
    out.backend = await page.evaluate(() => window.__miniBackend ? window.__miniBackend() : "canvas");
    fs.mkdirSync(config.captures_dir, { recursive: true });
    await page.evaluate((defaults) => window.__miniSetParameters(defaults), config.defaults || {});
    const neutralHash = await page.evaluate(() => window.__miniProbe.canvasHash());
    const neutralTiles = (await sampleTiles(page)).map((item) => ({ tile: item.tile, bytes: decodeBase64(item.raw) }));
    const neutralCapture = `${config.captures_dir}/000_neutral.png`;
    await page.screenshot({ path: neutralCapture });
    out.frames.push({ name: "neutral", group: "neutral", parameters: {}, canvas_hash: neutralHash, screenshot: neutralCapture, pixel_delta_mean_abs: 0, changed_sample_ratio: 0 });
    for (const state of config.states) {
      const values = { ...(config.defaults || {}), ...(state.parameters || {}) };
      await page.evaluate((payload) => window.__miniSetParameters(payload), values);
      for (let i = 0; i < (state.physics_steps || 0); i += 1) await page.evaluate(() => window.__miniStepPhysics && window.__miniStepPhysics(1 / 30));
      await page.waitForTimeout(30);
      const hash = await page.evaluate(() => window.__miniProbe.canvasHash());
      const tiles = await sampleTiles(page);
      let mean = 0, ratio = 0;
      for (let i = 0; i < tiles.length; i += 1) {
        const d = tileDelta(neutralTiles[i].bytes, decodeBase64(tiles[i].raw));
        mean += d.mean_abs;
        ratio += d.changed_ratio;
      }
      const capture = `${config.captures_dir}/${String(out.frames.length).padStart(3, "0")}_${slug(state.name)}.png`;
      await page.screenshot({ path: capture });
      out.frames.push({ name: state.name, group: state.group, parameters: state.parameters || {}, canvas_hash: hash, screenshot: capture, pixel_delta_mean_abs: tiles.length ? mean / tiles.length : 0, changed_sample_ratio: tiles.length ? ratio / tiles.length : 0 });
    }
  } catch (error) {
    out.errors.push(String(error && error.stack ? error.stack : error));
  } finally {
    if (browser) await browser.close();
    fs.writeFileSync(config.out, JSON.stringify(out, null, 2));
  }
})();
