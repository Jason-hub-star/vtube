#!/usr/bin/env node
/**
 * Inspect a Cubism .cmo3 CAFF archive and emit structure reports.
 *
 * This intentionally avoids image-specific part-name assumptions. It extracts
 * whatever parts, drawables, deformers, parameters, and keyform bindings exist
 * in the CMO3's main.xml and summarizes their structure for validation.
 */

import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, isAbsolute, join, relative, resolve } from 'node:path';
import { createInflateRaw } from 'node:zlib';

const REPO_ROOT = resolve(dirname(new URL(import.meta.url).pathname), '..');

const DEFAULT_STANDARD_PARAMS = [
  'ParamAngleX',
  'ParamAngleY',
  'ParamAngleZ',
  'ParamEyeLOpen',
  'ParamEyeROpen',
  'ParamEyeBallX',
  'ParamEyeBallY',
  'ParamMouthForm',
  'ParamMouthOpenY',
  'ParamBodyAngleX',
  'ParamBodyAngleY',
  'ParamBodyAngleZ',
  'ParamBreath',
  'ParamHairFront',
  'ParamHairSide',
  'ParamHairBack',
];

function usage() {
  return `usage:
  node scripts/inspect_cmo3_structure.mjs --experiment-id imagen-live2d-001
  node scripts/inspect_cmo3_structure.mjs --cmo3 /path/to/model.cmo3 --out-json /path/report.json

options:
  --experiment-id <id>        Uses experiments/<id>/cubism_mvp_rig.cmo3 by default.
  --cmo3 <path>               Explicit CMO3 path.
  --out-json <path>           JSON output path.
  --out-md <path>             Markdown output path.
  --dump-main-xml <path>      Debug: write extracted main.xml to this path.
  --required-param <id>       Add a required parameter check. Repeatable.
  --no-default-param-checks   Do not check the default standard Live2D parameter list.
`;
}

function parseArgs(argv) {
  const args = {
    experimentId: null,
    cmo3Path: null,
    outJson: null,
    outMd: null,
    dumpMainXml: null,
    requiredParams: [],
    useDefaultParamChecks: true,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = () => {
      if (i + 1 >= argv.length) throw new Error(`missing value for ${a}`);
      return argv[++i];
    };
    if (a === '--experiment-id') args.experimentId = next();
    else if (a === '--cmo3') args.cmo3Path = next();
    else if (a === '--out-json') args.outJson = next();
    else if (a === '--out-md') args.outMd = next();
    else if (a === '--dump-main-xml') args.dumpMainXml = next();
    else if (a === '--required-param') args.requiredParams.push(next());
    else if (a === '--no-default-param-checks') args.useDefaultParamChecks = false;
    else if (a === '-h' || a === '--help') {
      console.log(usage());
      process.exit(0);
    } else {
      throw new Error(`unknown argument: ${a}`);
    }
  }
  if (!args.cmo3Path && !args.experimentId) {
    throw new Error('provide --experiment-id or --cmo3');
  }
  if (!args.cmo3Path) {
    args.cmo3Path = join(REPO_ROOT, 'experiments', args.experimentId, 'cubism_mvp_rig.cmo3');
  }
  args.cmo3Path = resolvePath(args.cmo3Path);

  const inferredExperiment = args.experimentId || inferExperimentId(args.cmo3Path);
  if (!args.outJson) {
    if (inferredExperiment) {
      args.outJson = join(REPO_ROOT, 'experiments', inferredExperiment, 'reports', 'cmo3_structure_report.json');
    } else {
      args.outJson = join(dirname(args.cmo3Path), 'cmo3_structure_report.json');
    }
  }
  if (!args.outMd) {
    if (inferredExperiment) {
      args.outMd = join(REPO_ROOT, 'experiments', inferredExperiment, 'reports', 'cmo3_structure_report.md');
    } else {
      args.outMd = join(dirname(args.cmo3Path), 'cmo3_structure_report.md');
    }
  }
  args.outJson = resolvePath(args.outJson);
  args.outMd = resolvePath(args.outMd);
  if (args.dumpMainXml) args.dumpMainXml = resolvePath(args.dumpMainXml);
  args.experimentId = inferredExperiment;
  return args;
}

function resolvePath(p) {
  return isAbsolute(p) ? p : resolve(REPO_ROOT, p);
}

