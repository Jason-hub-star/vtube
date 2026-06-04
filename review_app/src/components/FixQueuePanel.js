export function FixQueuePanel({ queue, onSelect }) {
  const root = document.createElement("section");
  root.className = "fix-queue";
  const h2 = document.createElement("h2");
  h2.textContent = `AI 수정 큐 ${queue.length}개`;
  root.append(h2);

  if (queue.length === 0) {
    const empty = document.createElement("p");
    empty.className = "empty-note";
    empty.textContent = "X 또는 수정 필요 파츠가 아직 없습니다.";
    root.append(empty);
    return root;
  }

  const list = document.createElement("div");
  list.className = "queue-list";
  for (const item of queue) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "queue-row";
    button.addEventListener("click", () => onSelect(item.part_id));

    const title = document.createElement("strong");
    title.textContent = `${item.part_id} · ${item.ko_name || ""}`;
    const tags = document.createElement("span");
    tags.textContent = labelTags(item.issue_tags || item.failure_tags || []);
    const note = document.createElement("small");
    note.textContent = item.human_note || item.suggested_generation_mode || "";

    button.append(title, tags, note);
    list.append(button);
  }
  root.append(list);
  return root;
}

function labelTags(tags) {
  if (!tags.length) return "태그 없음";
  const labels = {
    hair_mixed: "머리카락 섞임",
    skin_mixed: "피부 섞임",
    eye_white_mixed: "흰자 섞임",
    iris_mixed: "홍채/동공 섞임",
    line_cut: "선 잘림",
    alpha_dirty: "투명도 지저분함",
    bbox_too_tight: "영역 너무 타이트",
    missing_underpaint: "언더페인트 부족",
    wrong_shape: "형태 다름",
  };
  return tags.map((tag) => labels[tag] || tag).join(", ");
}
