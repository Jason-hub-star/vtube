export function IssueTags({ tags, selectedTags, onChange }) {
  const root = document.createElement("div");
  root.className = "issue-tags";
  for (const tag of tags) {
    const label = document.createElement("label");
    label.className = selectedTags.includes(tag) ? "tag selected" : "tag";
    label.title = tag;

    const input = document.createElement("input");
    input.type = "checkbox";
    input.checked = selectedTags.includes(tag);
    input.addEventListener("change", () => {
      const next = new Set(selectedTags);
      if (input.checked) next.add(tag);
      else next.delete(tag);
      onChange({ issue_tags: [...next].sort() });
    });

    const span = document.createElement("span");
    span.textContent = tagLabel(tag);
    label.append(input, span);
    root.append(label);
  }
  return root;
}

function tagLabel(tag) {
  return {
    hair_mixed: "머리카락 섞임",
    skin_mixed: "피부 섞임",
    eye_white_mixed: "흰자 섞임",
    iris_mixed: "홍채/동공 섞임",
    line_cut: "선 잘림",
    alpha_dirty: "투명도 지저분함",
    bbox_too_tight: "영역 너무 타이트",
    missing_underpaint: "언더페인트 부족",
    wrong_shape: "형태 다름",
  }[tag] || tag;
}
