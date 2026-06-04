export function VerdictControls({ review, onChange }) {
  const root = document.createElement("div");
  root.className = "verdict-controls";
  for (const verdict of ["O", "X", "REVISE", "REFERENCE_ONLY"]) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label(verdict);
    button.className = review.verdict === verdict ? `active ${verdict.toLowerCase()}` : "";
    button.addEventListener("click", () => onChange({ verdict }));
    root.append(button);
  }
  return root;
}

function label(verdict) {
  return {
    O: "O 통과",
    X: "X 실패",
    REVISE: "수정 필요",
    REFERENCE_ONLY: "참고용",
  }[verdict];
}
