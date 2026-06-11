// 엔트리포인트.

import { defaultViewZoom, draw } from "./core/draw.js";
import { initPhysicsState, stepPhysics } from "./core/physics.js";
import { normalizeRig } from "./core/rig.js";
import { state } from "./core/state.js";
import { escapeHtml, fetchJson, loadImages } from "./core/utils.js";
import { exposeAutomationApi } from "./probe.js";
import { render } from "./ui/components.js";
import { app } from "./ui/dom.js";

async function init() {
  try {
    const project = await fetchJson("/api/project");
    state.project = project;
    const search = new URLSearchParams(location.search);
    state.renderScale = parseFloat(search.get("render_scale")) || 1; // 드라이브 성능용 저해상 렌더 (canvas 백엔드 전용)
    state.rendererBackend = search.get("renderer") === "pixi" ? "pixi" : "canvas";
    state.rig = normalizeRig(project._mini_rig);
    state.viewZoom = defaultViewZoom();
    state.parameters = Object.fromEntries(project.parameters.map((param) => [param.id, param.default]));
    initPhysicsState(project);
    state.selectedPartId = project.parts[0]?.id || null;
    await loadImages(project);
    if (state.rendererBackend === "pixi") {
      try {
        const pixi = await import("./core/draw_pixi.js"); // 켤 때만 로드 — canvas 모드는 의존성 0
        await pixi.initPixi(project);
      } catch (error) {
        console.warn("pixi 백엔드 초기화 실패 — canvas 폴백:", error);
        state.rendererBackend = "canvas";
      }
    }
    exposeAutomationApi();
    render();
    draw();
    if (project.physics_profiles?.length) {
      // 물리 프로파일이 있으면 30fps 상시 스테핑 — 슬라이더 조작만으로 찰랑임이 보인다
      setInterval(() => stepPhysics(1 / 30), 33);
    }
  } catch (error) {
    app.innerHTML = `<div class="fatal">Mini Cubism preview failed: ${escapeHtml(error.message)}</div>`;
  }
}

init();


export { init };
