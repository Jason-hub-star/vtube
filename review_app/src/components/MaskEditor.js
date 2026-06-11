export function MaskEditor({ item, open, saveState, onOpenChange, onSaveMask }) {
  const root = document.createElement("section");
  root.className = `mask-editor ${open ? "open" : ""}`;

  const header = document.createElement("div");
  header.className = "mask-editor-header";
  const title = document.createElement("h2");
  title.textContent = "직접 마스크";
  const toggle = document.createElement("button");
  toggle.type = "button";
  toggle.className = open ? "active" : "";
  toggle.textContent = open ? "마스크 닫기" : "마스크 편집";
  toggle.addEventListener("click", () => onOpenChange(!open));
  header.append(title, toggle);
  root.append(header);

  if (!open) {
    const hint = document.createElement("p");
    hint.className = "mask-hint";
    hint.textContent = "필요한 영역만 직접 칠해서 manual 후보를 만들 수 있습니다.";
    root.append(hint);
    return root;
  }

  const canvas = document.createElement("canvas");
  canvas.className = "mask-canvas";
  canvas.width = 760;
  canvas.height = 520;

  const toolbar = document.createElement("div");
  toolbar.className = "mask-toolbar";
  const paintButton = toolButton("칠하기", true);
  const eraseButton = toolButton("지우개", false);
  const resetButton = toolButton("현재 알파로 시작", false);
  const clearButton = toolButton("전부 비우기", false);
  const saveButton = toolButton("마스크 저장", false, "primary");
  const brushLabel = document.createElement("label");
  brushLabel.textContent = "브러시";
  const brushInput = document.createElement("input");
  brushInput.type = "range";
  brushInput.min = "4";
  brushInput.max = "120";
  brushInput.value = "34";
  brushLabel.append(brushInput);
  toolbar.append(paintButton, eraseButton, brushLabel, resetButton, clearButton, saveButton);

  const status = document.createElement("p");
  status.className = `mask-status ${saveState}`;
  status.textContent = saveStateLabel(saveState);

  const guide = document.createElement("p");
  guide.className = "mask-guide";
  guide.textContent = "빨간 영역이 PSD 후보로 남을 영역입니다. 저장하면 새 manual 후보가 목록에 추가됩니다.";

  root.append(toolbar, canvas, guide, status);

  if (!item.image_path) {
    status.textContent = "이 항목은 마스크를 만들 원본 이미지가 없습니다.";
    status.className = "mask-status error";
    return root;
  }

  const session = createMaskSession({ canvas, item, status });
  paintButton.addEventListener("click", () => {
    session.mode = "paint";
    paintButton.classList.add("active");
    eraseButton.classList.remove("active");
  });
  eraseButton.addEventListener("click", () => {
    session.mode = "erase";
    eraseButton.classList.add("active");
    paintButton.classList.remove("active");
  });
  brushInput.addEventListener("input", () => {
    session.brushSize = Number(brushInput.value);
    session.render();
  });
  resetButton.addEventListener("click", () => session.resetFromAlpha());
  clearButton.addEventListener("click", () => session.clearMask());
  saveButton.addEventListener("click", async () => {
    saveButton.disabled = true;
    status.textContent = "마스크 저장 중...";
    try {
      await onSaveMask(item, session.maskDataUrl());
    } finally {
      saveButton.disabled = false;
    }
  });

  return root;
}