function inferExperimentId(cmo3Path) {
  const rel = relative(REPO_ROOT, cmo3Path);
  const parts = rel.split(/[\\/]/);
  return parts[0] === 'experiments' && parts[1] ? parts[1] : null;
}

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function readVarNumber(u8, pos, xorByte) {
  let val = 0;
  while (true) {
    if (pos >= u8.length) throw new Error('unexpected EOF while reading CAFF var number');
    const b = u8[pos++] ^ xorByte;
    val = (val << 7) | (b & 0x7f);
    if ((b & 0x80) === 0) break;
  }
  return { val, pos };
}

function readString(u8, pos, xorByte, decoder) {
  const lenRead = readVarNumber(u8, pos, xorByte);
  const len = lenRead.val;
  pos = lenRead.pos;
  if (pos + len > u8.length) throw new Error('unexpected EOF while reading CAFF string');
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) bytes[i] = u8[pos + i] ^ xorByte;
  return { str: decoder.decode(bytes), pos: pos + len };
}

async function inflateRawTolerant(bytes) {
  const chunks = [];
  const inflate = createInflateRaw();
  await new Promise((resolvePromise) => {
    inflate.on('data', c => chunks.push(c));
    inflate.on('end', resolvePromise);
    inflate.on('error', resolvePromise);
    inflate.end(bytes);
  });
  return Buffer.concat(chunks);
}

async function extractMainXml(cmo3Path) {
  const raw = readFileSync(cmo3Path);
  const u8 = Uint8Array.from(raw);
  const decoder = new TextDecoder();
  const magic = decoder.decode(u8.slice(0, 4));
  if (magic !== 'CAFF') {
    throw new Error(`not a CAFF archive: ${cmo3Path}`);
  }

  const dv = new DataView(u8.buffer, u8.byteOffset, u8.byteLength);
  const obfKey = dv.getInt32(14, false);
  const xorByte = obfKey & 0xff;

  let pos = 26;
  pos += 2; // preview marker
  pos += 2;
  pos += 2;
  pos += 2;
  pos += 8;
  pos += 4;
  pos += 8;

  const fileCount = dv.getInt32(pos, false) ^ obfKey;
  pos += 4;

  const maskLow = BigInt(obfKey) & 0xffffffffn;
  const maskHi = obfKey < 0 ? 0xffffffffn : (BigInt(obfKey) & 0xffffffffn);
  const mask64 = (maskHi << 32n) | maskLow;

  const fileEntries = [];
  for (let i = 0; i < fileCount; i++) {
    const pathRead = readString(u8, pos, xorByte, decoder);
    pos = pathRead.pos;
    const tagRead = readString(u8, pos, xorByte, decoder);
    pos = tagRead.pos;
    const rawStart = dv.getBigUint64(pos, false);
    const startPos = Number((rawStart ^ mask64) & 0xffffffffffffffffn);
    pos += 8;
    const fileLen = dv.getInt32(pos, false) ^ obfKey;
    pos += 4;
    const obfuscated = Boolean(dv.getUint8(pos) ^ xorByte);
    pos += 1;
    const compress = dv.getUint8(pos) ^ xorByte;
    pos += 1;
    pos += 8;
    fileEntries.push({
      path: pathRead.str,
      tag: tagRead.str,
      startPos,
      fileLen,
      obfuscated,
      compress,
    });
  }

  const mainEntry = fileEntries.find(e => e.path === 'main.xml');
  if (!mainEntry) throw new Error('main.xml entry not found in CMO3 CAFF table');

  let mainBytes = u8.slice(mainEntry.startPos, mainEntry.startPos + mainEntry.fileLen);
  if (mainEntry.obfuscated) {
    const out = new Uint8Array(mainBytes.length);
    for (let i = 0; i < mainBytes.length; i++) out[i] = mainBytes[i] ^ xorByte;
    mainBytes = out;
  }

  let xml;
  if (mainEntry.compress === 16) {
    xml = decoder.decode(mainBytes);
  } else {
    const zipDv = new DataView(mainBytes.buffer, mainBytes.byteOffset, mainBytes.byteLength);
    const sig = zipDv.getUint32(0, true);
    if (sig !== 0x04034b50) {
      throw new Error(`main.xml entry is not raw XML or ZIP, signature=0x${sig.toString(16)}`);
    }
    const method = zipDv.getUint16(8, true);
    const flags = zipDv.getUint16(6, true);
    const compSize = zipDv.getUint32(18, true);
    const fnLen = zipDv.getUint16(26, true);
    const extraLen = zipDv.getUint16(28, true);
    const contentStart = 30 + fnLen + extraLen;
    let compContent;
    if ((flags & 0x08) && compSize === 0) {
      const descOff = mainBytes.length - 16;
      const descSig = zipDv.getUint32(descOff, true);
      compContent = descSig === 0x08074b50 ? mainBytes.slice(contentStart, descOff) : mainBytes.slice(contentStart);
    } else {
      compContent = mainBytes.slice(contentStart, contentStart + compSize);
    }
    if (method === 0) xml = decoder.decode(compContent);
    else if (method === 8) xml = new TextDecoder().decode(await inflateRawTolerant(compContent));
    else throw new Error(`unsupported ZIP compression method for main.xml: ${method}`);
  }

  return {
    raw,
    xml,
    fileEntries,
    mainEntry,
    caff: {
      magic,
      obfKey,
      fileCount,
      mainXml: {
        path: mainEntry.path,
        tag: mainEntry.tag,
        compressedLength: mainEntry.fileLen,
        compression: mainEntry.compress,
        obfuscated: mainEntry.obfuscated,
        extractedBytes: Buffer.byteLength(xml, 'utf8'),
      },
    },
  };
}

