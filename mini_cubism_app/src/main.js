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
    state.rig = normalizeRig(project._mini_rig);
    state.viewZoom = defaultViewZoom();
    state.parameters = Object.fromEntries(project.parameters.map((param) => [param.id, param.default]));
    initPhysicsState(project);
    state.selectedPartId = project.parts[0]?.id || null;
    await loadImages(project);
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