function createMaskSession({ canvas, item, status }) {
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  const canvasSize = item.canvas_size || [2048, 2048];
  const crop = cropBox(item);
  const canonical = new Image();
  const part = new Image();
  const mask = document.createElement("canvas");
  mask.width = canvasSize[0];
  mask.height = canvasSize[1];
  const maskCtx = mask.getContext("2d", { willReadFrequently: true });
  const state = {
    mode: "paint",
    brushSize: 34,
    drawing: false,
    loaded: false,
    render,
    resetFromAlpha,
    clearMask,
    maskDataUrl: () => mask.toDataURL("image/png"),
  };

  canonical.onload = markLoaded;
  part.onload = markLoaded;
  canonical.onerror = () => showError("기준 이미지를 불러오지 못했습니다.");
  part.onerror = () => showError("파츠 이미지를 불러오지 못했습니다.");
  canonical.src = item.canonical_path || item.image_path;
  part.src = item.image_path;

  canvas.addEventListener("pointerdown", (event) => {
    if (!state.loaded) return;
    state.drawing = true;
    canvas.setPointerCapture(event.pointerId);
    drawAt(event);
  });
  canvas.addEventListener("pointermove", (event) => {
    if (!state.drawing || !state.loaded) return;
    drawAt(event);
  });
  for (const eventName of ["pointerup", "pointercancel", "pointerleave"]) {
    canvas.addEventListener(eventName, () => {
      state.drawing = false;
    });
  }

  function markLoaded() {
    if (!canonical.complete || !part.complete) return;
    state.loaded = true;
    resetFromAlpha();
  }

  function resetFromAlpha() {
    maskCtx.clearRect(0, 0, mask.width, mask.height);
    const temp = document.createElement("canvas");
    temp.width = mask.width;
    temp.height = mask.height;
    const tempCtx = temp.getContext("2d", { willReadFrequently: true });
    tempCtx.drawImage(part, 0, 0, mask.width, mask.height);
    const source = tempCtx.getImageData(0, 0, mask.width, mask.height);
    const data = source.data;
    for (let index = 0; index < data.length; index += 4) {
      const alpha = data[index + 3];
      data[index] = 255;
      data[index + 1] = 255;
      data[index + 2] = 255;
      data[index + 3] = alpha > 10 ? 255 : 0;
    }
    maskCtx.putImageData(source, 0, 0);
    render();
  }

  function clearMask() {
    maskCtx.clearRect(0, 0, mask.width, mask.height);
    render();
  }

  function drawAt(event) {
    const point = eventToCanvasPoint(event);
    const fullX = crop.x + (point.x / canvas.width) * crop.w;
    const fullY = crop.y + (point.y / canvas.height) * crop.h;
    const radius = (state.brushSize / canvas.width) * crop.w;
    maskCtx.save();
    maskCtx.globalCompositeOperation = state.mode === "erase" ? "destination-out" : "source-over";
    maskCtx.fillStyle = "rgba(255,255,255,1)";
    maskCtx.beginPath();
    maskCtx.arc(fullX, fullY, radius, 0, Math.PI * 2);
    maskCtx.fill();
    maskCtx.restore();
    render(point);
  }

  function eventToCanvasPoint(event) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: ((event.clientX - rect.left) / rect.width) * canvas.width,
      y: ((event.clientY - rect.top) / rect.height) * canvas.height,
    };
  }

  function render(pointer = null) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#d9dde5";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    drawChecker(ctx, canvas.width, canvas.height);
    ctx.globalAlpha = 0.72;
    ctx.drawImage(canonical, crop.x, crop.y, crop.w, crop.h, 0, 0, canvas.width, canvas.height);
    ctx.globalAlpha = 0.86;
    ctx.drawImage(part, crop.x, crop.y, crop.w, crop.h, 0, 0, canvas.width, canvas.height);
    drawTintedMask(ctx, mask, crop, canvas.width, canvas.height);
    if (pointer) {
      ctx.strokeStyle = state.mode === "erase" ? "#ffffff" : "#ff324f";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(pointer.x, pointer.y, state.brushSize, 0, Math.PI * 2);
      ctx.stroke();
    }
  }

  function showError(message) {
    status.textContent = message;
    status.className = "mask-status error";
  }

  return state;
}

function drawTintedMask(ctx, mask, crop, width, height) {
  const overlay = document.createElement("canvas");
  overlay.width = width;
  overlay.height = height;
  const overlayCtx = overlay.getContext("2d");
  overlayCtx.drawImage(mask, crop.x, crop.y, crop.w, crop.h, 0, 0, width, height);
  overlayCtx.globalCompositeOperation = "source-in";
  overlayCtx.fillStyle = "#ff324f";
  overlayCtx.fillRect(0, 0, width, height);
  ctx.globalAlpha = 0.56;
  ctx.drawImage(overlay, 0, 0);
  ctx.globalAlpha = 1;
}

function cropBox(item) {
  const canvas = item.canvas_size || [2048, 2048];
  if (!item.bbox) return { x: 0, y: 0, w: canvas[0], h: canvas[1], canvas };
  const [x, y, w, h] = item.bbox;
  const pad = Math.max(80, Math.round(Math.max(w, h) * 0.32));
  const left = Math.max(0, x - pad);
  const top = Math.max(0, y - pad);
  const right = Math.min(canvas[0], x + w + pad);
  const bottom = Math.min(canvas[1], y + h + pad);
  return { x: left, y: top, w: right - left, h: bottom - top, canvas };
}

function drawChecker(ctx, width, height) {
  const size = 24;
  for (let y = 0; y < height; y += size) {
    for (let x = 0; x < width; x += size) {
      ctx.fillStyle = (x / size + y / size) % 2 === 0 ? "#eef1f5" : "#cfd5de";
      ctx.fillRect(x, y, size, size);
    }
  }
}

function toolButton(label, active = false, className = "") {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.className = [active ? "active" : "", className].filter(Boolean).join(" ");
  return button;
}

function saveStateLabel(saveState) {
  return {
    idle: "마스크를 칠한 뒤 저장하세요.",
    unsaved: "검수 변경사항이 아직 저장되지 않았습니다.",
    saving: "저장 중...",
    saved: "저장되었습니다. 새 manual 후보가 목록에 나타납니다.",
    error: "저장에 실패했습니다.",
  }[saveState] || "";
}
