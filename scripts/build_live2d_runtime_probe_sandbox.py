#!/usr/bin/env python3
"""Build an isolated Cubism Web Samples probe sandbox for selected models."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "live2d-strong-model-pattern-001"
OFFICIAL = ROOT / "experiments" / "reference-model-structure-001" / "official_github_samples" / "repos" / "live2d_cubism_web_samples"
DEFAULT_MANIFEST = EXPERIMENT / "reports" / "pilot_render_manifest.json"
SANDBOX = EXPERIMENT / "probe_sandbox"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--sandbox", type=Path, default=SANDBOX)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path | str | None) -> str | None:
    if path is None:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return p.resolve().as_posix()


def copy_tree(src: Path, dst: Path, ignore: set[str] | None = None) -> None:
    ignore = ignore or set()
    if dst.exists():
        shutil.rmtree(dst)

    def ignore_func(_dir: str, names: list[str]) -> set[str]:
        return {name for name in names if name in ignore}

    shutil.copytree(src, dst, ignore=ignore_func)


def copy_runtime(model: dict[str, Any], resources_dir: Path) -> dict[str, Any]:
    model3 = ROOT / model["local_paths"]["model3_json"]
    if not model3.exists():
        return {"safe_id": model["safe_id"], "status": "FAIL", "error": f"missing model3: {model3}"}
    src_dir = model3.parent
    dst_dir = resources_dir / model["safe_id"]
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    shutil.copytree(src_dir, dst_dir)
    safe_model3 = dst_dir / f"{model['safe_id']}.model3.json"
    shutil.copy2(model3, safe_model3)
    return {
        "safe_id": model["safe_id"],
        "name": model["name"],
        "status": "PASS",
        "source_runtime_dir": rel(src_dir),
        "sandbox_runtime_dir": rel(dst_dir),
        "sandbox_model3_json": rel(safe_model3),
    }


def copy_resource_root_files(src_resources: Path, dst_resources: Path) -> list[str]:
    copied = []
    for src in src_resources.iterdir():
        if not src.is_file():
            continue
        dst = dst_resources / src.name
        shutil.copy2(src, dst)
        copied.append(rel(dst) or dst.as_posix())
    return copied


def patch_lappdefine(path: Path, model_ids: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    start = text.index("export const ModelDir: string[] = [")
    end = text.index("];", start) + 2
    replacement = "export const ModelDir: string[] = [\n" + ",\n".join(f"  '{item}'" for item in model_ids) + "\n];"
    path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")


def patch_lappmodel(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "_probeParameterOverrides" not in text:
        text = text.replace(
            "export class LAppModel extends CubismUserModel {\n",
            "export class LAppModel extends CubismUserModel {\n"
            "  private _probeParameterOverrides: Map<number, number> = new Map();\n\n"
            "  private _probeDisableIdleMotion = false;\n\n"
            "  public probeSetDisableIdleMotion(value: boolean): void {\n"
            "    this._probeDisableIdleMotion = value;\n"
            "  }\n\n"
            "  public probeClearMotion(): void {\n"
            "    this._motionManager.stopAllMotions();\n"
            "  }\n\n"
            "  public probeClearParameterOverrides(): void {\n"
            "    this._probeParameterOverrides.clear();\n"
            "  }\n\n"
            "  public probeSetParameterOverrides(overrides: Array<{ index: number; value: number }>): void {\n"
            "    this._probeParameterOverrides.clear();\n"
            "    for (const item of overrides) {\n"
            "      this._probeParameterOverrides.set(item.index, item.value);\n"
            "    }\n"
            "  }\n\n"
            "  public probeParameterSnapshot(): Array<{ index: number; id: string; min: number; max: number; defaultValue: number; value: number }> {\n"
            "    const model = this.getModel();\n"
            "    if (!model) return [];\n"
            "    const out: Array<{ index: number; id: string; min: number; max: number; defaultValue: number; value: number }> = [];\n"
            "    for (let i = 0; i < model.getParameterCount(); i++) {\n"
            "      out.push({\n"
            "        index: i,\n"
            "        id: model.getParameterId(i).getString(),\n"
            "        min: model.getParameterMinimumValue(i),\n"
            "        max: model.getParameterMaximumValue(i),\n"
            "        defaultValue: model.getParameterDefaultValue(i),\n"
            "        value: model.getParameterValueByIndex(i),\n"
            "      });\n"
            "    }\n"
            "    return out;\n"
            "  }\n\n",
        )
    if "probeCoreSnapshot" not in text:
        text = text.replace(
            "  /**\n"
            "   * model3.jsonが置かれたディレクトリとファイルパスからモデルを生成する\n",
            "  public probeCoreSnapshot(): any {\n"
            "    const model = this.getModel() as any;\n"
            "    if (!model) return null;\n"
            "    const coreModel = model.getModel ? model.getModel() : null;\n"
            "    const toArray = (value: any): Array<any> => value ? Array.from(value) : [];\n"
            "    const boundsFromVertices = (vertices: Float32Array): any => {\n"
            "      if (!vertices || vertices.length < 2) return null;\n"
            "      let minX = Number.POSITIVE_INFINITY;\n"
            "      let minY = Number.POSITIVE_INFINITY;\n"
            "      let maxX = Number.NEGATIVE_INFINITY;\n"
            "      let maxY = Number.NEGATIVE_INFINITY;\n"
            "      for (let i = 0; i + 1 < vertices.length; i += 2) {\n"
            "        const x = vertices[i];\n"
            "        const y = vertices[i + 1];\n"
            "        if (x < minX) minX = x;\n"
            "        if (y < minY) minY = y;\n"
            "        if (x > maxX) maxX = x;\n"
            "        if (y > maxY) maxY = y;\n"
            "      }\n"
            "      return { minX, minY, maxX, maxY, width: maxX - minX, height: maxY - minY };\n"
            "    };\n"
            "    const parameters: Array<any> = [];\n"
            "    for (let i = 0; i < model.getParameterCount(); i++) {\n"
            "      const keyValues = coreModel?.parameters?.keyValues?.[i] ? toArray(coreModel.parameters.keyValues[i]) : [];\n"
            "      parameters.push({\n"
            "        index: i,\n"
            "        id: model.getParameterId(i).getString(),\n"
            "        min: model.getParameterMinimumValue(i),\n"
            "        max: model.getParameterMaximumValue(i),\n"
            "        defaultValue: model.getParameterDefaultValue(i),\n"
            "        value: model.getParameterValueByIndex(i),\n"
            "        type: coreModel?.parameters?.types?.[i] ?? null,\n"
            "        repeat: coreModel?.parameters?.repeats?.[i] ?? null,\n"
            "        keyCount: coreModel?.parameters?.keyCounts?.[i] ?? null,\n"
            "        keyValues,\n"
            "      });\n"
            "    }\n"
            "    const partParentIndices = model.getPartParentPartIndices ? toArray(model.getPartParentPartIndices()) : [];\n"
            "    const partOffscreenIndices = model.getPartOffscreenIndices ? toArray(model.getPartOffscreenIndices()) : [];\n"
            "    const parts: Array<any> = [];\n"
            "    for (let i = 0; i < model.getPartCount(); i++) {\n"
            "      parts.push({\n"
            "        index: i,\n"
            "        id: model.getPartId(i).getString(),\n"
            "        opacity: model.getPartOpacityByIndex(i),\n"
            "        parentPartIndex: partParentIndices[i] ?? -1,\n"
            "        offscreenIndex: partOffscreenIndices[i] ?? -1,\n"
            "      });\n"
            "    }\n"
            "    const drawableMaskCounts = model.getDrawableMaskCounts ? model.getDrawableMaskCounts() : [];\n"
            "    const drawableMasks = model.getDrawableMasks ? model.getDrawableMasks() : [];\n"
            "    const renderOrders = model.getRenderOrders ? model.getRenderOrders() : [];\n"
            "    const drawables: Array<any> = [];\n"
            "    for (let i = 0; i < model.getDrawableCount(); i++) {\n"
            "      const vertices = model.getDrawableVertexPositions(i);\n"
            "      drawables.push({\n"
            "        index: i,\n"
            "        id: model.getDrawableId(i).getString(),\n"
            "        textureIndex: model.getDrawableTextureIndex(i),\n"
            "        drawOrder: coreModel?.drawables?.drawOrders?.[i] ?? null,\n"
            "        renderOrder: renderOrders?.[i] ?? null,\n"
            "        opacity: model.getDrawableOpacity(i),\n"
            "        parentPartIndex: model.getDrawableParentPartIndex(i),\n"
            "        blendMode: model.getDrawableBlendMode(i),\n"
            "        colorBlend: model.getDrawableColorBlend ? model.getDrawableColorBlend(i) : null,\n"
            "        alphaBlend: model.getDrawableAlphaBlend ? model.getDrawableAlphaBlend(i) : null,\n"
            "        culling: model.getDrawableCulling(i),\n"
            "        invertedMask: model.getDrawableInvertedMaskBit(i),\n"
            "        maskCount: drawableMaskCounts?.[i] ?? 0,\n"
            "        masks: drawableMasks?.[i] ? toArray(drawableMasks[i]) : [],\n"
            "        vertexCount: model.getDrawableVertexCount(i),\n"
            "        vertexIndexCount: model.getDrawableVertexIndexCount(i),\n"
            "        vertexBounds: boundsFromVertices(vertices),\n"
            "        dynamicFlags: {\n"
            "          visible: model.getDrawableDynamicFlagIsVisible(i),\n"
            "          vertexPositionsDidChange: model.getDrawableDynamicFlagVertexPositionsDidChange(i),\n"
            "          visibilityDidChange: model.getDrawableDynamicFlagVisibilityDidChange(i),\n"
            "          opacityDidChange: model.getDrawableDynamicFlagOpacityDidChange(i),\n"
            "          renderOrderDidChange: model.getDrawableDynamicFlagRenderOrderDidChange(i),\n"
            "          blendColorDidChange: model.getDrawableDynamicFlagBlendColorDidChange(i),\n"
            "        },\n"
            "      });\n"
            "    }\n"
            "    const offscreenMaskCounts = model.getOffscreenMaskCounts ? model.getOffscreenMaskCounts() : [];\n"
            "    const offscreenMasks = model.getOffscreenMasks ? model.getOffscreenMasks() : [];\n"
            "    const offscreenOwnerIndices = model.getOffscreenOwnerIndices ? model.getOffscreenOwnerIndices() : [];\n"
            "    const offscreens: Array<any> = [];\n"
            "    const offscreenCount = model.getOffscreenCount ? model.getOffscreenCount() : 0;\n"
            "    for (let i = 0; i < offscreenCount; i++) {\n"
            "      offscreens.push({\n"
            "        index: i,\n"
            "        ownerIndex: offscreenOwnerIndices?.[i] ?? -1,\n"
            "        opacity: model.getOffscreenOpacity(i),\n"
            "        colorBlend: model.getOffscreenColorBlend ? model.getOffscreenColorBlend(i) : null,\n"
            "        alphaBlend: model.getOffscreenAlphaBlend ? model.getOffscreenAlphaBlend(i) : null,\n"
            "        maskCount: offscreenMaskCounts?.[i] ?? 0,\n"
            "        masks: offscreenMasks?.[i] ? toArray(offscreenMasks[i]) : [],\n"
            "        invertedMask: model.getOffscreenInvertedMask ? model.getOffscreenInvertedMask(i) : false,\n"
            "      });\n"
            "    }\n"
            "    return {\n"
            "      source: 'Cubism SDK for Web / Live2DCubismCore-backed Framework snapshot',\n"
            "      canvas: {\n"
            "        width: model.getCanvasWidth(),\n"
            "        height: model.getCanvasHeight(),\n"
            "        pixelsPerUnit: model.getPixelsPerUnit(),\n"
            "        raw: coreModel?.canvasinfo ? {\n"
            "          CanvasWidth: coreModel.canvasinfo.CanvasWidth,\n"
            "          CanvasHeight: coreModel.canvasinfo.CanvasHeight,\n"
            "          CanvasOriginX: coreModel.canvasinfo.CanvasOriginX,\n"
            "          CanvasOriginY: coreModel.canvasinfo.CanvasOriginY,\n"
            "          PixelsPerUnit: coreModel.canvasinfo.PixelsPerUnit,\n"
            "        } : null,\n"
            "      },\n"
            "      counts: {\n"
            "        parameters: parameters.length,\n"
            "        parts: parts.length,\n"
            "        drawables: drawables.length,\n"
            "        maskedDrawables: drawables.filter(item => item.maskCount > 0).length,\n"
            "        invertedMaskDrawables: drawables.filter(item => item.invertedMask).length,\n"
            "        offscreens: offscreens.length,\n"
            "        maskedOffscreens: offscreens.filter(item => item.maskCount > 0).length,\n"
            "      },\n"
            "      parameters,\n"
            "      parts,\n"
            "      drawables,\n"
            "      offscreens,\n"
            "    };\n"
            "  }\n\n"
            "  /**\n"
            "   * model3.jsonが置かれたディレクトリとファイルパスからモデルを生成する\n",
            1,
        )
    needle = "    this._model.update();\n"
    if "probeParameterOverrides" not in text[text.find("public update(): void"):text.find("public startMotion", text.find("public update(): void"))]:
        text = text.replace(
            needle,
            "    for (const [index, value] of this._probeParameterOverrides.entries()) {\n"
            "      this._model.setParameterValueByIndex(index, value, 1.0);\n"
            "    }\n\n"
            "    this._model.update();\n",
            1,
        )
    idle_block = (
        "    if (this._motionManager.isFinished()) {\n"
        "      // モーションの再生がない場合、待機モーションの中からランダムで再生する\n"
        "      this.startRandomMotion(\n"
        "        LAppDefine.MotionGroupIdle,\n"
        "        LAppDefine.PriorityIdle\n"
        "      );\n"
        "    } else {"
    )
    if idle_block in text:
        text = text.replace(
            idle_block,
            "    if (this._motionManager.isFinished()) {\n"
            "      // モーションの再生がない場合、待機モーションの中からランダムで再生する\n"
            "      if (!this._probeDisableIdleMotion) {\n"
            "        this.startRandomMotion(\n"
            "          LAppDefine.MotionGroupIdle,\n"
            "          LAppDefine.PriorityIdle\n"
            "        );\n"
            "      }\n"
            "    } else {",
            1,
        )
    path.write_text(text, encoding="utf-8")


def patch_manager(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "probeWaitReady" not in text:
        marker = "  public setViewMatrix(m: CubismMatrix44) {\n"
        injection = """
  public probeModelNames(): string[] {
    return LAppDefine.ModelDir;
  }

  public probeSwitchModel(index: number): void {
    this.changeScene(index);
  }

  public probeCurrentModelName(): string {
    return LAppDefine.ModelDir[this._sceneIndex];
  }

  public probeCurrentModel(): LAppModel | null {
    return this._models[0] || null;
  }

  public async probeWaitReady(timeoutMs = 10000): Promise<boolean> {
    const started = Date.now();
    while (Date.now() - started < timeoutMs) {
      const model = this.probeCurrentModel();
      if (model && model.getModel()) return true;
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    return false;
  }

  public probeClear(): void {
    const model = this.probeCurrentModel() as any;
    if (model?.probeSetDisableIdleMotion) model.probeSetDisableIdleMotion(true);
    if (model?.probeClearMotion) model.probeClearMotion();
    if (model?.probeClearParameterOverrides) model.probeClearParameterOverrides();
  }

  public probeParameters(): Array<{ index: number; id: string; min: number; max: number; defaultValue: number; value: number }> {
    const model = this.probeCurrentModel() as any;
    return model?.probeParameterSnapshot ? model.probeParameterSnapshot() : [];
  }

  public probeSetParameter(parameterId: string, position: 'min' | 'max' | 'default'): any {
    const model = this.probeCurrentModel() as any;
    if (!model?.probeParameterSnapshot || !model?.probeSetParameterOverrides) return null;
    const params = model.probeParameterSnapshot();
    const match = params.find((p: { id: string }) => p.id === parameterId);
    if (!match) return null;
    const value = position === 'min' ? match.min : position === 'max' ? match.max : match.defaultValue;
    model.probeSetParameterOverrides([{ index: match.index, value }]);
    return {
      id: match.id,
      index: match.index,
      position,
      value,
      min: match.min,
      max: match.max,
      defaultValue: match.defaultValue,
    };
  }

  public probeSetParameterValues(values: Record<string, number>): any {
    const model = this.probeCurrentModel() as any;
    if (!model?.probeParameterSnapshot || !model?.probeSetParameterOverrides) return null;
    const params = model.probeParameterSnapshot();
    const byId = new Map(params.map((p: { id: string }) => [p.id, p]));
    const applied: Array<any> = [];
    const missing: Array<string> = [];
    const overrides: Array<{ index: number; value: number }> = [];
    for (const parameterId in (values || {})) {
      const rawValue = values[parameterId];
      const match = byId.get(parameterId) as any;
      if (!match) {
        missing.push(parameterId);
        continue;
      }
      const value = Math.max(match.min, Math.min(match.max, Number(rawValue)));
      overrides.push({ index: match.index, value });
      applied.push({
        id: match.id,
        index: match.index,
        value,
        rawValue,
        min: match.min,
        max: match.max,
        defaultValue: match.defaultValue,
      });
    }
    model.probeSetParameterOverrides(overrides);
    return { applied, missing };
  }

  public probeCoreSnapshot(): any {
    const model = this.probeCurrentModel() as any;
    return model?.probeCoreSnapshot ? model.probeCoreSnapshot() : null;
  }

  public probeSetCategory(category: string, position: 'min' | 'max' | 'default'): Array<string> {
    const model = this.probeCurrentModel() as any;
    if (!model?.probeParameterSnapshot || !model?.probeSetParameterOverrides) return [];
    const params = model.probeParameterSnapshot();
    const match = (id: string): boolean => {
      const v = id.toLowerCase();
      if (category === 'eye') return v.indexOf('eye') >= 0;
      if (category === 'mouth') return v.indexOf('mouth') >= 0 || ['parama', 'parami', 'paramu', 'parame', 'paramo'].indexOf(v) >= 0;
      if (category === 'hair') return v.indexOf('hair') >= 0 || v.indexOf('kami') >= 0;
      if (category === 'body_angle') return v.indexOf('anglex') >= 0 || v.indexOf('angley') >= 0 || v.indexOf('anglez') >= 0 || v.indexOf('bodyangle') >= 0;
      if (category === 'arm') return v.indexOf('arm') >= 0 || v.indexOf('hand') >= 0 || v.indexOf('shoulder') >= 0;
      return false;
    };
    const matched = params.filter((p: { id: string }) => match(p.id));
    const overrides = matched.map((p: { index: number; min: number; max: number; defaultValue: number }) => ({
      index: p.index,
      value: position === 'min' ? p.min : position === 'max' ? p.max : p.defaultValue,
    }));
    model.probeSetParameterOverrides(overrides);
    return matched.map((p: { id: string }) => p.id);
  }

  public probeStartRepresentativeMotion(): string | null {
    const model = this.probeCurrentModel() as any;
    const setting = model?._modelSetting;
    if (!model || !setting) return null;
    const groupCount = setting.getMotionGroupCount();
    const groups: string[] = [];
    for (let i = 0; i < groupCount; i++) groups.push(setting.getMotionGroupName(i));
    const preferred = groups.find(g => g === LAppDefine.MotionGroupTapBody)
      || groups.find(g => g === LAppDefine.MotionGroupIdle)
      || groups[0];
    if (!preferred || setting.getMotionCount(preferred) <= 0) return null;
    if (model.probeSetDisableIdleMotion) model.probeSetDisableIdleMotion(false);
    model.startMotion(preferred, 0, LAppDefine.PriorityForce);
    return preferred;
  }

"""
        text = text.replace(marker, injection + marker)
    if "__vtubeProbe" not in text:
        text = text.replace(
            "    this._subdelegate = subdelegate;\n"
            "    this.changeScene(this._sceneIndex);\n",
            "    this._subdelegate = subdelegate;\n"
            "    this.changeScene(this._sceneIndex);\n"
            "    (window as any).__vtubeLive2DManager = this;\n"
            "    (window as any).__vtubeProbe = {\n"
            "      modelNames: () => this.probeModelNames(),\n"
            "      switchModel: (index: number) => this.probeSwitchModel(index),\n"
            "      currentModelName: () => this.probeCurrentModelName(),\n"
            "      waitReady: (timeoutMs?: number) => this.probeWaitReady(timeoutMs),\n"
            "      clear: () => this.probeClear(),\n"
            "      parameters: () => this.probeParameters(),\n"
            "      setParameter: (parameterId: string, position: 'min' | 'max' | 'default') => this.probeSetParameter(parameterId, position),\n"
            "      setParameterValues: (values: Record<string, number>) => this.probeSetParameterValues(values),\n"
            "      coreSnapshot: () => this.probeCoreSnapshot(),\n"
            "      setCategory: (category: string, position: 'min' | 'max' | 'default') => this.probeSetCategory(category, position),\n"
            "      startRepresentativeMotion: () => this.probeStartRepresentativeMotion(),\n"
            "    };\n",
            1,
        )
    path.write_text(text, encoding="utf-8")


def main() -> int:
    args = parse_args()
    manifest = load_json(args.manifest)
    sandbox_root = args.sandbox / manifest["kind"]
    src_demo = OFFICIAL / "Samples" / "TypeScript" / "Demo"
    dst_core = sandbox_root / "Core"
    dst_framework = sandbox_root / "Framework"
    dst_demo = sandbox_root / "Samples" / "TypeScript" / "Demo"
    dst_resources = sandbox_root / "Samples" / "Resources"

    if sandbox_root.exists():
        shutil.rmtree(sandbox_root)
    copy_tree(OFFICIAL / "Core", dst_core)
    copy_tree(OFFICIAL / "Framework", dst_framework, ignore={"node_modules"})
    copy_tree(src_demo, dst_demo, ignore={"node_modules", "public", "dist"})
    dst_resources.mkdir(parents=True, exist_ok=True)
    resource_root_files = copy_resource_root_files(OFFICIAL / "Samples" / "Resources", dst_resources)

    resources = []
    model_ids = []
    for model in manifest["models"]:
        if model["manifest_status"] != "PASS":
            resources.append({"safe_id": model["safe_id"], "status": "SKIPPED_MANIFEST_FAIL"})
            continue
        resources.append(copy_runtime(model, dst_resources))
        model_ids.append(model["safe_id"])

    patch_lappdefine(dst_demo / "src" / "lappdefine.ts", model_ids)
    patch_lappmodel(dst_demo / "src" / "lappmodel.ts")
    patch_manager(dst_demo / "src" / "lapplive2dmanager.ts")

    report = {
        "schema_version": 1,
        "manifest": rel(args.manifest),
        "kind": manifest["kind"],
        "sandbox_root": rel(sandbox_root),
        "demo_dir": rel(dst_demo),
        "model_ids": model_ids,
        "resource_root_files": resource_root_files,
        "resources": resources,
        "status": "PASS" if model_ids else "FAIL",
    }
    reports_dir = EXPERIMENT / "reports"
    write_json(reports_dir / f"{manifest['kind']}_runtime_probe_sandbox.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if model_ids else 1


if __name__ == "__main__":
    raise SystemExit(main())
