#!/usr/bin/env python3
"""T3: 웹캠/재생 트래킹 스트림으로 Mini Cubism 런타임을 구동하는 드라이브 서버.

- `/`            Mini Cubism 프리뷰 앱 (mini_cubism_preview_server 재사용)
- `/drive`       드라이브 페이지: 좌측 웹캠 트래킹(MediaPipe) → 우측 iframe 모델 주입
- `/drive?replay=1[&speed=4][&auto=1]`  저장된 T1 스트림 재생 주입 (웹캠 불필요)
- `/api/replay-stream`  T1 raw 스트림 JSON

트래킹→Cubism 변환식은 T1 프로브 페이지(face_tracking_webcam_probe/index.html)의
rawChannels/convert를 그대로 이식했다. EyeOpen 0.27 / MouthOpenY 0.85 클램프는
v21 프로젝트 파라미터 범위에 내장되어 있어 앱 쪽 setParameterValue가 자동 적용한다.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from http import HTTPStatus
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import mini_cubism_preview_server as mcps  # noqa: E402

DEFAULT_PROJECT = (
    ROOT
    / "experiments/cubism-v2-new-character-002/model_edit_v21_supported_rig_smoke_preview/mini_cubism_diagnostic_project"
)
DEFAULT_STREAM = ROOT / "experiments/reference-model-structure-001/reports/face_tracking_webcam_probe_raw.json"

DRIVE_HTML = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>T3 웹캠 드라이브 — Mini Cubism</title>
<style>
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body { margin: 0; background: #f2f4f6; color: #191f28; font-family: -apple-system, "Apple SD Gothic Neo", sans-serif; }
  .layout { display: grid; grid-template-columns: 360px minmax(0, 1fr); gap: 16px; padding: 16px; height: 100vh; }
  .panel { background: #fff; border-radius: 20px; box-shadow: 0 1px 8px rgba(2, 32, 71, 0.06); padding: 18px; overflow: auto; }
  h1 { font-size: 18px; margin: 0 0 4px; }
  .sub { color: #6b7684; font-size: 12.5px; margin-bottom: 14px; }
  .cam { position: relative; border-radius: 14px; overflow: hidden; background: #111; aspect-ratio: 4/3; }
  video, #overlay { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; transform: scaleX(-1); }
  .row { display: flex; gap: 8px; margin: 14px 0; }
  button { flex: 1; border: 0; border-radius: 12px; padding: 12px 10px; font-size: 14px; font-weight: 700; cursor: pointer; background: #3182f6; color: #fff; }
  button.secondary { background: #eef3f8; color: #3182f6; }
  button:disabled { background: #e5e8eb; color: #b0b8c1; cursor: default; }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
  .chip { background: #f2f4f6; border-radius: 99px; padding: 5px 11px; font-size: 12px; color: #4e5968; }
  .chip b { color: #191f28; }
  .params { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
  .param { display: flex; justify-content: space-between; background: #f9fafb; border-radius: 10px; padding: 7px 10px; font-size: 11.5px; color: #6b7684; }
  .param b { font-variant-numeric: tabular-nums; color: #191f28; }
  iframe { width: 100%; height: 100%; border: 0; border-radius: 20px; background: #fff; box-shadow: 0 1px 8px rgba(2, 32, 71, 0.06); }
  .stage { display: flex; }
  .note { font-size: 12px; color: #8b95a1; margin-top: 10px; line-height: 1.5; }
</style>
</head>
<body>
<div class="layout">
  <section class="panel">
    <h1>T3 웹캠 드라이브</h1>
    <div class="sub" id="modeLabel">웹캠 모드 — 얼굴 움직임이 오른쪽 캐릭터를 움직여요</div>
    <div class="cam" id="camBox"><video id="video" autoplay playsinline muted></video><canvas id="overlay"></canvas></div>
    <div class="row">
      <button id="startBtn">시작할게요</button>
      <button id="calibrateBtn" class="secondary" disabled>중립 보정</button>
    </div>
    <div class="chips">
      <span class="chip">카메라 <b id="cameraState">꺼짐</b></span>
      <span class="chip">얼굴 <b id="faceState">-</b></span>
      <span class="chip">FPS <b id="fpsState">0</b></span>
      <span class="chip">적용 파라미터 <b id="appliedState">0</b></span>
      <span class="chip">프레임 <b id="frameState">0</b></span>
    </div>
    <div class="params" id="paramGrid"></div>
    <div class="note">EyeOpen 0.27(자연 감김)·MouthOpenY 0.85 클램프는 리그 프로젝트 범위로 자동 적용돼요.</div>
  </section>
  <section class="stage"><iframe id="model" src="/"></iframe></section>
</div>
<script type="module">
const qs = new URLSearchParams(location.search);
const REPLAY = qs.get("replay") === "1";
const AUTO = qs.get("auto") === "1";
const SPEED = Math.max(0.25, Number(qs.get("speed") || 1));

const video = document.getElementById("video");
const overlay = document.getElementById("overlay");
const ctx = overlay.getContext("2d");
const frame = document.getElementById("model");
const els = Object.fromEntries(
  ["startBtn", "calibrateBtn", "cameraState", "faceState", "fpsState", "appliedState", "frameState", "paramGrid", "modeLabel", "camBox"]
    .map((id) => [id, document.getElementById(id)])
);

const keyParams = [
  "ParamAngleX", "ParamAngleY", "ParamAngleZ", "ParamEyeLOpen", "ParamEyeROpen",
  "ParamEyeBallX", "ParamEyeBallY", "ParamMouthOpenY", "ParamMouthForm",
  "ParamBodyAngleX", "ParamBodyAngleY", "ParamBreath",
];
const paramEls = new Map();
for (const param of keyParams) {
  const card = document.createElement("div");
  card.className = "param";
  card.innerHTML = `<span>${param.replace("Param", "")}</span><b>0.00</b>`;
  els.paramGrid.appendChild(card);
  paramEls.set(param, card.querySelector("b"));
}

window.__driveReport = { mode: REPLAY ? "replay" : "webcam", frames_applied: 0, applied_counts: [], missing_union: [], last_outputs: null, done: false };

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, Number.isFinite(v) ? v : 0)); }
function normalizeCentered(v, lo, hi) { const m = Math.max(Math.abs(lo), Math.abs(hi)) || 1; return clamp(v / m, -1, 1); }
function remapDeadzone(v, dz, mx) { if (v <= dz) return 0; if (mx <= dz) return 1; return clamp((v - dz) / (mx - dz), 0, 1); }
function avg(...vs) { return vs.reduce((a, b) => a + b, 0) / vs.length; }

let neutral = null;
let latestRaw = null;

function rawChannels(result, nowMs) {
  const landmarks = result.faceLandmarks?.[0];
  const cats = result.faceBlendshapes?.[0]?.categories ?? [];
  const blends = new Map(cats.map((c) => [c.categoryName, c.score]));
  const b = (name) => blends.get(name) ?? 0;
  if (!landmarks) return null;
  const leftEye = landmarks[33] ?? landmarks[130];
  const rightEye = landmarks[263] ?? landmarks[359];
  const nose = landmarks[1] ?? landmarks[4];
  const chin = landmarks[152] ?? landmarks[175];
  const forehead = landmarks[10] ?? landmarks[9];
  if (!leftEye || !rightEye || !nose || !chin || !forehead) return null;
  const eyeDx = rightEye.x - leftEye.x;
  const eyeDy = rightEye.y - leftEye.y;
  const eyeWidth = Math.max(Math.abs(eyeDx), 0.04);
  const faceHeight = Math.max(Math.abs(chin.y - forehead.y), 0.12);
  const eyeCenterX = (leftEye.x + rightEye.x) / 2;
  const eyeCenterY = (leftEye.y + rightEye.y) / 2;
  const rollDeg = Math.atan2(eyeDy, eyeDx) * 180 / Math.PI;
  const yawDeg = clamp(((nose.x - eyeCenterX) / eyeWidth) * 42, -25, 25);
  const pitchDeg = clamp(((eyeCenterY - nose.y) / faceHeight) * 46, -20, 20);
  const gazeX = clamp(avg(b("eyeLookOutRight"), b("eyeLookInLeft")) - avg(b("eyeLookInRight"), b("eyeLookOutLeft")), -1, 1);
  const gazeY = clamp(avg(b("eyeLookUpLeft"), b("eyeLookUpRight")) - avg(b("eyeLookDownLeft"), b("eyeLookDownRight")), -1, 1);
  return {
    head_yaw_raw: yawDeg, head_pitch_raw: pitchDeg, head_roll_raw: rollDeg,
    head_yaw: yawDeg - (neutral?.head_yaw_raw ?? 0),
    head_pitch: pitchDeg - (neutral?.head_pitch_raw ?? 0),
    head_roll: rollDeg - (neutral?.head_roll_raw ?? 0),
    eyeBlinkLeft: b("eyeBlinkLeft"), eyeBlinkRight: b("eyeBlinkRight"),
    eye_gaze_x: gazeX - (neutral?.eye_gaze_x ?? 0),
    eye_gaze_y: gazeY - (neutral?.eye_gaze_y ?? 0),
    jawOpen: b("jawOpen"),
    mouthSmileLeft: b("mouthSmileLeft"), mouthSmileRight: b("mouthSmileRight"),
    mouthFrownLeft: b("mouthFrownLeft"), mouthFrownRight: b("mouthFrownRight"),
    time: (nowMs % 4000) / 4000,
  };
}

function convert(ch) {
  const headYaw = clamp(ch.head_yaw, -25, 25);
  const headPitch = clamp(ch.head_pitch, -20, 20);
  const headRoll = clamp(ch.head_roll, -25, 25);
  return {
    ParamAngleX: clamp(normalizeCentered(headYaw, -25, 25) * 30, -30, 30),
    ParamAngleY: clamp(normalizeCentered(headPitch, -20, 20) * 30, -30, 30),
    ParamAngleZ: clamp(normalizeCentered(headRoll, -25, 25) * 30, -30, 30),
    ParamEyeLOpen: clamp(1 - ch.eyeBlinkLeft, 0, 1),
    ParamEyeROpen: clamp(1 - ch.eyeBlinkRight, 0, 1),
    ParamEyeBallX: clamp(ch.eye_gaze_x, -1, 1),
    ParamEyeBallY: clamp(ch.eye_gaze_y, -1, 1),
    ParamMouthOpenY: clamp(remapDeadzone(ch.jawOpen, 0.08, 0.85), 0, 1),
    ParamMouthForm: clamp(avg(ch.mouthSmileLeft, ch.mouthSmileRight) - avg(ch.mouthFrownLeft, ch.mouthFrownRight), -1, 1),
    ParamBodyAngleX: clamp(normalizeCentered(headYaw, -25, 25) * 10 * 0.65, -10, 10),
    ParamBodyAngleY: clamp(normalizeCentered(headPitch, -20, 20) * 10 * 0.45, -10, 10),
    ParamBreath: clamp(0.5 + 0.5 * Math.sin(ch.time * Math.PI * 2), 0, 1),
  };
}

async function probe() {
  const started = performance.now();
  while (performance.now() - started < 20000) {
    const win = frame.contentWindow;
    if (win?.__miniProbe) {
      const ready = await win.__miniProbe.waitReady(15000);
      return ready ? win.__miniProbe : null;
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  return null;
}

function apply(outputs) {
  const win = frame.contentWindow;
  if (!win?.__miniProbe) return;
  if (win.__miniProject?.physics_profiles?.length) win.__miniStepPhysics?.(1 / 30); // 물리 스프링 라이브 스테핑 (프로파일 있을 때만 — 불필요한 리드로 방지)
  const result = win.__miniProbe.setParameterValues(outputs);
  const report = window.__driveReport;
  report.frames_applied += 1;
  report.applied_counts.push(result.applied.length);
  if (report.applied_counts.length > 4000) report.applied_counts.shift();
  for (const id of result.missing) if (!report.missing_union.includes(id)) report.missing_union.push(id);
  report.last_outputs = outputs;
  els.appliedState.textContent = String(result.applied.length);
  els.frameState.textContent = String(report.frames_applied);
  for (const param of keyParams) {
    const el = paramEls.get(param);
    if (el) el.textContent = (outputs[param] ?? 0).toFixed(2);
  }
}

// ---------- 재생 모드 ----------
async function runReplay() {
  els.modeLabel.textContent = `재생 모드 — 저장된 T1 스트림 주입 (배속 ${SPEED}x)`;
  els.camBox.style.display = "none";
  els.calibrateBtn.style.display = "none";
  els.startBtn.textContent = "재생 시작할게요";
  const stream = await fetch("/api/replay-stream").then((r) => r.json());
  const frames = (stream.frames || []).filter((f) => f.face_present && f.outputs);
  const start = async () => {
    els.startBtn.disabled = true;
    if (!(await probe())) { els.modeLabel.textContent = "모델 로드 실패"; return; }
    els.cameraState.textContent = "재생";
    const t0 = frames[0]?.t_ms ?? 0;
    const begin = performance.now();
    let i = 0;
    const tick = () => {
      const elapsed = (performance.now() - begin) * SPEED;
      // 밀린 프레임 중 마지막 것만 그린다 (중간 프레임 풀 리드로 방지 — 60fps 소스라 시각 동일)
      let last = -1;
      while (i < frames.length && (frames[i].t_ms - t0) <= elapsed) { last = i; i += 1; }
      if (last >= 0) {
        const skipped = Math.max(0, i - 1 - (window.__lastApplied ?? -1) - 1);
        apply(frames[last].outputs);
        const report = window.__driveReport;
        for (let s = 0; s < skipped; s++) { report.frames_applied += 1; report.applied_counts.push(report.applied_counts[report.applied_counts.length - 1] ?? 0); }
        window.__lastApplied = i - 1;
        els.frameState.textContent = String(report.frames_applied);
      }
      els.faceState.textContent = `${i}/${frames.length}`;
      if (i < frames.length) requestAnimationFrame(tick);
      else { window.__driveReport.done = true; els.modeLabel.textContent = "재생 완료"; }
    };
    requestAnimationFrame(tick);
  };
  els.startBtn.addEventListener("click", start);
  if (AUTO) start();
}

// ---------- 웹캠 모드 ----------
async function runWebcam() {
  const { FaceLandmarker, FilesetResolver } = await import("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14");
  let landmarker = null;
  let lastVideoTime = -1;
  let frames = 0;
  let fpsWindowStart = performance.now();

  async function loadLandmarker() {
    if (landmarker) return landmarker;
    const fileset = await FilesetResolver.forVisionTasks("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm");
    landmarker = await FaceLandmarker.createFromOptions(fileset, {
      baseOptions: {
        modelAssetPath: "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task",
        delegate: "CPU",
      },
      outputFaceBlendshapes: true,
      runningMode: "VIDEO",
      numFaces: 1,
    });
    return landmarker;
  }

  function drawDots(result) {
    overlay.width = video.videoWidth || overlay.clientWidth;
    overlay.height = video.videoHeight || overlay.clientHeight;
    ctx.clearRect(0, 0, overlay.width, overlay.height);
    const landmarks = result.faceLandmarks?.[0];
    if (!landmarks) return;
    ctx.fillStyle = "#3182f6";
    for (const idx of [1, 10, 33, 61, 152, 263, 291]) {
      const point = landmarks[idx];
      if (!point) continue;
      ctx.beginPath();
      ctx.arc(point.x * overlay.width, point.y * overlay.height, 4, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function loop() {
    if (video.readyState >= 2 && video.currentTime !== lastVideoTime) {
      lastVideoTime = video.currentTime;
      const now = performance.now();
      const result = landmarker.detectForVideo(video, now);
      drawDots(result);
      const channels = rawChannels(result, now);
      if (channels) {
        latestRaw = channels;
        els.faceState.textContent = "인식";
        apply(convert(channels));
      } else {
        els.faceState.textContent = "없음";
      }
      frames += 1;
      if (now - fpsWindowStart >= 1000) {
        els.fpsState.textContent = String(frames);
        frames = 0;
        fpsWindowStart = now;
      }
    }
    requestAnimationFrame(loop);
  }

  els.startBtn.addEventListener("click", async () => {
    try {
      els.startBtn.disabled = true;
      els.startBtn.textContent = "준비 중...";
      await loadLandmarker();
      if (!(await probe())) throw new Error("모델 로드 실패");
      const media = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false });
      video.srcObject = media;
      await video.play();
      els.cameraState.textContent = "켜짐";
      els.calibrateBtn.disabled = false;
      els.startBtn.textContent = "추적 중";
      requestAnimationFrame(loop);
    } catch (error) {
      els.cameraState.textContent = "실패";
      els.startBtn.disabled = false;
      els.startBtn.textContent = "다시 시도할게요";
      els.modeLabel.textContent = `카메라를 열 수 없어요: ${error.message}`;
    }
  });

  els.calibrateBtn.addEventListener("click", async () => {
    if (!latestRaw) return;
    const samples = [];
    const started = performance.now();
    els.calibrateBtn.textContent = "측정 중...";
    while (performance.now() - started < 1500) {
      if (latestRaw) samples.push(latestRaw);
      await new Promise((resolve) => setTimeout(resolve, 60));
    }
    const mean = (key) => samples.reduce((acc, item) => acc + (item[key] ?? 0), 0) / Math.max(samples.length, 1);
    neutral = {
      head_yaw_raw: mean("head_yaw_raw"),
      head_pitch_raw: mean("head_pitch_raw"),
      head_roll_raw: mean("head_roll_raw"),
      eye_gaze_x: mean("eye_gaze_x"),
      eye_gaze_y: mean("eye_gaze_y"),
    };
    els.calibrateBtn.textContent = "보정 완료";
  });
}

if (REPLAY) runReplay();
else runWebcam();
</script>
</body>
</html>
"""


