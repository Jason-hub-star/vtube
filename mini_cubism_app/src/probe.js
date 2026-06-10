// 자동화/주입 API (__miniProbe, __miniSetParameters 등). T2/T3 계약.

import { draw } from "./core/draw.js";
import { resetPhysics, stepPhysics } from "./core/physics.js";
import { partOpacity, setParameterValue } from "./core/rig.js";
import { state } from "./core/state.js";
import { render, syncParameterControls } from "./ui/components.js";

function exposeAutomationApi() {
  window.__miniSetParameters = (values = {}) => {
    for (const [parameterId, value] of Object.entries(values)) {
      setParameterValue(parameterId, value);
    }
    syncParameterControls();
    draw();
  };
  window.__miniResetPhysics = () => {
    resetPhysics();
    draw();
  };
  window.__miniClearSelection = () => {
    state.selectedPartId = null;
    render();
    draw();
  };
  window.__miniStepPhysics = (dt = 1 / 30) => stepPhysics(dt);
  window.__miniSnapshot = () => ({
    parameters: { ...state.parameters },
    physics: Object.fromEntries(
      [...state.physics.entries()].map(([id, item]) => [id, { offset: [...item.offset], velocity: [...item.velocity] }]),
    ),
    part_opacity: Object.fromEntries((state.project?.parts || []).map((part) => [part.id, partOpacity(state.project, part)])),
  });
  window.__miniRig = () => state.rig;
  window.__miniProject = state.project;
  // T2 __vtubeProbe와 동일 계약의 주입 인터페이스 (T3 웹캠 드라이브용)
  window.__miniProbe = {
    waitReady(timeoutMs = 10000) {
      return new Promise((resolve) => {
        const started = performance.now();
        const tick = () => {
          if (state.project) return resolve(true);
          if (performance.now() - started > timeoutMs) return resolve(false);
          setTimeout(tick, 50);
        };
        tick();
      });
    },
    parameters() {
      return (state.project?.parameters || []).map((param) => ({
        id: param.id,
        min: param.min,
        max: param.max,
        defaultValue: param.default,
      }));
    },
    setParameterValues(values = {}) {
      const applied = [];
      const missing = [];
      for (const [parameterId, value] of Object.entries(values)) {
        if (state.project?.parameters?.some((item) => item.id === parameterId)) {
          setParameterValue(parameterId, value);
          applied.push(parameterId);
        } else {
          missing.push(parameterId);
        }
      }
      syncParameterControls();
      draw();
      return { applied, missing };
    },
    snapshot: () => window.__miniSnapshot(),
    canvasHash() {
      const canvas = document.querySelector("#preview-canvas");
      if (!canvas) return null;
      const ctx2d = canvas.getContext("2d");
      const { data } = ctx2d.getImageData(0, 0, canvas.width, canvas.height);
      let hash = 2166136261;
      for (let i = 0; i < data.length; i += 64) {
        hash ^= data[i];
        hash = Math.imul(hash, 16777619) >>> 0;
      }
      return hash >>> 0;
    },
  };
}


export { exposeAutomationApi };
