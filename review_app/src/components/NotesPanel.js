export function NotesPanel({ item, review, onChange, onSave, saveState }) {
  const root = document.createElement("section");
  root.className = "review-panel";

  const h2 = document.createElement("h2");
  h2.textContent = "검수 메모";

  const rules = document.createElement("div");
  rules.className = "rules";
  rules.append(ruleBlock("허용 픽셀", item.allowed_features), ruleBlock("섞이면 안 되는 것", item.forbidden_contamination));

  const textarea = document.createElement("textarea");
  textarea.placeholder = "짧은 메모: 예) 머리카락 픽셀이 속눈썹에 섞임";
  textarea.value = review.human_note || "";
  textarea.addEventListener("input", () => onChange({ human_note: textarea.value }));

  const saveRow = document.createElement("div");
  saveRow.className = "save-row";
  const save = document.createElement("button");
  save.type = "button";
  save.className = "primary";
  save.textContent = saveState === "saving" ? "저장 중..." : "검수 저장";
  save.disabled = saveState === "saving";
  save.addEventListener("click", onSave);
  const status = document.createElement("span");
  status.className = `save-state ${saveState}`;
  status.textContent = saveState === "saved" ? "저장됨" : saveState === "error" ? "저장 실패" : "";
  saveRow.append(save, status);

  root.append(h2, rules, textarea, saveRow);
  return root;
}

function ruleBlock(title, values = []) {
  const block = document.createElement("div");
  block.className = "rule-block";
  const strong = document.createElement("strong");
  strong.textContent = title;
  const text = document.createElement("p");
  text.textContent = values.map(labelRule).join(", ");
  block.append(strong, text);
  return block;
}

function labelRule(value) {
  return {
    "hidden skin fill behind face parts": "가려진 얼굴 피부 밑색",
    "rear hair mass only": "뒷머리 덩어리만",
    "body skin and torso base": "몸 피부와 몸통 베이스",
    "clothing pixels only": "의상 픽셀만",
    "neck skin only": "목 피부만",
    "visible face skin and face outline": "보이는 얼굴 피부와 얼굴 외곽",
    "left sclera only": "왼쪽 흰자만",
    "right sclera only": "오른쪽 흰자만",
    "left iris color only": "왼쪽 홍채 색만",
    "right iris color only": "오른쪽 홍채 색만",
    "left pupil only": "왼쪽 동공만",
    "right pupil only": "오른쪽 동공만",
    "left eye catchlight only": "왼쪽 눈 하이라이트만",
    "right eye catchlight only": "오른쪽 눈 하이라이트만",
    "upper lash line only": "윗속눈썹 선만",
    "lower lash line only": "아랫속눈썹 선만",
    "left brow only": "왼쪽 눈썹만",
    "right brow only": "오른쪽 눈썹만",
    "mouth outline and lip line only": "입 외곽선과 입술선만",
    "dark mouth cavity only": "어두운 입 안쪽만",
    "teeth only": "치아만",
    "tongue only": "혀만",
    "left side hair lock only": "왼쪽 옆머리 다발만",
    "right side hair lock only": "오른쪽 옆머리 다발만",
    "front bangs only": "앞머리만",
    "left animal ear outer fur only": "왼쪽 귀 바깥 털만",
    "right animal ear outer fur only": "오른쪽 귀 바깥 털만",
    "left animal ear inner shadow and color only": "왼쪽 귀 안쪽 색/그림자만",
    "right animal ear inner shadow and color only": "오른쪽 귀 안쪽 색/그림자만",
    "left white shoulder fur only": "왼쪽 흰 어깨 털만",
    "right white shoulder fur only": "오른쪽 흰 어깨 털만",
    "black choker band only": "검정 초커 밴드만",
    "gold ornaments only": "금색 장식만",
    "reference key-pose guide only": "키포즈 참고 이미지로만 사용",
    "visual comparison overlay only": "비교용 오버레이로만 사용",
    "production import pixels": "PSD production 픽셀",
    "guide overlay pixels": "가이드/오버레이 픽셀",
    hair: "머리카락",
    eyes: "눈",
    mouth: "입",
    clothes: "의상",
    face: "얼굴",
    neck: "목",
    front_hair: "앞머리",
    side_hair: "옆머리",
    back_hair: "뒷머리",
    skin: "피부",
    face_outline: "얼굴 외곽선",
    iris: "홍채",
    pupil: "동공",
    lash: "속눈썹",
    highlight: "하이라이트",
    eye_white: "흰자",
    brow: "눈썹",
    tongue: "혀",
    teeth: "치아",
    mouth_line: "입 라인",
    cropped_line: "잘린 선",
    eye: "눈",
    ear_inner: "귀 안쪽",
    ear_outer: "귀 바깥",
    accessory: "장식",
    gold_ornaments: "금색 장식",
    body: "몸통",
    choker: "초커",
  }[value] || value;
}
