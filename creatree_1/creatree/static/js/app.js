// Simple drag-to-reorder for the dashboard link list.
// Uses native HTML5 drag-and-drop; falls back silently if not supported.
document.addEventListener("DOMContentLoaded", () => {
  const list = document.getElementById("link-manager");
  if (!list) return;

  let dragged = null;

  list.querySelectorAll(".link-row").forEach((row) => {
    row.setAttribute("draggable", "true");

    row.addEventListener("dragstart", () => {
      dragged = row;
      row.classList.add("dragging");
    });

    row.addEventListener("dragend", () => {
      row.classList.remove("dragging");
      dragged = null;
      persistOrder();
    });

    row.addEventListener("dragover", (e) => {
      e.preventDefault();
      const bounding = row.getBoundingClientRect();
      const offset = e.clientY - bounding.top - bounding.height / 2;
      if (offset < 0 && row !== dragged) {
        list.insertBefore(dragged, row);
      } else if (row.nextSibling !== dragged && row !== dragged) {
        list.insertBefore(dragged, row.nextSibling);
      }
    });
  });

  function persistOrder() {
    const ids = Array.from(list.querySelectorAll(".link-row")).map((r) => r.dataset.id);
    const body = new URLSearchParams();
    ids.forEach((id) => body.append("order[]", id));

    fetch("/dashboard/links/reorder", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
  }
});
