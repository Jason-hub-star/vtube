const app = document.querySelector("#app");

const state = {
  project: null,
  images: new Map(),
  selectedPartId: null,
  overlays: {
    mesh: false,
    deformers: false,
  },
  parameters: {},
  physics: new Map(),
};

const PARAM_LABELS = {
  ParamAngleX: "Angle X",
  ParamAngleZ: "Tilt",
  ParamEyeLOpen: "Eye L",
  ParamEyeROpen: "Eye R",
  ParamEyeBallX: "Eye Ball X",
  ParamEyeBallY: "Eye Ball Y",
  ParamBrowLY: "Brow L",
  ParamBrowRY: "Brow R",
  ParamCheek: "Cheek",
  ParamMouthOpenY: "Mouth",
  ParamMouthForm: "Mouth Form",
  ParamHairFront: "Hair Front",
  ParamHairBack: "Hair Back",
  ParamAccessory: "Accessory",
};

const PREVIEW_PARAMETER_GROUPS = {
  head: ["ParamAngleX", "ParamAngleY", "ParamAngleZ"],
  body: ["ParamBodyAngleX", "ParamBodyAngleY", "ParamBreath"],
  eye: ["ParamEyeLOpen", "ParamEyeROpen", "ParamEyeBallX", "ParamEyeBallY"],
  mouth: ["ParamMouthOpenY", "ParamMouthForm"],
  hair: ["ParamHairFront", "ParamHairSide", "ParamHairBack"],
};