function countDefinitions(xml, tagName) {
  return allMatches(xml, new RegExp(`<${tagName}\\b(?![^>]*\\bxs\\.ref=)`, 'g')).length;
}

function countReferences(xml, tagName) {
  return allMatches(xml, new RegExp(`<${tagName}\\b(?=[^>]*\\bxs\\.ref=)`, 'g')).length;
}

function allMatches(text, regex) {
  return Array.from(text.matchAll(regex));
}

function getAttr(tagText, name) {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = tagText.match(new RegExp(`${escaped}="([^"]*)"`));
  return match ? decodeXml(match[1]) : null;
}

function decodeXml(value) {
  return value
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&');
}

function textByName(block, tag, name) {
  const escapedName = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const re = new RegExp(`<${tag}\\b[^>]*\\bxs\\.n="${escapedName}"[^>]*>([\\s\\S]*?)<\\/${tag}>`);
  const m = block.match(re);
  return m ? decodeXml(m[1].trim()) : null;
}

function idstrByTag(block, tag, name = 'id') {
  const escapedName = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const re = new RegExp(`<${tag}\\b[^>]*\\bxs\\.n="${escapedName}"[^>]*\\bidstr="([^"]*)"`);
  const m = block.match(re);
  return m ? decodeXml(m[1]) : null;
}

function sourceBlocks(xml, tagName) {
  const blocks = [];
  const re = new RegExp(`<${tagName}\\b(?=[^>]*\\bxs\\.id=)([\\s\\S]*?)<\\/${tagName}>`, 'g');
  for (const match of xml.matchAll(re)) {
    const full = match[0];
    const open = full.slice(0, full.indexOf('>') + 1);
    blocks.push({
      tag: tagName,
      xsId: getAttr(open, 'xs.id'),
      xsIdx: getAttr(open, 'xs.idx'),
      localName: textByName(full, 's', 'localName'),
      idstr: null,
      sourceGuidRef: null,
      targetDeformerRef: refByName(full, 'CDeformerGuid', 'targetDeformerGuid'),
      parentPartRef: refByName(full, 'CPartGuid', 'parentGuid'),
      keyformGridRef: refByName(full, 'KeyformGridSource', 'keyformGridSource'),
      keyformCount: countNestedTag(full, 'KeyformOnGrid'),
      snippetHash: sha256(Buffer.from(full)).slice(0, 12),
    });
  }
  return blocks;
}

function refByName(block, tag, name) {
  const escapedName = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const re = new RegExp(`<${tag}\\b[^>]*\\bxs\\.n="${escapedName}"[^>]*\\bxs\\.ref="([^"]*)"`);
  const m = block.match(re);
  return m ? m[1] : null;
}

