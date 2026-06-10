// 캔버스 렌더러. #preview-canvas에 그린다 — 서비스 플레이어가 그대로 쓴다.

import { deformerTransform, ensureEyeSocketCoverConfig, ensureEyeSocketCovers, inferredEyeSocketCoverBbox, partOpacity, partTransform } from "../core/rig.js";
import { state } from "../core/state.js";
import { bboxCenter, clamp } from "../core/utils.js";
import { coverHandlePoints } from "../ui/pointer.js";
import { editableMeshForPart } from "../ui/rig_panel.js";

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

let clipTempCanvas = null; // 클리핑용 임시캔버스 캐시 (매 호출 신규 할당이 프레임 끊김의 주범이었다)

function drawClippedEyePart(ctx, project, part, image, transform, opacity) {
  const pairs = state.rig?.clipping?.pairs || {};
  const maskPartId =
    Object.keys(pairs).find((key) => (pairs[key] || []).includes(part.id)) ||
    (part.id.startsWith("eye_L_") ? "eye_L_white" : "eye_R_white");
  const maskImage = state.images.get(maskPartId);
  if (!maskImage) return;
  if (!clipTempCanvas || clipTempCanvas.width !== project.canvas_size[0]) {
    clipTempCanvas = document.createElement("canvas");
    clipTempCanvas.width = project.canvas_size[0];
    clipTempCanvas.height = project.canvas_size[1];
  }
  const temp = clipTempCanvas;
  const tempCtx = temp.getContext("2d");
  tempCtx.globalCompositeOperation = "source-over"; // 이전 호출의 destination-in 잔류 해제
  tempCtx.globalAlpha = 1;
  tempCtx.clearRect(0, 0, temp.width, temp.height);
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

function applyCanvasViewZoom(canvas) {
  if (!state.project) return;
  canvas.style.width = `${Math.round(state.project.canvas_size[0] * state.viewZoom)}px`;
}

function defaultViewZoom() {
  return window.innerWidth <= 980 ? 0.18 : 0.42;
}


export { draw, drawPart, drawClippedEyePart, drawEyeSocketCovers, drawSocketCoverShape, drawEyeCoverEditor, clippedByEyeWhite, drawMeshes, drawDeformers, applyCanvasViewZoom, defaultViewZoom };
