// 엔트리포인트.

import { defaultViewZoom, draw } from "./core/draw.js";
import { initPhysicsState } from "./core/physics.js";
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
  } catch (error) {
    app.innerHTML = `<div class="fatal">Mini Cubism preview failed: ${escapeHtml(error.message)}</div>`;
  }
}

init();


export { init };
