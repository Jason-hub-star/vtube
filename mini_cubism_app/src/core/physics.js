// 스프링-댐퍼 물리.

import { draw } from "../core/draw.js";
import { identityTransform } from "../core/rig.js";
import { state } from "../core/state.js";
import { clamp } from "../core/utils.js";

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


export { initPhysicsState, resetPhysics, stepPhysics, physicsTargetOffset, physicsTransformForPart };