async function init() {
  try {
    const project = await fetchJson("/api/project");
    state.project = project;
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

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url} ${response.status}`);
  return response.json();
}

async function loadImages(project) {
  await Promise.all(
    project.parts.map(
      (part) =>
        new Promise((resolve, reject) => {
          const image = new Image();
          image.onload = () => {
            state.images.set(part.id, image);
            resolve();
          };
          image.onerror = () => reject(new Error(`image failed: ${part.source_path}`));
          image.src = `${project._project_base_url}${part.source_path}`;
        }),
    ),
  );
}

function render() {
  const project = state.project;
  app.replaceChildren();
  const shell = document.createElement("div");
  shell.className = "app-shell";
  shell.append(Sidebar(project), Stage(project), Inspector(project));
  app.append(shell);
}

function Sidebar(project) {
  const aside = document.createElement("aside");
  aside.className = "sidebar";

  const title = document.createElement("div");
  title.className = "panel-title";
  title.innerHTML = `<h1>Mini Cubism v0</h1><p>${escapeHtml(project.experiment_id)}</p>`;
  aside.append(title);

  const grouped = groupBy(project.parts, (part) => part.folder);
  for (const [folder, parts] of Object.entries(grouped)) {
    const section = document.createElement("section");
    section.className = "part-group";
    const h2 = document.createElement("h2");
    h2.textContent = `${folder} ${parts.length}`;
    section.append(h2);
    for (const part of [...parts].sort((a, b) => a.draw_order - b.draw_order)) {
      const button = document.createElement("button");
      button.className = `part-row ${part.id === state.selectedPartId ? "active" : ""}`;
      button.innerHTML = `<span>${escapeHtml(part.display_name)}</span><small>${part.draw_order}</small>`;
      button.addEventListener("click", () => {
        state.selectedPartId = part.id;
        render();
        draw();
      });
      section.append(button);
    }
    aside.append(section);
  }
  return aside;
}

function Stage(project) {
  const stage = document.createElement("main");
  stage.className = "stage";

  const toolbar = document.createElement("div");
  toolbar.className = "toolbar";
  toolbar.append(
    ToggleButton("Mesh", state.overlays.mesh, () => {
      state.overlays.mesh = !state.overlays.mesh;
      render();
      draw();
    }),
    ToggleButton("Deformers", state.overlays.deformers, () => {
      state.overlays.deformers = !state.overlays.deformers;
      render();
      draw();
    }),
    Chip(`${project.parts.length} parts`),
    Chip(`${project.deformers.length} deformers`),
    Chip(`${project.keyform_bindings.length} bindings`),
  );

  const wrap = document.createElement("div");
  wrap.className = "canvas-wrap";
  const canvas = document.createElement("canvas");
  canvas.id = "preview-canvas";
  canvas.width = project.canvas_size[0];
  canvas.height = project.canvas_size[1];
  wrap.append(canvas);
  stage.append(toolbar, wrap);
  return stage;
}

function Inspector(project) {
  const aside = document.createElement("aside");
  aside.className = "inspector";

  const section = document.createElement("section");
  section.className = "control-card";
  const h2 = document.createElement("h2");
  h2.textContent = "Parameters";
  section.append(h2);
  for (const param of project.parameters) {
    section.append(ParameterControl(param));
  }
  aside.append(section);

  const selected = project.parts.find((part) => part.id === state.selectedPartId);
  if (selected) {
    const info = document.createElement("section");
    info.className = "control-card";
    info.innerHTML = `
      <h2>Selected</h2>
      <dl>
        <dt>Part</dt><dd>${escapeHtml(selected.id)}</dd>
        <dt>Folder</dt><dd>${escapeHtml(selected.folder)}</dd>
        <dt>BBox</dt><dd>${selected.bbox.join(", ")}</dd>
        <dt>Alpha</dt><dd>${selected.alpha_coverage}</dd>
      </dl>
    `;
    aside.append(info);
  }

  const note = document.createElement("section");
  note.className = "control-card note";
  note.textContent = "v0 validates local mesh/deformer/keyform preview only. Glue remains an empty fixture-backed placeholder.";
  aside.append(note);
  return aside;
}

function ParameterControl(param) {
  const row = document.createElement("label");
  row.className = "param-row";
  row.dataset.paramId = param.id;
  const value = state.parameters[param.id] ?? param.default;
  row.innerHTML = `
    <span>${escapeHtml(PARAM_LABELS[param.id] || param.id)}</span>
    <output>${formatValue(value)}</output>
  `;
  const input = document.createElement("input");
  input.type = "range";
  input.min = param.min;
  input.max = param.max;
  input.step = param.max - param.min <= 2 ? 0.01 : 1;
  input.value = value;
  input.addEventListener("input", () => {
    resetOtherPreviewParameterGroups(param.id);
    setParameterValue(param.id, Number(input.value));
    syncParameterControls();
    draw();
  });
  row.append(input);
  return row;
}

function ToggleButton(label, active, onClick) {
  const button = document.createElement("button");
  button.className = `tool-button ${active ? "active" : ""}`;
  button.textContent = label;
  button.addEventListener("click", onClick);
  return button;
}

function Chip(text) {
  const chip = document.createElement("span");
  chip.className = "chip";
  chip.textContent = text;
  return chip;
}

function draw() {
  const canvas = document.querySelector("#preview-canvas");
  if (!canvas || !state.project) return;
  const ctx = canvas.getContext("2d");
  const project = state.project;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#f4f0e8";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const parts = [...project.parts].sort((a, b) => a.draw_order - b.draw_order);
  for (const part of parts) drawPart(ctx, project, part);
  if (state.overlays.deformers) drawDeformers(ctx, project);
  if (state.overlays.mesh) drawMeshes(ctx, project);
}

function drawPart(ctx, project, part) {
  const image = state.images.get(part.id);
  if (!image) return;
  const transform = partTransform(project, part);
  const opacity = partOpacity(project, part);
  if (opacity <= 0.01 || transform.opacity <= 0.01) return;
  const center = bboxCenter(part.bbox);
  ctx.save();
  ctx.translate(center[0] + transform.translate[0], center[1] + transform.translate[1]);
  ctx.rotate((transform.rotate * Math.PI) / 180);
  ctx.scale(transform.scale[0], transform.scale[1]);
  ctx.globalAlpha = opacity * transform.opacity;
  ctx.drawImage(image, -center[0], -center[1], project.canvas_size[0], project.canvas_size[1]);
  if (part.id === state.selectedPartId) {
    ctx.strokeStyle = "#ffcc33";
    ctx.lineWidth = 5;
    const [x, y, w, h] = part.bbox;
    ctx.strokeRect(x - center[0], y - center[1], w, h);
  }
  ctx.restore();
}

function drawMeshes(ctx, project) {
  ctx.save();
  ctx.lineWidth = 2;
  for (const mesh of project.meshes) {
    const part = project.parts.find((candidate) => candidate.id === mesh.part_id);
    if (!part) continue;
    const transform = partTransform(project, part);
    const center = bboxCenter(part.bbox);
    ctx.save();
    ctx.translate(center[0] + transform.translate[0], center[1] + transform.translate[1]);
    ctx.rotate((transform.rotate * Math.PI) / 180);
    ctx.scale(transform.scale[0], transform.scale[1]);
    ctx.translate(-center[0], -center[1]);
    ctx.strokeStyle = part.id === state.selectedPartId ? "rgba(255, 204, 51, 0.95)" : "rgba(0, 235, 190, 0.45)";
    ctx.fillStyle = part.id === state.selectedPartId ? "rgba(255, 91, 51, 0.95)" : "rgba(255,255,255,0.7)";
    for (const triangle of mesh.triangles) {
      ctx.beginPath();
      const a = mesh.vertices[triangle[0]];
      ctx.moveTo(a[0], a[1]);
      for (const index of triangle.slice(1)) {
        const v = mesh.vertices[index];
        ctx.lineTo(v[0], v[1]);
      }
      ctx.closePath();
      ctx.stroke();
    }
    if (part.id === state.selectedPartId) {
      for (const vertex of mesh.vertices) {
        ctx.fillRect(vertex[0] - 4, vertex[1] - 4, 8, 8);
      }
    }
    ctx.restore();
  }
  ctx.restore();
}

function drawDeformers(ctx, project) {
  ctx.save();
  ctx.lineWidth = 5;
  ctx.font = "34px system-ui";
  for (const deformer of project.deformers) {
    const [left, top, right, bottom] = deformer.bounds;
    const transform = deformerTransform(project, deformer);
    const pivot = deformer.pivot;
    ctx.save();
    ctx.translate(pivot[0] + transform.translate[0], pivot[1] + transform.translate[1]);
    ctx.rotate((transform.rotate * Math.PI) / 180);
    ctx.scale(transform.scale[0], transform.scale[1]);
    ctx.translate(-pivot[0], -pivot[1]);
    ctx.strokeStyle = deformer.type === "rotation" ? "rgba(255, 126, 51, 0.85)" : "rgba(80, 220, 120, 0.8)";
    ctx.strokeRect(left, top, right - left, bottom - top);
    ctx.fillStyle = "rgba(255, 255, 255, 0.9)";
    ctx.fillText(deformer.id, left + 8, top + 38);
    ctx.restore();
  }
  ctx.restore();
}

function partTransform(project, part) {
  const deformer = primaryDeformerForPart(project, part.id);
  const base = deformer ? deformerTransform(project, deformer) : identityTransform();
  return mergeTransform(mergeTransform(base, bindingTransform(project, part.id)), physicsTransformForPart(part.id));
}

function primaryDeformerForPart(project, partId) {
  const preferred = ["Eye_L", "Eye_R", "Mouth", "Hair_Front", "Hair_Back"]
    .map((id) => project.deformers.find((deformer) => deformer.id === id && deformer.child_ids.includes(partId)))
    .find(Boolean);
  if (preferred) return preferred;
  const direct = project.deformers.find((deformer) => deformer.child_ids.includes(partId) && deformer.id !== "Root");
  if (!direct) return null;
  if (partId.includes("hair") && project.deformers.find((d) => d.id === "Head_X")) return project.deformers.find((d) => d.id === "Head_X");
  return direct;
}

function deformerTransform(project, deformer) {
  let result = identityTransform();
  const chain = [];
  let current = deformer;
  while (current) {
    chain.unshift(current);
    current = project.deformers.find((candidate) => candidate.id === current.parent_id);
  }
  for (const item of chain) {
    result = mergeTransform(result, bindingTransform(project, item.id));
  }
  return result;
}

function bindingTransform(project, targetId) {
  let transform = identityTransform();
  const groups = groupBy(project.keyform_bindings.filter((item) => item.target_id === targetId), (binding) => binding.parameter_id);
  for (const [parameterId, bindings] of Object.entries(groups)) {
    const param = project.parameters.find((item) => item.id === parameterId);
    if (!param) continue;
    const current = state.parameters[param.id] ?? param.default;
    const keyframes = [
      { key_value: param.default, deltas: identityDeltas() },
      ...bindings.map((binding) => ({ key_value: binding.key_value, deltas: binding.deltas || identityDeltas() })),
    ].sort((a, b) => a.key_value - b.key_value);
    const sampled = sampleTransformKeyframes(keyframes, current);
    transform = mergeTransform(transform, sampled);
  }
  return transform;
}

function sampleTransformKeyframes(keyframes, value) {
  if (!keyframes.length) return identityTransform();
  if (value <= keyframes[0].key_value) return transformFromDeltas(keyframes[0].deltas);
  if (value >= keyframes[keyframes.length - 1].key_value) return transformFromDeltas(keyframes[keyframes.length - 1].deltas);
  for (let index = 0; index < keyframes.length - 1; index += 1) {
    const lower = keyframes[index];
    const upper = keyframes[index + 1];
    if (value >= lower.key_value && value <= upper.key_value) {
      const span = upper.key_value - lower.key_value || 1;
      const t = clamp((value - lower.key_value) / span, 0, 1);
      return interpolateTransform(transformFromDeltas(lower.deltas), transformFromDeltas(upper.deltas), t);
    }
  }
  return identityTransform();
}

function identityDeltas() {
  return { translate: [0, 0], scale: [1, 1], rotate: 0, opacity: 1 };
}

function transformFromDeltas(deltas) {
  return {
    translate: [deltas.translate?.[0] || 0, deltas.translate?.[1] || 0],
    scale: [deltas.scale?.[0] ?? 1, deltas.scale?.[1] ?? 1],
    rotate: deltas.rotate || 0,
    opacity: deltas.opacity ?? 1,
  };
}

function interpolateTransform(a, b, t) {
  return {
    translate: [lerp(a.translate[0], b.translate[0], t), lerp(a.translate[1], b.translate[1], t)],
    scale: [lerp(a.scale[0], b.scale[0], t), lerp(a.scale[1], b.scale[1], t)],
    rotate: lerp(a.rotate, b.rotate, t),
    opacity: lerp(a.opacity, b.opacity, t),
  };
}

function identityTransform() {
  return { translate: [0, 0], scale: [1, 1], rotate: 0, opacity: 1 };
}

function mergeTransform(a, b) {
  return {
    translate: [a.translate[0] + b.translate[0], a.translate[1] + b.translate[1]],
    scale: [a.scale[0] * b.scale[0], a.scale[1] * b.scale[1]],
    rotate: a.rotate + b.rotate,
    opacity: a.opacity * b.opacity,
  };
}

function partOpacity(project, part) {
  let opacity = part.opacity ?? 1;
  let hasNeutralSuppression = false;
  for (const keyform of project.part_opacity_keyframes || []) {
    if (keyform.part_id !== part.id) continue;
    if (isNeutralVisualRepairKeyform(keyform)) {
      hasNeutralSuppression = true;
      continue;
    }
    const param = project.parameters.find((item) => item.id === keyform.parameter_id);
    if (!param) continue;
    const current = state.parameters[param.id] ?? param.default;
    opacity *= sampleOpacityKeyframes(keyform.keyframes || [], current, keyform.mode || "linear");
  }
  if (hasNeutralSuppression && shouldSuppressNeutralPart(project, part)) opacity *= 0;
  return clamp(opacity, 0, 1);
}

function isNeutralVisualRepairKeyform(keyform) {
  return String(keyform.purpose || "").startsWith("neutral visual repair");
}

function shouldSuppressNeutralPart(project, part) {
  const parameterIds = neutralActivationParametersForPart(part);
  if (!parameterIds.size) return true;
  return ![...parameterIds].some((parameterId) => parameterMoved(project, parameterId));
}

function neutralActivationParametersForPart(part) {
  const ids = new Set();
  if (part.id.startsWith("eye_L_")) {
    ids.add("ParamEyeLOpen");
    if (isEyeBallDetailPart(part.id) || part.id === "eye_L_white") ["ParamEyeBallX", "ParamEyeBallY"].forEach((id) => ids.add(id));
  }
  if (part.id.startsWith("eye_R_")) {
    ids.add("ParamEyeROpen");
    if (isEyeBallDetailPart(part.id) || part.id === "eye_R_white") ["ParamEyeBallX", "ParamEyeBallY"].forEach((id) => ids.add(id));
  }
  if (part.id.startsWith("mouth_")) ["ParamMouthOpenY", "ParamMouthForm"].forEach((id) => ids.add(id));
  if (part.id.startsWith("hair_front_")) ids.add("ParamHairFront");
  if (part.id.startsWith("hair_side_")) ids.add("ParamHairSide");
  if (part.id.startsWith("hair_back_")) ids.add("ParamHairBack");
  if (["torso_base", "neck", "shoulder_L", "shoulder_R", "arm_L_upper_simple", "arm_R_upper_simple"].includes(part.id)) {
    ["ParamBodyAngleX", "ParamBodyAngleY", "ParamBreath"].forEach((id) => ids.add(id));
  }
  if (part.id.includes("cloth") || part.id.startsWith("collar_")) ["ParamBodyAngleX", "ParamBodyAngleY", "ParamBreath"].forEach((id) => ids.add(id));
  return ids;
}

function isEyeBallDetailPart(partId) {
  return partId.endsWith("_iris") || partId.endsWith("_pupil") || partId.endsWith("_highlight");
}

function parameterMoved(project, parameterId) {
  const param = project.parameters.find((item) => item.id === parameterId);
  if (!param) return false;
  const current = state.parameters[parameterId] ?? param.default;
  return Math.abs(Number(current) - Number(param.default)) > 0.001;
}

function sampleOpacityKeyframes(keyframes, value, mode) {
  if (!keyframes.length) return 1;
  const sorted = [...keyframes].sort((a, b) => a.value - b.value);
  if (mode === "step_nearest") {
    return sorted.reduce((best, item) => {
      const bestDistance = Math.abs(best.value - value);
      const itemDistance = Math.abs(item.value - value);
      return itemDistance < bestDistance ? item : best;
    }, sorted[0]).opacity;
  }
  if (value <= sorted[0].value) return sorted[0].opacity;
  if (value >= sorted[sorted.length - 1].value) return sorted[sorted.length - 1].opacity;
  for (let index = 0; index < sorted.length - 1; index += 1) {
    const lower = sorted[index];
    const upper = sorted[index + 1];
    if (value >= lower.value && value <= upper.value) {
      const span = upper.value - lower.value || 1;
      return lerp(lower.opacity, upper.opacity, clamp((value - lower.value) / span, 0, 1));
    }
  }
  return 1;
}

function initPhysicsState(project) {
  state.physics = new Map();
  for (const profile of project.physics_profiles || []) {
    state.physics.set(profile.id, { offset: [0, 0], velocity: [0, 0] });
  }
}

function resetPhysics() {
  for (const item of state.physics.values()) {
    item.offset = [0, 0];
    item.velocity = [0, 0];
  }
}

function stepPhysics(dt = 1 / 30) {
  if (!state.project) return;
  const project = state.project;
  for (const profile of project.physics_profiles || []) {
    const item = state.physics.get(profile.id);
    if (!item) continue;
    const target = physicsTargetOffset(project, profile);
    const damping = Math.pow(profile.damping ?? 0.82, dt * 60);
    const stiffness = (profile.stiffness ?? 0.16) * dt * 60;
    const drag = profile.drag ?? 0;
    for (let axis = 0; axis < 2; axis += 1) {
      const force = (target[axis] - item.offset[axis]) * stiffness;
      item.velocity[axis] = (item.velocity[axis] + force) * damping * (1 - drag);
      item.offset[axis] += item.velocity[axis] * dt * 60;
      const limit = profile.max_offset?.[axis] ?? 30;
      item.offset[axis] = clamp(item.offset[axis], -limit, limit);
    }
  }
  draw();
}

function physicsTargetOffset(project, profile) {
  const result = [0, 0];
  const weights = profile.input_weights || {};
  for (const [parameterId, vector] of Object.entries(weights)) {
    const param = project.parameters.find((item) => item.id === parameterId);
    if (!param) continue;
    const current = state.parameters[parameterId] ?? param.default;
    const range = Math.max(Math.abs(param.max - param.default), Math.abs(param.min - param.default), 1);
    const normalized = (current - param.default) / range;
    result[0] += normalized * (vector[0] || 0);
    result[1] += normalized * (vector[1] || 0);
  }
  return result;
}

function physicsTransformForPart(partId) {
  if (!state.project) return identityTransform();
  let result = identityTransform();
  for (const profile of state.project.physics_profiles || []) {
    if (!(profile.targets || []).includes(partId)) continue;
    const item = state.physics.get(profile.id);
    if (!item) continue;
    const weight = profile.part_weights?.[partId] ?? 1;
    result.translate[0] += item.offset[0] * weight;
    result.translate[1] += item.offset[1] * weight;
    result.rotate += (profile.rotate_factor || 0) * item.offset[0] * weight;
  }
  return result;
}

function setParameterValue(parameterId, value) {
  state.parameters[parameterId] = Number(value);
}

function resetOtherPreviewParameterGroups(activeParameterId) {
  const activeGroup = previewParameterGroup(activeParameterId);
  if (!activeGroup || !state.project) return;
  for (const [group, parameterIds] of Object.entries(PREVIEW_PARAMETER_GROUPS)) {
    if (group === activeGroup) continue;
    for (const parameterId of parameterIds) {
      const param = state.project.parameters.find((item) => item.id === parameterId);
      if (param) state.parameters[parameterId] = param.default;
    }
  }
}

function previewParameterGroup(parameterId) {
  for (const [group, parameterIds] of Object.entries(PREVIEW_PARAMETER_GROUPS)) {
    if (parameterIds.includes(parameterId)) return group;
  }
  return null;
}

function syncParameterControls() {
  for (const [parameterId, value] of Object.entries(state.parameters)) {
    const row = document.querySelector(`.param-row[data-param-id="${CSS.escape(parameterId)}"]`);
    if (!row) continue;
    const input = row.querySelector("input");
    const output = row.querySelector("output");
    if (input) input.value = String(value);
    if (output) output.textContent = formatValue(value);
  }
}

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
  window.__miniProject = state.project;
}

function bboxCenter(bbox) {
  return [bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2];
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function lerp(a, b, t) {
  return a + (b - a) * t;
}

function formatValue(value) {
  return Number(value).toFixed(Math.abs(value) < 2 ? 2 : 0);
}

function groupBy(items, getKey) {
  return items.reduce((groups, item) => {
    const key = getKey(item);
    if (!groups[key]) groups[key] = [];
    groups[key].push(item);
    return groups;
  }, {});
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

init();