function ownGuidRefByTag(block, tag, excludedNames = []) {
  const excluded = new Set(excludedNames);
  const re = new RegExp(`<${tag}\\b(?![^>]*\\bxs\\.ref=)[^>]*\\bxs\\.id="([^"]+)"[^>]*>`, 'g');
  for (const match of block.matchAll(re)) {
    const open = match[0];
    const name = getAttr(open, 'xs.n');
    if (!name || !excluded.has(name)) return match[1];
  }
  const reversed = new RegExp(`<${tag}\\b(?![^>]*\\bxs\\.ref=)[^>]*\\bxs\\.n="([^"]+)"[^>]*\\bxs\\.id="([^"]+)"[^>]*>`, 'g');
  for (const match of block.matchAll(reversed)) {
    if (!excluded.has(decodeXml(match[1]))) return match[2];
  }
  return null;
}

function countNestedTag(block, tag) {
  return allMatches(block, new RegExp(`<${tag}\\b`, 'g')).length;
}

function extractPartSources(xml) {
  return sourceBlocks(xml, 'CPartSource').map(block => ({
    ...block,
    idstr: idstrBySourceId(block, xml, 'CPartSource', 'CPartId'),
    childRefCount: countChildGuidRefsForSource(xml, block.xsId, 'CPartSource'),
  }));
}

function extractArtMeshSources(xml) {
  return sourceBlocks(xml, 'CArtMeshSource').map(block => ({
    ...block,
    idstr: idstrBySourceId(block, xml, 'CArtMeshSource', 'CArtMeshId'),
    drawableIdstr: idstrBySourceId(block, xml, 'CArtMeshSource', 'CDrawableId'),
    vertexCount: extractFirstIntByName(getSourceFullBlock(xml, 'CArtMeshSource', block.xsId), 'pointCount'),
    triangleIndexCount: extractFirstFloatArrayCount(getSourceFullBlock(xml, 'CArtMeshSource', block.xsId), 'triangleIndices'),
  }));
}

function extractDeformerSources(xml, tagName, idTag) {
  return sourceBlocks(xml, tagName).map(block => ({
    ...block,
    idstr: idstrBySourceId(block, xml, tagName, idTag),
    sourceGuidRef: refByName(getSourceFullBlock(xml, tagName, block.xsId), 'CDeformerGuid', 'guid')
      || ownGuidRefByTag(getSourceFullBlock(xml, tagName, block.xsId), 'CDeformerGuid', ['targetDeformerGuid']),
    targetDeformerRef: block.targetDeformerRef,
    keyformCount: countSourceKeyforms(xml, tagName, block.xsId),
    col: extractFirstIntByName(getSourceFullBlock(xml, tagName, block.xsId), 'col'),
    row: extractFirstIntByName(getSourceFullBlock(xml, tagName, block.xsId), 'row'),
  }));
}

function getSourceFullBlock(xml, tagName, xsId) {
  if (!xsId) return '';
  const escaped = xsId.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const re = new RegExp(`<${tagName}\\b(?=[^>]*\\bxs\\.id="${escaped}")[\\s\\S]*?<\\/${tagName}>`);
  const m = xml.match(re);
  return m ? m[0] : '';
}

function idstrBySourceId(block, xml, tagName, idTag) {
  const full = getSourceFullBlock(xml, tagName, block.xsId);
  return idstrByTag(full, idTag);
}

function countSourceKeyforms(xml, tagName, xsId) {
  const full = getSourceFullBlock(xml, tagName, xsId);
  const keyformsList = full.match(/<carray_list\b[^>]*\bxs\.n="keyforms"[^>]*\bcount="(\d+)"/);
  if (keyformsList) return Number(keyformsList[1]);
  return countNestedTag(full, 'KeyformOnGrid');
}

function countChildGuidRefsForSource(xml, xsId, sourceTag) {
  const full = getSourceFullBlock(xml, sourceTag, xsId);
  const childList = full.match(/<carray_list\b[^>]*\bxs\.n="_childGuids"[^>]*\bcount="(\d+)"/);
  if (childList) return Number(childList[1]);
  return 0;
}

function extractFirstIntByName(block, name) {
  const value = textByName(block, 'i', name);
  return value === null ? null : Number(value);
}

function extractFirstFloatArrayCount(block, name) {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const m = block.match(new RegExp(`<float-array\\b[^>]*\\bxs\\.n="${escaped}"[^>]*\\bcount="(\\d+)"`));
  return m ? Number(m[1]) : null;
}

