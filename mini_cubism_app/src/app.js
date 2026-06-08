const app = document.querySelector("#app");

const state = {
  project: null,
  images: new Map(),
  selectedPartId: null,
  overlays: {
    mesh: false,
    deformers: false,
  },
  activePanel: "preview",
  clippingPreview: true,
  parameters: {},
  physics: new Map(),
  rig: null,
  rigStatus: "",
  rigTool: "mesh",
  selectedCoverSide: "L",
  draggedVertex: null,
  draggedCover: null,
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
    state.rig = normalizeRig(project._mini_rig);
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
    ToggleButton("Preview", state.activePanel === "preview", () => {
      state.activePanel = "preview";
      render();
      draw();
    }),
    ToggleButton("Rig", state.activePanel === "rig", () => {
      state.activePanel = "rig";
      state.overlays.mesh = true;
      state.rigTool = state.rigTool || "mesh";
      ensureRigEyeSelection(project);
      render();
      draw();
    }),
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
    ToggleButton("Clip", state.clippingPreview, () => {
      state.clippingPreview = !state.clippingPreview;
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
  canvas.addEventListener("pointerdown", onCanvasPointerDown);
  canvas.addEventListener("pointermove", onCanvasPointerMove);
  canvas.addEventListener("pointerup", onCanvasPointerUp);
  canvas.addEventListener("pointerleave", onCanvasPointerUp);
  wrap.append(canvas);
  stage.append(toolbar, wrap);
  return stage;
}

function Inspector(project) {
  const aside = document.createElement("aside");
  aside.className = "inspector";

  if (state.activePanel === "rig") {
    aside.append(RigPanel(project));
    return aside;
  }

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

function RigPanel(project) {
  const fragment = document.createDocumentFragment();
  ensureRigEyeSelection(project);
  const selected = selectedPart(project);
  const eyeParts = project.parts.filter((part) => part.id.startsWith("eye_"));

  const header = document.createElement("section");
  header.className = "control-card";
  header.innerHTML = `
    <h2>Rig</h2>
    <p class="note">눈 ArtMesh와 keyform을 Mini Cubism 전용 rig JSON으로 저장합니다.</p>
  `;
  const actions = document.createElement("div");
  actions.className = "button-row";
  actions.append(
    SmallButton("저장", saveRig),
    SmallButton("눈 검증", runEyeValidation),
  );
  header.append(actions);
  const modeRow = document.createElement("div");
  modeRow.className = "segmented-row";
  modeRow.append(
    SegmentButton("Mesh", state.rigTool === "mesh", () => {
      state.rigTool = "mesh";
      state.overlays.mesh = true;
      state.draggedCover = null;
      render();
      draw();
    }),
    SegmentButton("눈 영역", state.rigTool === "cover", () => {
      state.rigTool = "cover";
      state.overlays.mesh = false;
      state.draggedVertex = null;
      render();
      draw();
    }),
  );
  header.append(modeRow);
  if (state.rigStatus) {
    const status = document.createElement("p");
    status.className = "status-line";
    status.textContent = state.rigStatus;
    header.append(status);
  }
  fragment.append(header);

  if (state.rigTool === "mesh") {
    const partCard = document.createElement("section");
    partCard.className = "control-card";
    const select = document.createElement("select");
    select.className = "rig-select";
    for (const part of eyeParts) {
      const option = document.createElement("option");
      option.value = part.id;
      option.textContent = `${part.display_name} (${part.id})`;
      option.selected = part.id === state.selectedPartId;
      select.append(option);
    }
    select.addEventListener("change", () => {
      state.selectedPartId = select.value;
      render();
      draw();
    });
    partCard.innerHTML = `<h2>Eye ArtMesh</h2>`;
    partCard.append(select);
    if (selected) {
      const mesh = editableMeshForPart(project, selected.id);
      const selectedVertex = state.draggedVertex?.partId === selected.id ? state.draggedVertex.vertexIndex : "-";
      const meta = document.createElement("dl");
      meta.innerHTML = `
        <dt>Part</dt><dd>${escapeHtml(selected.id)}</dd>
        <dt>Vertices</dt><dd>${mesh?.vertices.length || 0}</dd>
        <dt>Selected</dt><dd>${selectedVertex}</dd>
      `;
      partCard.append(meta);
    }
    const meshActions = document.createElement("div");
    meshActions.className = "button-row";
    meshActions.append(
      SmallButton("현재 Mesh 저장", () => saveMeshOverride(selected?.id)),
      SmallButton("Mesh 초기화", () => resetMeshOverride(selected?.id)),
    );
    partCard.append(meshActions);
    fragment.append(partCard);
  } else {
    fragment.append(EyeCoverPanel(project));
  }

  const keyCard = document.createElement("section");
  keyCard.className = "control-card";
  keyCard.innerHTML = `<h2>Eye Keyform</h2>`;
  for (const paramId of ["ParamEyeLOpen", "ParamEyeROpen", "ParamEyeBallX", "ParamEyeBallY"]) {
    const param = project.parameters.find((item) => item.id === paramId);
    if (param) keyCard.append(ParameterControl(param));
  }
  const keyActions = document.createElement("div");
  keyActions.className = "button-row";
  keyActions.append(
    SmallButton("EyeBall 키폼 저장", captureEyeBallKeyform),
    SmallButton("EyeOpen 키폼 저장", captureEyeOpenKeyform),
  );
  keyCard.append(keyActions);
  const saved = document.createElement("p");
  saved.className = "note";
  saved.textContent = `저장된 keyform overrides: ${state.rig.keyform_overrides.length}`;
  keyCard.append(saved);
  fragment.append(keyCard);

  const clipCard = document.createElement("section");
  clipCard.className = "control-card";
  clipCard.innerHTML = `
    <h2>Clipping Preview</h2>
    <p class="note">eye white 알파를 기준으로 iris/pupil/highlight를 잘라 봅니다.</p>
  `;
  const clipToggle = document.createElement("label");
  clipToggle.className = "toggle-row";
  clipToggle.innerHTML = `<span>눈동자 clipping</span>`;
  const input = document.createElement("input");
  input.type = "checkbox";
  input.checked = state.clippingPreview;
  input.addEventListener("change", () => {
    state.clippingPreview = input.checked;
    draw();
  });
  clipToggle.append(input);
  clipCard.append(clipToggle);
  fragment.append(clipCard);
  return fragment;
}

function EyeCoverPanel(project) {
  const card = document.createElement("section");
  card.className = "control-card";
  const covers = ensureEyeSocketCovers(project);
  const side = state.selectedCoverSide === "R" ? "R" : "L";
  const config = ensureEyeSocketCoverConfig(project, side);
  card.innerHTML = `
    <h2>눈 닫힘 영역</h2>
    <p class="note">파란/노란 박스를 눈 안쪽으로 맞추면 닫힘 때 눈 밖 피부가 덜 같이 움직입니다.</p>
  `;

  const sideRow = document.createElement("div");
  sideRow.className = "segmented-row";
  sideRow.append(
    SegmentButton("왼눈 L", side === "L", () => {
      state.selectedCoverSide = "L";
      render();
      draw();
    }),
    SegmentButton("오른눈 R", side === "R", () => {
      state.selectedCoverSide = "R";
      render();
      draw();
    }),
  );
  card.append(sideRow);

  const enabled = document.createElement("label");
  enabled.className = "toggle-row";
  enabled.innerHTML = `<span>cover 사용</span>`;
  const enabledInput = document.createElement("input");
  enabledInput.type = "checkbox";
  enabledInput.checked = covers.enabled !== false;
  enabledInput.addEventListener("change", () => {
    covers.enabled = enabledInput.checked;
    draw();
  });
  enabled.append(enabledInput);
  card.append(enabled);

  const bboxGrid = document.createElement("div");
  bboxGrid.className = "field-grid";
  ["x", "y", "w", "h"].forEach((label, index) => {
    bboxGrid.append(NumberField(label, config.bbox[index], 1, (value) => {
      const next = [...config.bbox];
      next[index] = Math.round(value);
      if (index >= 2) next[index] = Math.max(index === 2 ? 30 : 20, next[index]);
      config.bbox = next;
      draw();
    }));
  });
  card.append(bboxGrid);

  card.append(
    RangeField("불투명도", config.max_opacity ?? 0.9, 0, 1, 0.01, (value) => {
      config.max_opacity = Number(value.toFixed(2));
      draw();
    }),
    RangeField("가로 축소", config.scale_x ?? 0.8, 0.45, 1.2, 0.01, (value) => {
      config.scale_x = Number(value.toFixed(2));
      draw();
    }),
    RangeField("세로 축소", config.scale_y ?? 0.52, 0.25, 1.0, 0.01, (value) => {
      config.scale_y = Number(value.toFixed(2));
      draw();
    }),
    RangeField("blur", config.blur ?? 1, 0, 8, 0.25, (value) => {
      config.blur = Number(value.toFixed(2));
      draw();
    }),
  );

  const actions = document.createElement("div");
  actions.className = "button-row";
  actions.append(
    SmallButton("선택눈 닫힘 보기", () => previewSelectedEyeClosed(side)),
    SmallButton("양눈 닫힘 보기", previewBothEyesClosed),
    SmallButton("자동영역 복구", () => resetEyeCoverConfig(project, side)),
  );
  card.append(actions);
  return card;
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

function SmallButton(label, onClick) {
  const button = document.createElement("button");
  button.className = "small-button";
  button.type = "button";
  button.textContent = label;
  button.addEventListener("click", onClick);
  return button;
}

function SegmentButton(label, active, onClick) {
  const button = document.createElement("button");
  button.className = `segment-button ${active ? "active" : ""}`;
  button.type = "button";
  button.textContent = label;
  button.addEventListener("click", onClick);
  return button;
}

function NumberField(label, value, step, onInput) {
  const wrap = document.createElement("label");
  wrap.className = "number-field";
  wrap.innerHTML = `<span>${escapeHtml(label)}</span>`;
  const input = document.createElement("input");
  input.type = "number";
  input.step = step;
  input.value = value;
  input.addEventListener("input", () => onInput(Number(input.value)));
  wrap.append(input);
  return wrap;
}

function RangeField(label, value, min, max, step, onInput) {
  const row = document.createElement("label");
  row.className = "param-row compact";
  row.innerHTML = `<span>${escapeHtml(label)}</span><output>${formatValue(value)}</output>`;
  const input = document.createElement("input");
  input.type = "range";
  input.min = min;
  input.max = max;
  input.step = step;
  input.value = value;
  input.addEventListener("input", () => {
    const next = Number(input.value);
    row.querySelector("output").textContent = formatValue(next);
    onInput(next);
  });
  row.append(input);
  return row;
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
  for (const part of parts) {
    drawPart(ctx, project, part);
    if (part.id === "face_base") drawEyeSocketCovers(ctx, project);
  }
  if (state.overlays.deformers) drawDeformers(ctx, project);
  if (state.overlays.mesh) drawMeshes(ctx, project);
  if (state.activePanel === "rig" && state.rigTool === "cover") drawEyeCoverEditor(ctx, project);
}

function drawPart(ctx, project, part) {
  const image = state.images.get(part.id);
  if (!image) return;
  const transform = partTransform(project, part);
  const opacity = partOpacity(project, part);
  if (opacity <= 0.01 || transform.opacity <= 0.01) return;
  if (state.clippingPreview && clippedByEyeWhite(part.id)) {
    drawClippedEyePart(ctx, project, part, image, transform, opacity);
    return;
  }
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

function drawClippedEyePart(ctx, project, part, image, transform, opacity) {
  const maskPartId = part.id.startsWith("eye_L_") ? "eye_L_white" : "eye_R_white";
  const maskImage = state.images.get(maskPartId);
  if (!maskImage) return;
  const temp = document.createElement("canvas");
  temp.width = project.canvas_size[0];
  temp.height = project.canvas_size[1];
  const tempCtx = temp.getContext("2d");
  const center = bboxCenter(part.bbox);
  tempCtx.save();
  tempCtx.translate(center[0] + transform.translate[0], center[1] + transform.translate[1]);
  tempCtx.rotate((transform.rotate * Math.PI) / 180);
  tempCtx.scale(transform.scale[0], transform.scale[1]);
  tempCtx.globalAlpha = opacity * transform.opacity;
  tempCtx.drawImage(image, -center[0], -center[1], project.canvas_size[0], project.canvas_size[1]);
  tempCtx.restore();
  tempCtx.globalCompositeOperation = "destination-in";
  tempCtx.drawImage(maskImage, 0, 0, project.canvas_size[0], project.canvas_size[1]);
  ctx.drawImage(temp, 0, 0);
}

function drawEyeSocketCovers(ctx, project) {
  const covers = state.rig?.eye_socket_covers;
  if (!covers?.enabled) return;
  for (const side of ["L", "R"]) {
    const config = covers[side];
    if (!config) continue;
    const parameterId = side === "L" ? "ParamEyeLOpen" : "ParamEyeROpen";
    const openValue = state.parameters[parameterId] ?? 1;
    const start = config.fade_start ?? 0.96;
    const full = config.fade_full ?? 0.08;
    const opacity = clamp(((start - openValue) / Math.max(start - full, 0.001)) * (config.max_opacity ?? 0.98), 0, config.max_opacity ?? 0.98);
    if (opacity <= 0.01) continue;
    const bbox = config.bbox || inferredEyeSocketCoverBbox(project, side);
    drawSocketCoverShape(ctx, bbox, config, opacity);
  }
}

function drawSocketCoverShape(ctx, bbox, config, opacity) {
  const [x, y, w, h] = bbox;
  const cx = x + w / 2;
  const cy = y + h / 2;
  const rx = (w / 2) * (config.scale_x ?? 0.92);
  const ry = (h / 2) * (config.scale_y ?? 0.66);
  ctx.save();
  ctx.globalAlpha = opacity;
  ctx.filter = `blur(${config.blur ?? 2}px)`;
  const gradient = ctx.createLinearGradient(cx, y, cx, y + h);
  gradient.addColorStop(0, config.upper_color || "#f8ded2");
  gradient.addColorStop(0.55, config.mid_color || "#f4cfc3");
  gradient.addColorStop(1, config.lower_color || "#e7b6aa");
  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.filter = "none";
  ctx.globalAlpha = Math.min(1, opacity * 0.42);
  ctx.fillStyle = config.lower_color || "#e7b6aa";
  ctx.beginPath();
  ctx.ellipse(cx, cy + ry * 0.32, rx * 0.74, ry * 0.24, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function drawEyeCoverEditor(ctx, project) {
  const covers = ensureEyeSocketCovers(project);
  ctx.save();
  ctx.lineWidth = 4;
  ctx.font = "28px system-ui";
  for (const side of ["L", "R"]) {
    const config = ensureEyeSocketCoverConfig(project, side);
    const [x, y, w, h] = config.bbox;
    const selected = side === state.selectedCoverSide;
    ctx.strokeStyle = selected ? "rgba(255, 204, 51, 0.98)" : "rgba(66, 170, 255, 0.72)";
    ctx.fillStyle = selected ? "rgba(255, 204, 51, 0.12)" : "rgba(66, 170, 255, 0.08)";
    ctx.fillRect(x, y, w, h);
    ctx.strokeRect(x, y, w, h);
    ctx.fillStyle = selected ? "rgba(255, 204, 51, 0.98)" : "rgba(66, 170, 255, 0.9)";
    for (const point of coverHandlePoints(config.bbox)) {
      ctx.fillRect(point.x - 8, point.y - 8, 16, 16);
    }
    ctx.fillText(`${side} eye cover`, x, Math.max(34, y - 12));
  }
  if (covers.enabled === false) {
    ctx.fillStyle = "rgba(255, 80, 48, 0.9)";
    ctx.fillText("eye cover disabled", 34, 54);
  }
  ctx.restore();
}

function inferredEyeSocketCoverBbox(project, side) {
  const prefix = side === "L" ? "eye_L_" : "eye_R_";
  const ids = ["white", "upper_lash", "lower_lash", "closed_lid"].map((suffix) => `${prefix}${suffix}`);
  const boxes = ids.map((id) => project.parts.find((part) => part.id === id)?.bbox).filter(Boolean);
  if (!boxes.length) return [0, 0, 0, 0];
  const left = Math.min(...boxes.map((bbox) => bbox[0])) - 8;
  const top = Math.min(...boxes.map((bbox) => bbox[1])) - 6;
  const right = Math.max(...boxes.map((bbox) => bbox[0] + bbox[2])) + 8;
  const bottom = Math.max(...boxes.map((bbox) => bbox[1] + bbox[3])) + 8;
  return [left, top, right - left, bottom - top];
}

function clippedByEyeWhite(partId) {
  if (!state.rig?.clipping?.enabled) return false;
  const pairs = state.rig.clipping.pairs || {};
  return Object.values(pairs).some((partIds) => partIds.includes(partId));
}

function drawMeshes(ctx, project) {
  ctx.save();
  ctx.lineWidth = 2;
  for (const mesh of project.meshes) {
    const part = project.parts.find((candidate) => candidate.id === mesh.part_id);
    if (!part) continue;
    const editableMesh = editableMeshForPart(project, part.id) || mesh;
    const transform = partTransform(project, part);
    const center = bboxCenter(part.bbox);
    ctx.save();
    ctx.translate(center[0] + transform.translate[0], center[1] + transform.translate[1]);
    ctx.rotate((transform.rotate * Math.PI) / 180);
    ctx.scale(transform.scale[0], transform.scale[1]);
    ctx.translate(-center[0], -center[1]);
    ctx.strokeStyle = part.id === state.selectedPartId ? "rgba(255, 204, 51, 0.95)" : "rgba(0, 235, 190, 0.45)";
    ctx.fillStyle = part.id === state.selectedPartId ? "rgba(255, 91, 51, 0.95)" : "rgba(255,255,255,0.7)";
    for (const triangle of editableMesh.triangles) {
      ctx.beginPath();
      const a = editableMesh.vertices[triangle[0]];
      ctx.moveTo(a[0], a[1]);
      for (const index of triangle.slice(1)) {
        const v = editableMesh.vertices[index];
        ctx.lineTo(v[0], v[1]);
      }
      ctx.closePath();
      ctx.stroke();
    }
    if (part.id === state.selectedPartId) {
      editableMesh.vertices.forEach((vertex, index) => {
        const isDragged = state.draggedVertex?.partId === part.id && state.draggedVertex.vertexIndex === index;
        ctx.fillStyle = isDragged ? "rgba(255, 80, 48, 1)" : "rgba(255, 204, 51, 0.95)";
        ctx.fillRect(vertex[0] - 5, vertex[1] - 5, 10, 10);
      });
      if (state.clippingPreview && (part.id === "eye_L_white" || part.id === "eye_R_white")) {
        ctx.strokeStyle = "rgba(66, 170, 255, 0.95)";
        ctx.lineWidth = 4;
        const [x, y, w, h] = part.bbox;
        ctx.strokeRect(x, y, w, h);
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
  const groups = groupBy(effectiveKeyformBindings(project).filter((item) => item.target_id === targetId), (binding) => binding.parameter_id);
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

function effectiveKeyformBindings(project) {
  const overrides = state.rig?.keyform_overrides || [];
  if (!overrides.length) return project.keyform_bindings;
  const overrideKeys = new Set(overrides.map(bindingKey));
  return [...project.keyform_bindings.filter((binding) => !overrideKeys.has(bindingKey(binding))), ...overrides];
}

function bindingKey(binding) {
  return `${binding.parameter_id}::${binding.target_id}::${binding.key_value}`;
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
  opacity *= eyeOpenDetailOpacity(project, part);
  return clamp(opacity, 0, 1);
}

function eyeOpenDetailOpacity(project, part) {
  if (!part.id.startsWith("eye_L_") && !part.id.startsWith("eye_R_")) return 1;
  if (part.id.endsWith("_closed_lid")) return 1;
  const side = part.id.startsWith("eye_L_") ? "L" : "R";
  const covers = state.rig?.eye_socket_covers;
  if (!covers?.enabled) return 1;
  const config = covers[side] || {};
  const parameterId = side === "L" ? "ParamEyeLOpen" : "ParamEyeROpen";
  const param = project.parameters.find((item) => item.id === parameterId);
  if (!param) return 1;
  const openValue = state.parameters[parameterId] ?? param.default;
  const hideAt = config.hide_open_parts_at ?? 0.22;
  const fullAt = config.show_open_parts_at ?? 0.82;
  return clamp((openValue - hideAt) / Math.max(fullAt - hideAt, 0.001), 0, 1);
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

function normalizeRig(rig) {
  const base = {
    schema_version: 1,
    project_kind: "mini_cubism_rig_v0",
    mesh_overrides: {},
    keyform_overrides: [],
    clipping: {
      enabled: true,
      pairs: {
        eye_L_white: ["eye_L_iris", "eye_L_pupil", "eye_L_highlight"],
        eye_R_white: ["eye_R_iris", "eye_R_pupil", "eye_R_highlight"],
      },
    },
    eye_socket_covers: {
      enabled: true,
      L: {
        bbox: [814, 674, 190, 92],
        fade_start: 0.96,
        fade_full: 0.08,
        max_opacity: 0.9,
        hide_open_parts_at: 0.22,
        show_open_parts_at: 0.82,
        upper_color: "#fae7dd",
        mid_color: "#f4d7cc",
        lower_color: "#e9bfb4",
        blur: 1,
        scale_x: 0.8,
        scale_y: 0.52,
      },
      R: {
        bbox: [1066, 676, 190, 92],
        fade_start: 0.96,
        fade_full: 0.08,
        max_opacity: 0.9,
        hide_open_parts_at: 0.22,
        show_open_parts_at: 0.82,
        upper_color: "#fae7dd",
        mid_color: "#f4d5ca",
        lower_color: "#e8bbb0",
        blur: 1,
        scale_x: 0.8,
        scale_y: 0.52,
      },
    },
    notes: [],
  };
  return {
    ...base,
    ...(rig || {}),
    mesh_overrides: { ...base.mesh_overrides, ...(rig?.mesh_overrides || {}) },
    keyform_overrides: rig?.keyform_overrides || [],
    clipping: {
      ...base.clipping,
      ...(rig?.clipping || {}),
      pairs: { ...base.clipping.pairs, ...(rig?.clipping?.pairs || {}) },
    },
    eye_socket_covers: {
      ...base.eye_socket_covers,
      ...(rig?.eye_socket_covers || {}),
      L: { ...base.eye_socket_covers.L, ...(rig?.eye_socket_covers?.L || {}) },
      R: { ...base.eye_socket_covers.R, ...(rig?.eye_socket_covers?.R || {}) },
    },
  };
}

function selectedPart(project) {
  const selected = project.parts.find((part) => part.id === state.selectedPartId);
  if (state.activePanel !== "rig") return selected;
  return selected?.id.startsWith("eye_") ? selected : project.parts.find((part) => part.id.startsWith("eye_"));
}

function ensureRigEyeSelection(project) {
  const selected = project.parts.find((part) => part.id === state.selectedPartId);
  if (!selected || !selected.id.startsWith("eye_")) {
    state.selectedPartId = project.parts.find((part) => part.id.startsWith("eye_"))?.id || state.selectedPartId;
  }
}

function editableMeshForPart(project, partId) {
  const source = project.meshes.find((mesh) => mesh.part_id === partId);
  if (!source) return null;
  const override = state.rig?.mesh_overrides?.[partId];
  if (!override) return source;
  return {
    ...source,
    vertices: override.vertices || source.vertices,
    triangles: override.triangles || source.triangles,
  };
}

function ensureMeshOverride(partId) {
  if (!partId || !state.project || !state.rig) return null;
  const source = state.project.meshes.find((mesh) => mesh.part_id === partId);
  if (!source) return null;
  if (!state.rig.mesh_overrides[partId]) {
    state.rig.mesh_overrides[partId] = {
      vertices: source.vertices.map((vertex) => [...vertex]),
      triangles: source.triangles.map((triangle) => [...triangle]),
      updated_at: new Date().toISOString(),
    };
  }
  return state.rig.mesh_overrides[partId];
}

function ensureEyeSocketCovers(project) {
  if (!state.rig) state.rig = normalizeRig(project?._mini_rig);
  if (!state.rig.eye_socket_covers) state.rig.eye_socket_covers = normalizeRig(null).eye_socket_covers;
  for (const side of ["L", "R"]) ensureEyeSocketCoverConfig(project, side);
  return state.rig.eye_socket_covers;
}

function ensureEyeSocketCoverConfig(project, side) {
  const covers = state.rig.eye_socket_covers;
  const base = normalizeRig(null).eye_socket_covers[side];
  if (!covers[side]) covers[side] = { ...base };
  covers[side] = {
    ...base,
    ...covers[side],
    bbox: covers[side].bbox || inferredEyeSocketCoverBbox(project, side),
  };
  return covers[side];
}

function resetEyeCoverConfig(project, side) {
  const config = ensureEyeSocketCoverConfig(project, side);
  config.bbox = inferredEyeSocketCoverBbox(project, side);
  state.rigStatus = `${side} 눈 영역 자동값으로 복구`;
  render();
  draw();
}

function previewSelectedEyeClosed(side) {
  resetOtherPreviewParameterGroups(side === "L" ? "ParamEyeLOpen" : "ParamEyeROpen");
  setParameterValue(side === "L" ? "ParamEyeLOpen" : "ParamEyeROpen", 0);
  syncParameterControls();
  draw();
}

function previewBothEyesClosed() {
  resetOtherPreviewParameterGroups("ParamEyeLOpen");
  setParameterValue("ParamEyeLOpen", 0);
  setParameterValue("ParamEyeROpen", 0);
  syncParameterControls();
  draw();
}

function saveMeshOverride(partId) {
  if (!partId) return;
  ensureMeshOverride(partId);
  state.rig.mesh_overrides[partId].updated_at = new Date().toISOString();
  state.rigStatus = `${partId} mesh override 저장 대기`;
  render();
  draw();
}

function resetMeshOverride(partId) {
  if (!partId || !state.rig) return;
  delete state.rig.mesh_overrides[partId];
  state.draggedVertex = null;
  state.rigStatus = `${partId} mesh override 초기화`;
  render();
  draw();
}

function canvasPoint(event) {
  const canvas = document.querySelector("#preview-canvas");
  const rect = canvas.getBoundingClientRect();
  return [
    ((event.clientX - rect.left) / rect.width) * canvas.width,
    ((event.clientY - rect.top) / rect.height) * canvas.height,
  ];
}

function onCanvasPointerDown(event) {
  if (state.activePanel !== "rig" || !state.project) return;
  if (state.rigTool === "cover") {
    onEyeCoverPointerDown(event);
    return;
  }
  if (!state.selectedPartId) return;
  const part = state.project.parts.find((item) => item.id === state.selectedPartId);
  if (!part || !part.id.startsWith("eye_")) return;
  const mesh = editableMeshForPart(state.project, part.id);
  if (!mesh) return;
  const point = canvasPoint(event);
  let best = null;
  mesh.vertices.forEach((vertex, index) => {
    const distance = Math.hypot(vertex[0] - point[0], vertex[1] - point[1]);
    if (distance <= 28 && (!best || distance < best.distance)) best = { vertexIndex: index, distance };
  });
  if (!best) return;
  ensureMeshOverride(part.id);
  state.draggedVertex = { partId: part.id, vertexIndex: best.vertexIndex };
  try {
    event.currentTarget.setPointerCapture(event.pointerId);
  } catch {
    // Synthetic browser tests do not always create an active pointer first.
  }
  render();
  draw();
}

function onCanvasPointerMove(event) {
  if (state.draggedCover) {
    onEyeCoverPointerMove(event);
    return;
  }
  if (!state.draggedVertex || !state.rig) return;
  const override = ensureMeshOverride(state.draggedVertex.partId);
  if (!override) return;
  const point = canvasPoint(event);
  override.vertices[state.draggedVertex.vertexIndex] = [Math.round(point[0]), Math.round(point[1])];
  override.updated_at = new Date().toISOString();
  draw();
}

function onCanvasPointerUp() {
  if (state.draggedCover) {
    state.rigStatus = `${state.draggedCover.side} 눈 영역 편집됨`;
    state.draggedCover = null;
    render();
    draw();
    return;
  }
  if (!state.draggedVertex) return;
  state.rigStatus = `${state.draggedVertex.partId} 정점 ${state.draggedVertex.vertexIndex} 편집됨`;
  state.draggedVertex = null;
  render();
  draw();
}

function onEyeCoverPointerDown(event) {
  if (!state.rig || !state.project) return;
  const point = canvasPoint(event);
  const hit = hitEyeCover(point);
  if (!hit) return;
  state.selectedCoverSide = hit.side;
  const config = ensureEyeSocketCoverConfig(state.project, hit.side);
  state.draggedCover = {
    side: hit.side,
    handle: hit.handle,
    startPoint: point,
    startBbox: [...config.bbox],
  };
  try {
    event.currentTarget.setPointerCapture(event.pointerId);
  } catch {
    // Synthetic browser tests do not always create an active pointer first.
  }
  render();
  draw();
}

function onEyeCoverPointerMove(event) {
  const drag = state.draggedCover;
  if (!drag || !state.project) return;
  const point = canvasPoint(event);
  const dx = Math.round(point[0] - drag.startPoint[0]);
  const dy = Math.round(point[1] - drag.startPoint[1]);
  const config = ensureEyeSocketCoverConfig(state.project, drag.side);
  config.bbox = resizedCoverBbox(drag.startBbox, drag.handle, dx, dy, state.project.canvas_size);
  draw();
}

function hitEyeCover(point) {
  for (const side of [state.selectedCoverSide, state.selectedCoverSide === "L" ? "R" : "L"]) {
    const config = ensureEyeSocketCoverConfig(state.project, side);
    for (const handle of coverHandlePoints(config.bbox)) {
      if (Math.abs(point[0] - handle.x) <= 24 && Math.abs(point[1] - handle.y) <= 24) {
        return { side, handle: handle.id };
      }
    }
    const [x, y, w, h] = config.bbox;
    if (point[0] >= x && point[0] <= x + w && point[1] >= y && point[1] <= y + h) {
      return { side, handle: "move" };
    }
  }
  return null;
}

function coverHandlePoints(bbox) {
  const [x, y, w, h] = bbox;
  return [
    { id: "nw", x, y },
    { id: "ne", x: x + w, y },
    { id: "sw", x, y: y + h },
    { id: "se", x: x + w, y: y + h },
  ];
}

function resizedCoverBbox(bbox, handle, dx, dy, canvasSize) {
  let [x, y, w, h] = bbox;
  if (handle === "move") {
    x += dx;
    y += dy;
  } else {
    if (handle.includes("w")) {
      x += dx;
      w -= dx;
    }
    if (handle.includes("e")) w += dx;
    if (handle.includes("n")) {
      y += dy;
      h -= dy;
    }
    if (handle.includes("s")) h += dy;
  }
  const minW = 30;
  const minH = 20;
  if (w < minW) {
    if (handle.includes("w")) x -= minW - w;
    w = minW;
  }
  if (h < minH) {
    if (handle.includes("n")) y -= minH - h;
    h = minH;
  }
  x = clamp(Math.round(x), 0, canvasSize[0] - minW);
  y = clamp(Math.round(y), 0, canvasSize[1] - minH);
  w = clamp(Math.round(w), minW, canvasSize[0] - x);
  h = clamp(Math.round(h), minH, canvasSize[1] - y);
  return [x, y, w, h];
}

function captureEyeBallKeyform() {
  const rows = [];
  const x = state.parameters.ParamEyeBallX || 0;
  const y = state.parameters.ParamEyeBallY || 0;
  if (Math.abs(x) > 0.001) {
    for (const partId of ["eye_L_iris", "eye_L_pupil", "eye_L_highlight", "eye_R_iris", "eye_R_pupil", "eye_R_highlight"]) {
      rows.push({
        parameter_id: "ParamEyeBallX",
        key_value: Number(x.toFixed(2)),
        target_id: partId,
        delta_type: "deformer_transform",
        deltas: bindingTransformFromProjectOnly(state.project, partId, "ParamEyeBallX", x),
      });
    }
  }
  if (Math.abs(y) > 0.001) {
    for (const partId of ["eye_L_iris", "eye_L_pupil", "eye_L_highlight", "eye_R_iris", "eye_R_pupil", "eye_R_highlight"]) {
      rows.push({
        parameter_id: "ParamEyeBallY",
        key_value: Number(y.toFixed(2)),
        target_id: partId,
        delta_type: "deformer_transform",
        deltas: bindingTransformFromProjectOnly(state.project, partId, "ParamEyeBallY", y),
      });
    }
  }
  upsertKeyformOverrides(rows);
  state.rigStatus = rows.length ? `EyeBall keyform ${rows.length}개 저장 대기` : "EyeBall 값을 먼저 움직여주세요";
  render();
  draw();
}

function captureEyeOpenKeyform() {
  const rows = [];
  const pairs = [
    ["ParamEyeLOpen", "eye_L_warp"],
    ["ParamEyeROpen", "eye_R_warp"],
  ];
  for (const [parameterId, targetId] of pairs) {
    const value = state.parameters[parameterId];
    const param = state.project.parameters.find((item) => item.id === parameterId);
    if (!param || Math.abs(value - param.default) <= 0.001) continue;
    rows.push({
      parameter_id: parameterId,
      key_value: Number(value.toFixed(2)),
      target_id: targetId,
      delta_type: "deformer_transform",
      deltas: bindingTransformFromProjectOnly(state.project, targetId, parameterId, value),
    });
  }
  upsertKeyformOverrides(rows);
  state.rigStatus = rows.length ? `EyeOpen keyform ${rows.length}개 저장 대기` : "EyeOpen 값을 먼저 움직여주세요";
  render();
  draw();
}

function bindingTransformFromProjectOnly(project, targetId, parameterId, value) {
  const param = project.parameters.find((item) => item.id === parameterId);
  const bindings = project.keyform_bindings.filter((item) => item.target_id === targetId && item.parameter_id === parameterId);
  const keyframes = [
    { key_value: param.default, deltas: identityDeltas() },
    ...bindings.map((binding) => ({ key_value: binding.key_value, deltas: binding.deltas || identityDeltas() })),
  ].sort((a, b) => a.key_value - b.key_value);
  return sampleTransformKeyframes(keyframes, value);
}

function upsertKeyformOverrides(rows) {
  if (!rows.length) return;
  const byKey = new Map(state.rig.keyform_overrides.map((row) => [bindingKey(row), row]));
  for (const row of rows) byKey.set(bindingKey(row), row);
  state.rig.keyform_overrides = [...byKey.values()].sort((a, b) => bindingKey(a).localeCompare(bindingKey(b)));
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || data.stderr || `${url} ${response.status}`);
  return data;
}

async function saveRig() {
  try {
    state.rig.updated_at = new Date().toISOString();
    const result = await postJson("/api/mini-rig", { rig: state.rig });
    state.rigStatus = `저장됨: ${result.path}`;
  } catch (error) {
    state.rigStatus = `저장 실패: ${error.message}`;
  }
  render();
}

async function runEyeValidation() {
  state.rigStatus = "눈 검증 실행 중...";
  render();
  try {
    await saveRig();
    const result = await postJson("/api/validate-eye-modes", {});
    const report = result.report;
    const outside = (report?.modes || []).reduce((sum, row) => sum + (row.outside_changed_pixels || 0), 0);
    state.rigStatus = `눈 검증 ${report?.status || "UNKNOWN"} / ROI 밖 변화 ${outside}px`;
  } catch (error) {
    state.rigStatus = `눈 검증 실패: ${error.message}`;
  }
  render();
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
  window.__miniRig = () => state.rig;
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
