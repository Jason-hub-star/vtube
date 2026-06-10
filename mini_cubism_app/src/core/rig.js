// 리그 수학: 트랜스폼/키폼/불투명도/파라미터. DOM 의존 없음 — 서비스 플레이어가 그대로 쓴다.

import { physicsTransformForPart } from "../core/physics.js";
import { PREVIEW_PARAMETER_GROUPS, state } from "../core/state.js";
import { clamp, groupBy, lerp } from "../core/utils.js";

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
  if (part.id.endsWith("_closed_lid") || part.id.endsWith("_closed_underpaint")) return 1;
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

function setParameterValue(parameterId, value) {
  const param = state.project?.parameters?.find((item) => item.id === parameterId);
  const numeric = Number(value);
  state.parameters[parameterId] = param ? clamp(numeric, param.min, param.max) : numeric;
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

function bindingTransformFromProjectOnly(project, targetId, parameterId, value) {
  const param = project.parameters.find((item) => item.id === parameterId);
  const bindings = project.keyform_bindings.filter((item) => item.target_id === targetId && item.parameter_id === parameterId);
  const keyframes = [
    { key_value: param.default, deltas: identityDeltas() },
    ...bindings.map((binding) => ({ key_value: binding.key_value, deltas: binding.deltas || identityDeltas() })),
  ].sort((a, b) => a.key_value - b.key_value);
  return sampleTransformKeyframes(keyframes, value);
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


export { normalizeRig, partTransform, primaryDeformerForPart, deformerTransform, bindingTransform, sampleTransformKeyframes, identityDeltas, transformFromDeltas, interpolateTransform, identityTransform, mergeTransform, effectiveKeyformBindings, bindingKey, partOpacity, eyeOpenDetailOpacity, isNeutralVisualRepairKeyform, shouldSuppressNeutralPart, neutralActivationParametersForPart, isEyeBallDetailPart, parameterMoved, sampleOpacityKeyframes, setParameterValue, resetOtherPreviewParameterGroups, previewParameterGroup, bindingTransformFromProjectOnly, ensureEyeSocketCovers, ensureEyeSocketCoverConfig, inferredEyeSocketCoverBbox };
