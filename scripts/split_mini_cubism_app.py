#!/usr/bin/env python3
"""AUTORIG-RUNTIME-SPLIT-001: mini_cubism_app/src/app.js(1,673줄 모놀리스)를 ES 모듈로 분할한다.

방식: 플러시-레프트 최상위 선언 경계로 블록을 자른 뒤(중괄호 파싱 불필요),
함수→모듈 매핑에 따라 배치하고, import는 다른 모듈의 export 식별자 사용을
단어 경계 스캔으로 자동 계산한다. 모든 블록은 글자 그대로 이동한다 (코드 수정 0).

검증: node --check 전 모듈 + T3 스모크 + eye mode validator (무회귀).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT  # noqa: E402

APP = ROOT / "mini_cubism_app"
SRC = APP / "src" / "app.js"
OUT = APP / "src"

# 모듈 경로 → 소속 최상위 선언 이름들 (97개 함수 + 상수 전부 명시; 누락 시 에러)
MODULES: dict[str, list[str]] = {
    "core/state.js": ["state", "PARAM_LABELS", "PREVIEW_PARAMETER_GROUPS"],
    "ui/dom.js": ["app"],
    "core/utils.js": [
        "fetchJson", "postJson", "loadImages", "bboxCenter", "clamp", "lerp",
        "formatValue", "groupBy", "escapeHtml",
    ],
    "core/rig.js": [
        "normalizeRig", "partTransform", "primaryDeformerForPart", "deformerTransform",
        "bindingTransform", "sampleTransformKeyframes", "identityDeltas", "transformFromDeltas",
        "interpolateTransform", "identityTransform", "mergeTransform", "effectiveKeyformBindings",
        "bindingKey", "partOpacity", "eyeOpenDetailOpacity", "isNeutralVisualRepairKeyform",
        "shouldSuppressNeutralPart", "neutralActivationParametersForPart", "isEyeBallDetailPart",
        "parameterMoved", "sampleOpacityKeyframes", "setParameterValue",
        "resetOtherPreviewParameterGroups", "previewParameterGroup",
        "bindingTransformFromProjectOnly", "ensureEyeSocketCovers", "ensureEyeSocketCoverConfig",
        "inferredEyeSocketCoverBbox",
    ],
    "core/physics.js": [
        "initPhysicsState", "resetPhysics", "stepPhysics", "physicsTargetOffset",
        "physicsTransformForPart",
    ],
    "core/draw.js": [
        "draw", "drawPart", "drawClippedEyePart", "drawEyeSocketCovers", "drawSocketCoverShape",
        "drawEyeCoverEditor", "clippedByEyeWhite", "drawMeshes", "drawDeformers",
        "applyCanvasViewZoom", "defaultViewZoom",
    ],
    "ui/components.js": [
        "render", "Sidebar", "Stage", "Inspector", "ParameterControl", "hiddenPreviewParameters",
        "isPreviewParameterHidden", "ToggleButton", "Chip", "SmallButton", "ViewZoomControl",
        "setViewZoom", "SegmentButton", "NumberField", "RangeField", "syncParameterControls",
    ],
    "ui/rig_panel.js": [
        "RigPanel", "EyeCoverPanel", "selectedPart", "ensureRigEyeSelection", "editableMeshForPart",
        "ensureMeshOverride", "resetEyeCoverConfig", "previewSelectedEyeClosed",
        "previewBothEyesClosed", "saveMeshOverride", "resetMeshOverride", "captureEyeBallKeyform",
        "captureEyeOpenKeyform", "upsertKeyformOverrides", "saveRig", "runEyeValidation",
    ],
    "ui/pointer.js": [
        "canvasPoint", "onCanvasWheel", "onCanvasPointerDown", "onCanvasPointerMove",
        "onCanvasPointerUp", "onEyeCoverPointerDown", "onEyeCoverPointerMove", "hitEyeCover",
        "coverHandlePoints", "resizedCoverBbox",
    ],
    "probe.js": ["exposeAutomationApi"],
    "main.js": ["init", "__entry__"],
}

HEADER = {
    "core/state.js": "// 전역 상태와 파라미터 상수. UI/DOM 의존 없음.",
    "ui/dom.js": "// 앱 루트 DOM 참조.",
    "core/utils.js": "// 범용 헬퍼 (fetch/수학/문자열).",
    "core/rig.js": "// 리그 수학: 트랜스폼/키폼/불투명도/파라미터. DOM 의존 없음 — 서비스 플레이어가 그대로 쓴다.",
    "core/physics.js": "// 스프링-댐퍼 물리.",
    "core/draw.js": "// 캔버스 렌더러. #preview-canvas에 그린다 — 서비스 플레이어가 그대로 쓴다.",
    "ui/components.js": "// 에디터 UI 컴포넌트 (사이드바/스테이지/인스펙터/컨트롤).",
    "ui/rig_panel.js": "// 리그 편집 패널과 키폼 캡처/저장 액션.",
    "ui/pointer.js": "// 캔버스 포인터/휠 인터랙션.",
    "probe.js": "// 자동화/주입 API (__miniProbe, __miniSetParameters 등). T2/T3 계약.",
    "main.js": "// 엔트리포인트.",
}

DECL_RE = re.compile(r"^(?:async )?function (\w+)|^const (\w+)\b|^let (\w+)\b")


def main() -> int:
    lines = SRC.read_text(encoding="utf-8").splitlines()
    # 1. 최상위 선언 경계 수집
    boundaries: list[tuple[int, str]] = []  # (line_idx, name)
    for i, line in enumerate(lines):
        m = DECL_RE.match(line)
        if m:
            boundaries.append((i, next(g for g in m.groups() if g)))
        elif re.match(r"^init\(\);", line):
            boundaries.append((i, "__entry__"))
    # 2. 블록 슬라이스
    blocks: dict[str, str] = {}
    for idx, (start, name) in enumerate(boundaries):
        end = boundaries[idx + 1][0] if idx + 1 < len(boundaries) else len(lines)
        blocks[name] = "\n".join(lines[start:end]).rstrip() + "\n"
    # 3. 매핑 완전성 검사
    assigned = {name for names in MODULES.values() for name in names}
    missing = sorted(set(blocks) - assigned)
    extra = sorted(assigned - set(blocks))
    if missing or extra:
        print(f"매핑 불일치 — 미배정: {missing} / 존재안함: {extra}")
        return 1
    # 4. export 이름 → 모듈 맵
    owner: dict[str, str] = {}
    for module, names in MODULES.items():
        for name in names:
            if name != "__entry__":
                owner[name] = module
    # 5. 모듈별 파일 생성 (import 자동 계산)
    for module, names in MODULES.items():
        body = "\n".join(blocks[name] for name in names if name in blocks)
        needed: dict[str, set[str]] = {}
        for name, src_module in owner.items():
            if src_module == module:
                continue
            if re.search(rf"\b{re.escape(name)}\b", body):
                needed.setdefault(src_module, set()).add(name)
        depth = module.count("/")
        prefix = "./" if depth == 0 else "../" * depth
        imports = []
        for src_module in sorted(needed):
            rel_path = (prefix + src_module) if depth else ("./" + src_module)
            names_list = ", ".join(sorted(needed[src_module]))
            imports.append(f'import {{ {names_list} }} from "{rel_path}";')
        exports = [n for n in names if n != "__entry__"]
        parts = [HEADER.get(module, ""), ""]
        if imports:
            parts += imports + [""]
        parts.append(body)
        if exports:
            parts.append(f"\nexport {{ {', '.join(exports)} }};")
        out_path = OUT / module
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(parts) + "\n", encoding="utf-8")
        print(f"  {module}: {len(exports)} exports, {len(needed)} deps, {body.count(chr(10))} lines")
    print(f"blocks total: {len(blocks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
