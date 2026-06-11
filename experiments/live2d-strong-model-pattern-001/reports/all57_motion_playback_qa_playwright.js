
const fs = require('fs');
const path = require('path');
const { chromium } = require("/Users/family/jason/Vtube/experiments/live2d-strong-model-pattern-001/probe_sandbox/strong20/Samples/TypeScript/Demo/node_modules/playwright");

const manifest = JSON.parse(fs.readFileSync("/Users/family/jason/Vtube/experiments/live2d-strong-model-pattern-001/reports/all57_render_manifest.json", 'utf8'));
const runtimeIndex = {"chitose_chitose_t01": 0, "epsilon_epsilon_t02": 1, "haru_greeter_pro_jp_haru_greeter_t05": 2, "haru_haru_t01": 3, "kei_ko_kei_basic_free_t02": 4, "kei_ko_kei_vowels_pro_t02": 5, "koharu_haruto_haruto_t01": 6, "koharu_haruto_koharu_t01": 7, "mao_pro_ko_mao_pro_t06": 8, "miara_pro_en_miara_pro_t04": 9, "natori_pro_ko_natori_pro_t06": 10, "ren_pro_ko_ren_t01": 11, "rice_pro_ko_rice_pro_t03": 12, "shizuku_shizuku_t02": 13, "tsumiki_tsumiki_t01": 14, "unitychan_unitychan_t01": 15, "wanko_wanko_touch_t01": 16, "hiyori_pro_ko_hiyori_pro_t11": 17, "miku_pro_jp_miku_sample_t05": 18, "tororo_hijiki_hijiki_t01": 19, "tororo_hijiki_tororo_t01": 20, "nito_nito_t01": 21, "nito_ni_j_model3_runtime": 22, "nito_nico_model3_runtime": 23, "nito_nietzsche_model3_runtime": 24, "nito_nipsilon_model3_runtime": 25, "izumi_izumi_anime_t01": 26, "izumi_izumi_atsu_t01": 27, "izumi_izumi_illust_t01": 28, "izumi_izumi_suisai_t01": 29, "gantzert_felixander_gantzert_felixander_t01": 30, "github_live2d_cubism_web_samples_samples_resources_haru_haru_model3": 31, "github_live2d_cubism_web_samples_samples_resources_hiyori_hiyori_model3": 32, "github_live2d_cubism_web_samples_samples_resources_mao_mao_model3": 33, "github_live2d_cubism_web_samples_samples_resources_mark_mark_model3": 34, "github_live2d_cubism_web_samples_samples_resources_natori_natori_model3": 35, "github_live2d_cubism_web_samples_samples_resources_ren_ren_model3": 36, "github_live2d_cubism_web_samples_samples_resources_rice_rice_model3": 37, "github_live2d_cubism_web_samples_samples_resources_wanko_wanko_model3": 38, "github_live2d_cubism_native_samples_samples_resources_haru_haru_model3": 39, "github_live2d_cubism_native_samples_samples_resources_hiyori_hiyori_model3": 40, "github_live2d_cubism_native_samples_samples_resources_mao_mao_model3": 41, "github_live2d_cubism_native_samples_samples_resources_mark_mark_model3": 42, "github_live2d_cubism_native_samples_samples_resources_natori_natori_model3": 43, "github_live2d_cubism_native_samples_samples_resources_ren_ren_model3": 44, "github_live2d_cubism_native_samples_samples_resources_rice_rice_model3": 45, "github_live2d_cubism_native_samples_samples_resources_wanko_wanko_model3": 46, "github_live2d_cubism_web_motionsync_samples_resources_kei_basic_kei_basic_model3": 47, "github_live2d_cubism_web_motionsync_samples_resources_kei_vowels_kei_vowels_model3": 48, "github_live2d_garage_cubism_web_ar_sample_assets_models_rice_rice_model3": 49};
const outDir = "/Users/family/jason/Vtube/experiments/live2d-strong-model-pattern-001";
const baseUrl = "http://127.0.0.1:5130/";
const limit = 0;

async function waitProbe(page) {
  await page.waitForFunction(() => window.__vtubeProbe, null, { timeout: 30000 });
}

async function waitReady(page) {
  const ready = await page.evaluate(() => window.__vtubeProbe.waitReady(20000));
  if (!ready) throw new Error('probe model did not become ready');
}

async function screenshot(page, filePath) {
  await page.screenshot({ path: filePath, fullPage: false });
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await page.goto(baseUrl, { waitUntil: 'load', timeout: 45000 });
  await waitProbe(page);

  const models = limit > 0 ? manifest.models.slice(0, limit) : manifest.models;
  const report = { models: [] };
  const rawPath = path.join(outDir, 'reports', 'all57_motion_playback_qa_raw.json');

  for (const model of models) {
    const item = {
      rank: model.rank,
      id: model.id,
      safe_id: model.safe_id,
      name: model.name,
      manifest_status: model.manifest_status,
      runtime_index: runtimeIndex[model.safe_id],
      status: 'PENDING',
      motion_group: null,
      captures: {},
      errors: [],
    };

    if (model.manifest_status !== 'PASS' || item.runtime_index === undefined) {
      item.status = 'NO_RUNTIME';
      item.errors.push((model.missing_required_paths || []).join(',') || 'runtime model not present in sandbox');
      report.models.push(item);
      fs.writeFileSync(rawPath, JSON.stringify(report, null, 2));
      continue;
    }

    const modelDir = path.join(outDir, 'all57_motion_qa', model.safe_id);
    fs.mkdirSync(modelDir, { recursive: true });

    try {
      await page.evaluate((idx) => window.__vtubeProbe.switchModel(idx), item.runtime_index);
      await waitReady(page);
      await page.waitForTimeout(700);
      await page.evaluate(() => window.__vtubeProbe.clear());
      await page.waitForTimeout(350);
      const neutral = path.join(modelDir, 'neutral.png');
      await screenshot(page, neutral);
      item.captures.neutral = neutral;

      item.motion_group = await page.evaluate(() => window.__vtubeProbe.startRepresentativeMotion());
      for (const [label, waitMs] of [['motion_20', 450], ['motion_50', 900], ['motion_80', 1300]]) {
        await page.waitForTimeout(waitMs);
        const filePath = path.join(modelDir, `${label}.png`);
        await screenshot(page, filePath);
        item.captures[label] = filePath;
      }
      item.status = item.motion_group ? 'MOTION_CAPTURED' : 'NO_MOTION_GROUP';
    } catch (error) {
      item.status = 'FAIL_CAPTURE';
      item.errors.push(String(error));
    }
    report.models.push(item);
    fs.writeFileSync(rawPath, JSON.stringify(report, null, 2));
  }

  await browser.close();
  fs.writeFileSync(rawPath, JSON.stringify(report, null, 2));
})().catch(error => {
  console.error(error);
  process.exit(1);
});