function extractParameterSources(xml) {
  const parameterIdsByRef = extractIdstrDefinitions(xml, 'CParameterId');
  const params = [];
  const re = /<CParameterSource\b([\s\S]*?)<\/CParameterSource>/g;
  let index = 0;
  for (const match of xml.matchAll(re)) {
    const full = match[0];
    const open = full.slice(0, full.indexOf('>') + 1);
    const idRef = refByName(full, 'CParameterId', 'id');
    const inlineId = idstrByTag(full, 'CParameterId');
    params.push({
      index,
      xsId: getAttr(open, 'xs.id'),
      xsIdx: getAttr(open, 'xs.idx'),
      id: inlineId || parameterIdsByRef.get(idRef) || idRef,
      idRef,
      localName: textByName(full, 's', 'name') || textByName(full, 's', 'localName'),
      min: numberByAnyName(full, ['min', 'minimumValue', 'minValue']),
      max: numberByAnyName(full, ['max', 'maximumValue', 'maxValue']),
      default: numberByAnyName(full, ['default', 'defaultValue']),
      snippetHash: sha256(Buffer.from(full)).slice(0, 12),
    });
    index++;
  }
  return params;
}

function extractIdstrDefinitions(xml, tagName) {
  const map = new Map();
  const re = new RegExp(`<${tagName}\\b(?![^>]*\\bxs\\.ref=)[^>]*\\bxs\\.id="([^"]+)"[^>]*\\bidstr="([^"]*)"`, 'g');
  for (const match of xml.matchAll(re)) {
    map.set(match[1], decodeXml(match[2]));
  }
  const reversedAttrOrder = new RegExp(`<${tagName}\\b(?![^>]*\\bxs\\.ref=)[^>]*\\bidstr="([^"]*)"[^>]*\\bxs\\.id="([^"]+)"`, 'g');
  for (const match of xml.matchAll(reversedAttrOrder)) {
    map.set(match[2], decodeXml(match[1]));
  }
  return map;
}

function numberByAnyName(block, names) {
  for (const name of names) {
    for (const tag of ['f', 'd', 'i']) {
      const value = textByName(block, tag, name);
      if (value !== null && value !== '') return Number(value);
    }
  }
  return null;
}

function extractLayerNames(xml) {
  const names = [];
  const re = /<CLayer\b(?=[^>]*\bxs\.id=)([\s\S]*?)<\/CLayer>/g;
  for (const match of xml.matchAll(re)) {
    const full = match[0];
    const open = full.slice(0, full.indexOf('>') + 1);
    names.push({
      xsId: getAttr(open, 'xs.id'),
      xsIdx: getAttr(open, 'xs.idx'),
      name: textByName(full, 's', 'name'),
      visible: textByName(full, 'b', 'isVisible'),
      opacity255: textByName(full, 'i', 'opacity255'),
    });
  }
  return names;
}

function extractKeyformBindings(xml) {
  const bindings = [];
  const re = /<KeyformBindingSource\b(?=[^>]*\bxs\.id=)([\s\S]*?)<\/KeyformBindingSource>/g;
  for (const match of xml.matchAll(re)) {
    const full = match[0];
    const open = full.slice(0, full.indexOf('>') + 1);
    bindings.push({
      xsId: getAttr(open, 'xs.id'),
      xsIdx: getAttr(open, 'xs.idx'),
      description: textByName(full, 's', 'description'),
      parameterRef: refByTag(full, 'CParameterGuid'),
      gridRef: refByTag(full, 'KeyformGridSource'),
      keyCount: extractArrayListCount(full, 'keys'),
    });
  }
  return bindings;
}

function refByTag(block, tag) {
  const m = block.match(new RegExp(`<${tag}\\b[^>]*\\bxs\\.ref="([^"]*)"`, 'm'));
  return m ? m[1] : null;
}

function extractArrayListCount(block, name) {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const m = block.match(new RegExp(`<array_list\\b[^>]*\\bxs\\.n="${escaped}"[^>]*\\bcount="(\\d+)"`));
  return m ? Number(m[1]) : null;
}

