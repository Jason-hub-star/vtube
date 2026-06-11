
const fs = require('fs');
const path = require('path');
const { test } = require('@playwright/test');

const manifest = JSON.parse(fs.readFileSync("/Users/family/jason/Vtube/experiments/live2d-strong-model-pattern-001/reports/pilot_render_manifest.json", 'utf8'));
const outDir = "/Users/family/jason/Vtube/experiments/live2d-strong-model-pattern-001";
const baseUrl = "http://127.0.0.1:5077/?probe=pilot";
const categories = ['eye', 'mouth', 'hair', 'body_angle', 'arm'];

async function waitProbe(page) {
  await page.waitForFunction(() => window.__vtubeProbe, null, { timeout: 15000 });
}

async function waitReady(page) {
  const ready = await page.evaluate(() => window.__vtubeProbe.waitReady(15000));
  if (!ready) throw new Error('probe model did not become ready');
}

async function capture(page, filePath) {
  await page.screenshot({ path: filePath, fullPage: false });
}

test('capture Live2D probe evidence', async ({ page }) => {
  test.setTimeout(240000);
  const report = { models: [] };
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto(baseUrl, { waitUntil: 'load' });
  await waitProbe(page);
  const names = await page.evaluate(() => window.__vtubeProbe.modelNames());
  for (let index = 0; index < manifest.models.length; index++) {
    const model = manifest.models[index];
    const modelDir = path.join(outDir, 'captures', model.safe_id);
    fs.mkdirSync(modelDir, { recursive: true });
    const item = {
      id: model.id,
      safe_id: model.safe_id,
      name: model.name,
      expected_name: names[index],
      status: 'PASS',
      captures: {},
      categories: {},
      errors: [],
    };
    try {
      await page.evaluate((i) => window.__vtubeProbe.switchModel(i), index);
      await waitReady(page);
      await page.waitForTimeout(700);
      await page.evaluate(() => window.__vtubeProbe.clear());
      const neutral = path.join(modelDir, 'neutral.png');
      await capture(page, neutral);
      item.captures.neutral = neutral;

      const motionGroup = await page.evaluate(() => window.__vtubeProbe.startRepresentativeMotion());
      item.motion_group = motionGroup;
      for (const [label, delay] of [['20', 500], ['50', 1000], ['80', 1500]]) {
        await page.waitForTimeout(delay);
        const filePath = path.join(modelDir, `motion_${label}.png`);
        await capture(page, filePath);
        item.captures[`motion_${label}`] = filePath;
      }

      for (const category of categories) {
        const categoryFiles = [];
        for (const position of ['min', 'default', 'max']) {
          const matched = await page.evaluate(([c, p]) => window.__vtubeProbe.setCategory(c, p), [category, position]);
          item.categories[category] = item.categories[category] || { matched_parameters: matched };
          await page.waitForTimeout(350);
          const filePath = path.join(modelDir, `extreme_${category}_${position}.png`);
          await capture(page, filePath);
          categoryFiles.push(filePath);
        }
        item.captures[`extreme_${category}_frames`] = categoryFiles;
        await page.evaluate(() => window.__vtubeProbe.clear());
      }
    } catch (error) {
      item.status = 'FAIL';
      item.errors.push(String(error));
    }
    report.models.push(item);
  }
  fs.writeFileSync(path.join(outDir, 'reports', `${manifest.kind}_runtime_probe_playwright_raw.json`), JSON.stringify(report, null, 2));
});
