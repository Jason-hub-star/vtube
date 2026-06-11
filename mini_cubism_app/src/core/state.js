// 전역 상태와 파라미터 상수. UI/DOM 의존 없음.

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
  rendererBackend: "canvas", // 'canvas' | 'pixi' (?renderer=pixi — PIXI-RENDER-001)
  pixiCanvas: null, // pixi 백엔드의 영속 캔버스 — render()가 DOM을 재구성해도 재부착
  pixiDraw: null, // draw_pixi.js가 주입 (draw.js ← draw_pixi 순환 임포트 방지)
  pixiExtract: null, // probe 픽셀 추출 훅 (WebGL 캔버스는 getContext('2d') 불가)
  rigStatus: "",
  rigTool: "mesh",
  selectedCoverSide: "L",
  draggedVertex: null,
  draggedCover: null,
  viewZoom: 0.42,
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
  ParamEyeSmile: "Eye Smile",
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
  eye: ["ParamEyeLOpen", "ParamEyeROpen", "ParamEyeBallX", "ParamEyeBallY", "ParamEyeSmile"],
  mouth: ["ParamMouthOpenY", "ParamMouthForm"],
  hair: ["ParamHairFront", "ParamHairSide", "ParamHairBack"],
};


export { state, PARAM_LABELS, PREVIEW_PARAMETER_GROUPS };