function buildAnalysis(xml, requiredParams) {
  const tags = [
    'CArtMeshSource',
    'CPartSource',
    'CWarpDeformerSource',
    'CRotationDeformerSource',
    'KeyformGridSource',
    'KeyformBindingSource',
    'CParameterSource',
    'CPhysicsSettingsSource',
    'CGlueSource',
    'CClippingMaskSource',
    'CClippingMaskGuid',
    'CInvertedMaskSource',
    'CLayer',
    'CLayerGroup',
    'CLayeredImage',
    'CImageResource',
    'GEditableMesh2',
  ];
  const counts = {};
  for (const tag of tags) {
    counts[tag] = {
      definitions: countDefinitions(xml, tag),
      references: countReferences(xml, tag),
    };
  }

  const parameters = extractParameterSources(xml);
  const parameterIds = parameters.map(p => p.id).filter(Boolean);
  const parameterSet = new Set(parameterIds);
  const requiredParameterPresence = {};
  for (const id of requiredParams) requiredParameterPresence[id] = parameterSet.has(id);

  const artMeshes = extractArtMeshSources(xml);
  const parts = extractPartSources(xml);
  const warpDeformers = extractDeformerSources(xml, 'CWarpDeformerSource', 'CDeformerId');
  const rotationDeformers = extractDeformerSources(xml, 'CRotationDeformerSource', 'CDeformerId');
  const keyformBindings = extractKeyformBindings(xml);
  const layers = extractLayerNames(xml);

  const checks = [];
  addCheck(checks, 'main_xml_extracted', 'PASS', 'main.xml was extracted from the CAFF archive.');
  addCheck(checks, 'artmesh_present', artMeshes.length > 0 ? 'PASS' : 'FAIL', `${artMeshes.length} CArtMeshSource definition(s) found.`);
  addCheck(checks, 'part_sources_present', parts.length > 0 ? 'PASS' : 'FAIL', `${parts.length} CPartSource definition(s) found.`);
  addCheck(checks, 'parameters_present', parameters.length > 0 ? 'PASS' : 'FAIL', `${parameters.length} CParameterSource definition(s) found.`);
  const missingRequired = Object.entries(requiredParameterPresence).filter(([, ok]) => !ok).map(([id]) => id);
  addCheck(
    checks,
    'required_parameters_present',
    missingRequired.length === 0 ? 'PASS' : 'WARN',
    missingRequired.length === 0
      ? `${requiredParams.length} configured parameter check(s) passed.`
      : `Missing configured parameter(s): ${missingRequired.join(', ')}`,
  );
  addCheck(
    checks,
    'warp_deformers_present',
    warpDeformers.length > 0 ? 'PASS' : 'WARN',
    `${warpDeformers.length} CWarpDeformerSource definition(s) found.`,
  );
  addCheck(
    checks,
    'rotation_deformers_present',
    rotationDeformers.length > 0 ? 'PASS' : 'WARN',
    `${rotationDeformers.length} CRotationDeformerSource definition(s) found.`,
  );
  addCheck(
    checks,
    'keyform_bindings_present',
    keyformBindings.length > 0 ? 'PASS' : 'WARN',
    `${keyformBindings.length} KeyformBindingSource definition(s) found.`,
  );

  const status = checks.some(c => c.status === 'FAIL')
    ? 'FAIL'
    : checks.some(c => c.status === 'WARN')
      ? 'WARN'
      : 'PASS';

  return {
    status,
    counts,
    checks,
    parameters: {
      count: parameters.length,
      ids: parameterIds,
      required_presence: requiredParameterPresence,
      sources: parameters,
    },
    parts: {
      count: parts.length,
      names: parts.map(p => p.localName || p.idstr).filter(Boolean),
      sources: parts,
    },
    art_meshes: {
      count: artMeshes.length,
      names: artMeshes.map(m => m.localName || m.idstr || m.drawableIdstr).filter(Boolean),
      sources: artMeshes,
    },
    deformers: {
      warp_count: warpDeformers.length,
      rotation_count: rotationDeformers.length,
      warp_names: warpDeformers.map(d => d.localName || d.idstr).filter(Boolean),
      rotation_names: rotationDeformers.map(d => d.localName || d.idstr).filter(Boolean),
      warp_sources: warpDeformers,
      rotation_sources: rotationDeformers,
    },
    keyforms: {
      grid_count: counts.KeyformGridSource.definitions,
      binding_count: keyformBindings.length,
      bindings: keyformBindings,
    },
    layers: {
      count: layers.length,
      names: layers.map(l => l.name).filter(Boolean),
      sources: layers,
    },
    interpretation: [
      'This report proves CMO3 structure presence, not visual motion quality.',
      'Parameter/keyform/deformer presence does not prove that the rig deforms well under extreme values.',
      'Use this as a stronger gate before runtime render and Cubism visual overhang validation.',
    ],
  };
}

