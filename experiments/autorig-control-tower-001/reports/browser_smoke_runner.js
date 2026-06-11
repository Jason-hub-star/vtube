
const fs = require('fs');
const config = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const { chromium } = require(config.playwright_module);

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1380, height: 1000 } });
  const out = { checks: [], errors: [] };
  const check = (name, ok, detail = '') => out.checks.push({ name, ok: !!ok, detail: String(detail) });
  try {
    await page.goto(config.base_url, { waitUntil: 'load', timeout: 20000 });
    await page.waitForSelector('.run-select', { timeout: 30000 });
    await page.waitForFunction((id) => [...document.querySelectorAll('.run-select option')].some((o) => o.value === id), config.run_id, { timeout: 30000 });
    await page.selectOption('.run-select', config.run_id); // 명시 선택(pinned) — 다른 런으로 전환 방지
    await page.waitForFunction((id) => window.__towerState?.runState?.run_id === id, config.run_id, { timeout: 30000 });

    // 1. 타임라인 칩 10개 (P0~P6 + H1/H1.5/H2)
    await page.waitForSelector('.stage-chip', { timeout: 10000 });
    const chipCount = await page.locator('.stage-chip').count();
    check('타임라인 칩 10개', chipCount === 10, chipCount);
    await page.screenshot({ path: config.captures_dir + '/01_timeline.png' });

    // 2. 아티팩트 피드 표시 (P1 산출물)
    await page.waitForFunction(() => (window.__towerState?.runState?.artifacts || []).length >= 1, null, { timeout: 60000 });
    const feedBefore = await page.evaluate(() => window.__towerState.runState.artifacts.length);
    await page.waitForSelector('.feed-item img', { timeout: 15000 });
    const imgVisible = await page.locator('.feed-item img').first().isVisible();
    check('피드 썸네일 표시', imgVisible, 'count=' + feedBefore);
    await page.screenshot({ path: config.captures_dir + '/02_feed.png' });

    // 3. H1 게이트 배너 → 승인
    await page.waitForSelector('.gate-card', { timeout: 90000 });
    const gateTitle = await page.locator('.gate-card h3').first().textContent();
    check('게이트 배너 출현', !!gateTitle, gateTitle);
    await page.screenshot({ path: config.captures_dir + '/03_gate_h1.png' });
    await page.locator('.gate-card .btn', { hasText: '좋아요' }).first().click();
    await page.waitForFunction(() => !document.querySelector('.gate-card .btn'), null, { timeout: 15000 }).catch(() => {});

    // 4. H1 승인 후 P2 아티팩트로 피드가 실시간 증가하는지
    await page.waitForFunction((n) => window.__towerState.runState.artifacts.length > n, feedBefore, { timeout: 90000 });
    const feedAfter = await page.evaluate(() => window.__towerState.runState.artifacts.length);
    check('피드 실시간 증가', feedAfter > feedBefore, feedBefore + ' -> ' + feedAfter);

    // 4. H1.5 배치 게이트: 마커 드래그 → 저장
    await page.waitForFunction(() => {
      const gates = window.__towerState?.runState?.gates || {};
      return gates['H1_5']?.status === 'WAITING';
    }, null, { timeout: 90000 });
    await page.waitForSelector('.gate-editor canvas', { timeout: 10000 });
    const canvas = page.locator('.gate-editor canvas');
    await canvas.scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);
    const box = await canvas.boundingBox();
    // eye_L_open 마커: 2048 공간 [880,687] → 캔버스 좌표
    const sx = box.x + (880 / 2048) * box.width;
    const sy = box.y + (687 / 2048) * box.height;
    await page.mouse.move(sx, sy);
    await page.mouse.down();
    await page.mouse.move(sx + 40, sy + 25, { steps: 8 });
    await page.mouse.up();
    const draft = await page.evaluate(() => window.__towerState.gateDrafts['H1_5']);
    check('마커 드래그로 오버라이드 생성', !!draft?.eye_L_open?.target_anchor, JSON.stringify(draft || {}));
    await page.screenshot({ path: config.captures_dir + '/04_gate_drag.png' });
    await page.locator('.gate-card .btn', { hasText: '이대로 진행할게요' }).click();
    await page.waitForTimeout(2000);

    // 5. 패널 드래그 재배치 (QA 패널을 맨 위로) — HTML5 DnD 시뮬레이션
    await page.evaluate(() => {
      const order = JSON.parse(localStorage.getItem('ct_panel_order_v1') || 'null') || ['timeline', 'gate', 'feed', 'qa', 'log'];
      const next = ['qa', ...order.filter((k) => k !== 'qa')];
      localStorage.setItem('ct_panel_order_v1', JSON.stringify(next));
    });
    await page.reload({ waitUntil: 'load' });
    await page.waitForSelector('.panel', { timeout: 15000 });
    const firstPanel = await page.locator('.panel').first().getAttribute('data-panel');
    check('패널 순서 localStorage 유지', firstPanel === 'qa', firstPanel);

    // 6. H2 처리 후 런 완주
    await page.waitForSelector('.gate-card', { timeout: 120000 });
    await page.locator('.gate-card .btn', { hasText: '좋아요' }).first().click();
    await page.waitForFunction(() => window.__towerState?.runState?.status === 'PASS', null, { timeout: 60000 });
    check('브라우저에서 런 완주 확인', true);
    await page.screenshot({ path: config.captures_dir + '/05_done.png' });
  } catch (error) {
    out.errors.push(String(error));
    try { await page.screenshot({ path: config.captures_dir + '/99_error.png' }); } catch {}
  } finally {
    await browser.close();
  }
  fs.writeFileSync(config.raw_out, JSON.stringify(out, null, 2));
})();
