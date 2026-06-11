#!/usr/bin/env node
/**
 * Build a positive CMO3 fixture that contains generated rig structures.
 *
 * This uses the cloned Stretchy Studio CMO3 writer as an external research
 * reference. The fixture is not a production model; it is a structural test
 * target for scripts/inspect_cmo3_structure.mjs.
 */

import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(HERE, '..');
const STRETCHY_ROOT = resolve(
  REPO_ROOT,
  'experiments/rigging-open-source-research-001/external_repos/stretchystudio',
);

const { generateCmo3 } = await import(
  `file://${STRETCHY_ROOT}/src/io/live2d/cmo3writer.js`
);

const TINY_PNG = new Uint8Array([
  137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 13, 73, 72, 68, 82,
  0, 0, 0, 1, 0, 0, 0, 1, 8, 6, 0, 0, 0, 31, 21, 196, 137,
  0, 0, 0, 13, 73, 68, 65, 84, 120, 156, 99, 252, 255, 255, 63, 0, 5,
  254, 2, 254, 167, 53, 129, 132, 0, 0, 0, 0, 73, 69, 78, 68, 174,
  66, 96, 130,
]);

function parseArgs(argv) {
  const args = {
    out: resolve(REPO_ROOT, 'experiments/cmo3-structure-fixture-001/rigged_positive_fixture.cmo3'),
  };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--out') args.out = resolve(REPO_ROOT, argv[++i]);
    else throw new Error(`unknown argument: ${arg}`);
  }
  return args;
}

function mkMesh(name, tag, cx, cy, w, h) {
  const x0 = cx - w / 2;
  const x1 = cx + w / 2;
  const y0 = cy - h / 2;
  const y1 = cy + h / 2;
  return {
    name,
    tag,
    partId: name,
    vertices: new Float32Array([x0, y0, x1, y0, x0, y1, x1, y1]),
    triangles: [0, 1, 2, 2, 1, 3],
    uvs: new Float32Array([0, 0, 1, 0, 0, 1, 1, 1]),
    pngData: TINY_PNG,
    pngPath: `${name}.png`,
    origin: { x: cx, y: cy },
  };
}

const args = parseArgs(process.argv.slice(2));
mkdirSync(dirname(args.out), { recursive: true });

const result = await generateCmo3({
  canvasW: 1000,
  canvasH: 1500,
  modelName: 'Cmo3StructurePositiveFixture',
  generateRig: true,
  generatePhysics: true,
  meshes: [
    mkMesh('Face', 'face', 500, 300, 200, 280),
    mkMesh('FrontHair', 'front hair', 500, 220, 260, 200),
    mkMesh('BackHair', 'back hair', 500, 350, 300, 400),
    mkMesh('Mouth', 'mouth', 500, 410, 90, 40),
    mkMesh('Neck', 'neck', 500, 520, 90, 160),
    mkMesh('Topwear', 'topwear', 500, 800, 400, 300),
    mkMesh('Bottomwear', 'bottomwear', 500, 1050, 350, 250),
  ],
  groups: [],
});

writeFileSync(args.out, Buffer.from(result.cmo3));
console.log(`[cmo3-fixture] wrote ${args.out}`);