function addCheck(checks, id, status, message) {
  checks.push({ id, status, message });
}

function makeReport({ args, raw, xml, caff, fileEntries, analysis }) {
  const generatedAt = new Date().toISOString();
  return {
    schema_version: 1,
    generated_at: generatedAt,
    tool: {
      name: 'inspect_cmo3_structure.mjs',
      repo_root: REPO_ROOT,
      note: 'Generic CMO3 structure inspector. No image-specific part names are hardcoded.',
    },
    experiment_id: args.experimentId,
    input: {
      cmo3_path: args.cmo3Path,
      cmo3_path_relative: relative(REPO_ROOT, args.cmo3Path),
      size_bytes: raw.length,
      sha256: sha256(raw),
    },
    caff,
    file_table: {
      count: fileEntries.length,
      paths_sample: fileEntries.slice(0, 40).map(e => e.path),
      main_xml_size_chars: xml.length,
    },
    ...analysis,
    outputs: {
      json: args.outJson,
      markdown: args.outMd,
    },
  };
}

function markdownReport(report) {
  const checks = report.checks.map(c => `| ${c.id} | ${c.status} | ${c.message} |`).join('\n');
  const counts = Object.entries(report.counts)
    .map(([tag, c]) => `| ${tag} | ${c.definitions} | ${c.references} |`)
    .join('\n');
  const params = report.parameters.ids.length
    ? report.parameters.ids.map(id => `- \`${id}\``).join('\n')
    : '- none';
  const partNames = report.parts.names.length
    ? report.parts.names.map(n => `- \`${n}\``).join('\n')
    : '- none';
  const artMeshNames = report.art_meshes.names.length
    ? report.art_meshes.names.map(n => `- \`${n}\``).join('\n')
    : '- none';
  const warpNames = report.deformers.warp_names.length
    ? report.deformers.warp_names.map(n => `- \`${n}\``).join('\n')
    : '- none';
  const rotationNames = report.deformers.rotation_names.length
    ? report.deformers.rotation_names.map(n => `- \`${n}\``).join('\n')
    : '- none';

  return `# CMO3 Structure Report

Generated: ${report.generated_at}

Status: **${report.status}**

Input:

- CMO3: \`${report.input.cmo3_path_relative}\`
- Size: ${report.input.size_bytes} bytes
- SHA256: \`${report.input.sha256}\`

## Checks

| Check | Status | Message |
|---|---:|---|
${checks}

## Structure Counts

| XML Source | Definitions | References |
|---|---:|---:|
${counts}

## Parameters

${params}

## Parts

${partNames}

## ArtMeshes

${artMeshNames}

## Warp Deformers

${warpNames}

## Rotation Deformers

${rotationNames}

## Interpretation

- This proves CMO3 structure presence, not final visual rig quality.
- It does not replace runtime render checks for keyform motion, draw order under motion, or overhang.
- Part and layer names are extracted dynamically from this CMO3; they are not image-specific hardcoded expectations.
`;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!existsSync(args.cmo3Path)) throw new Error(`CMO3 not found: ${args.cmo3Path}`);
  const requiredParams = [
    ...(args.useDefaultParamChecks ? DEFAULT_STANDARD_PARAMS : []),
    ...args.requiredParams,
  ];

  const { raw, xml, fileEntries, caff } = await extractMainXml(args.cmo3Path);
  if (args.dumpMainXml) {
    mkdirSync(dirname(args.dumpMainXml), { recursive: true });
    writeFileSync(args.dumpMainXml, xml);
  }
  const analysis = buildAnalysis(xml, requiredParams);
  const report = makeReport({ args, raw, xml, caff, fileEntries, analysis });

  mkdirSync(dirname(args.outJson), { recursive: true });
  mkdirSync(dirname(args.outMd), { recursive: true });
  writeFileSync(args.outJson, `${JSON.stringify(report, null, 2)}\n`);
  writeFileSync(args.outMd, markdownReport(report));

  console.log(`[cmo3-structure] ${report.status}`);
  console.log(`[cmo3-structure] json: ${args.outJson}`);
  console.log(`[cmo3-structure] md:   ${args.outMd}`);
}

main().catch(err => {
  console.error(`[cmo3-structure] ERROR: ${err.message}`);
  process.exit(1);
});
