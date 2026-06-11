export function IssueTags({ tags, selectedTags, onChange }) {
  const root = document.createElement("div");
  root.className = "issue-tags";
  for (const rawTag of tags) {
    const tag = normalizeTag(rawTag);
    const label = document.createElement("label");
    label.className = selectedTags.includes(tag.code) ? "tag selected" : "tag";
    label.title = tag.help || tag.code;

    const input = document.createElement("input");
    input.type = "checkbox";
    input.checked = selectedTags.includes(tag.code);
    input.addEventListener("change", () => {
      const next = new Set(selectedTags);
      if (input.checked) next.add(tag.code);
      else next.delete(tag.code);
      onChange({ issue_tags: [...next].sort() });
    });

    const span = document.createElement("span");
    span.textContent = tag.label;
    label.append(input, span);
    root.append(label);
  }
  return root;
}

export function normalizeTag(tag) {
  if (typeof tag === "object" && tag) {
    return {
      code: tag.code,
      label: tag.label_ko || tag.label || tag.code,
      help: tag.help_ko || tag.help || tag.code,
    };
  }
  return {
    code: tag,
    label: tagLabel(tag),
    help: tag,
  };
}

export function tagLabel(tag) {
  const labels = {
    missing_part: "파츠 없음",
    bad_alpha: "테두리 지저분함",
    misaligned: "위치 안 맞음",
    style_mismatch: "그림체 다름",
    underpaint_missing: "밑색 없음",
    clipping_risk: "마스크 위험",
    draw_order_issue: "앞뒤 순서 문제",
    overhang_issue: "튀어나온 부분 문제",
    hair_mixed: "머리카락 섞임",
    skin_mixed: "피부 섞임",
    eye_white_mixed: "흰자 섞임",
    iris_mixed: "홍채/동공 섞임",
    line_cut: "선 잘림",
    alpha_dirty: "투명도 지저분함",
    bbox_too_tight: "영역 너무 타이트",
    missing_underpaint: "언더페인트 부족",
    wrong_shape: "형태 다름",
    semantic_too_coarse: "너무 뭉쳐 있음",
    depth_order_wrong: "앞뒤 순서 이상",
  };
  return labels[tag] || tag;
}
