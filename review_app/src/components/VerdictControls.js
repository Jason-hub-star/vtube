export function VerdictControls({ review, saveState, onChange }) {
  const root = document.createElement("div");
  root.className = "verdict-block";
  const controls = document.createElement("div");
  controls.className = "verdict-controls";
  for (const verdict of ["O", "X", "REVISE", "REFERENCE_ONLY"]) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label(verdict);
    button.className = review.verdict === verdict ? `active ${verdict.toLowerCase()}` : "";
    button.addEventListener("click", () => onChange({ verdict }));
    controls.append(button);
  }
  const status = document.createElement("p");
  status.className = `auto-save-state ${saveState}`;
  status.textContent = saveStateLabel(saveState);
  root.append(controls, status);
  return root;
}

function label(verdict) {
  return {
    O: "좋아요",
    X: "다시 만들기",
    REVISE: "고쳐서 쓰기",
    REFERENCE_ONLY: "참고만",
  }[verdict];
}

function saveStateLabel(saveState) {
  return {
    idle: "버튼을 누르면 바로 저장됩니다.",
    unsaved: "바뀐 내용을 저장할게요...",
    saving: "저장 중...",
    saved: "저장됨",
    error: "저장 실패. 다시 눌러주세요.",
  }[saveState] || "버튼을 누르면 바로 저장됩니다.";
}