class DriveHandler(mcps.MiniCubismHandler):
    server_version = "MiniCubismWebcamDrive/1.0"

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path == "/drive":
            data = DRIVE_HTML.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
            return
        if path == "/api/replay-stream":
            stream_path: Path = self.server.stream_path  # type: ignore[attr-defined]
            if not stream_path.exists():
                self.send_error(HTTPStatus.NOT_FOUND, "saved T1 stream missing")
                return
            self.serve_file(stream_path)
            return
        super().do_GET()


class DriveServer(mcps.MiniCubismServer):
    def __init__(self, address: tuple[str, int], handler, project: Path, stream_path: Path):
        super().__init__(address, handler, project)
        self.stream_path = stream_path.resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT)
    parser.add_argument("--stream", type=Path, default=DEFAULT_STREAM)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8060)
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--init-only", action="store_true", help="설정 검증만 하고 종료")
    args = parser.parse_args()

    project = args.project if args.project.is_absolute() else ROOT / args.project
    if not (project / "character.json").exists():
        raise SystemExit(f"Missing character.json in {project}")

    if args.init_only:
        print(json.dumps({"ok": True, "project": str(project), "stream": str(args.stream)}, ensure_ascii=False))
        return 0

    server = DriveServer((args.host, args.port), DriveHandler, project, args.stream)
    url = f"http://{args.host}:{args.port}/drive"
    print(f"T3 webcam drive: {url}")
    print(f"Project: {project}")
    if not args.no_open:
        subprocess.run(["open", url], check=False)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
