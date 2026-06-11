
const fs = require('fs');
const config = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const { chromium } = require(config.playwright_module);

(async () => {
  const browser = await chromium.launch({ headless: true });
  const result = { t3a: null, t3b: null, errors: [] };
  try {
    // ---- T3-a: 합성 주입 (mini app 직접) ----
    const page = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
    await page.goto(config.base_url + '/', { waitUntil: 'load', timeout: 30000 });
    await page.waitForFunction(() => window.__miniProbe, null, { timeout: 20000 });
    const ready = await page.evaluate(() => window.__miniProbe.waitReady(20000));
    const params = await page.evaluate(() => window.__miniProbe.parameters());
    const neutralHash = await page.evaluate(() => window.__miniProbe.canvasHash());
    await page.screenshot({ path: config.captures_dir + '/t3a_neutral.png' });
    const rows = [];
    for (const sample of config.samples) {
      const applied = await page.evaluate((values) => window.__miniProbe.setParameterValues(values), sample.outputs);
      await page.waitForTimeout(120);
      const hash = await page.evaluate(() => window.__miniProbe.canvasHash());
      const snapshot = await page.evaluate(() => window.__miniProbe.snapshot().parameters);
      rows.push({ label: sample.label, applied: applied.applied, missing: applied.missing, canvas_hash: hash, parameters: snapshot });
      await page.screenshot({ path: config.captures_dir + '/t3a_' + sample.label + '.png' });
      // 다음 샘플 측정의 독립성을 위해 중립 복귀
      await page.evaluate((values) => window.__miniProbe.setParameterValues(values), config.samples[0].outputs);
      await page.waitForTimeout(60);
    }
    result.t3a = { ready, parameter_count: params.length, parameters: params, neutral_hash: neutralHash, rows };
    await page.close();

    // ---- T3-b: 저장된 T1 스트림 재생 (/drive) ----
    const drive = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
    await drive.goto(config.base_url + '/drive?replay=1&auto=1&speed=' + config.replay_speed, { waitUntil: 'load', timeout: 30000 });
    await drive.waitForFunction(() => window.__driveReport && window.__driveReport.frames_applied > 0, null, { timeout: 40000 });
    await drive.screenshot({ path: config.captures_dir + '/t3b_early.png' });
    await drive.waitForFunction(() => window.__driveReport.frames_applied > 60, null, { timeout: 60000 });
    await drive.screenshot({ path: config.captures_dir + '/t3b_mid.png' });
    await drive.waitForFunction(() => window.__driveReport.done === true, null, { timeout: 120000 });
    await drive.screenshot({ path: config.captures_dir + '/t3b_done.png' });
    result.t3b = await drive.evaluate(() => ({
      mode: window.__driveReport.mode,
      frames_applied: window.__driveReport.frames_applied,
      applied_counts: window.__driveReport.applied_counts,
      missing_union: window.__driveReport.missing_union,
      done: window.__driveReport.done,
    }));
    await drive.close();
  } catch (error) {
    result.errors.push(String(error));
  } finally {
    await browser.close();
  }
  fs.writeFileSync(config.raw_out, JSON.stringify(result, null, 2));
})();
