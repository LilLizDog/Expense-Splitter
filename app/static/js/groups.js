// FILE: static/js/groups.js
// Load groups from /api/groups and render them on the page.

// Update the "X total" labels at top and bottom.
function setTotals(count) {
  const text = `${count} total`;
  const top = document.getElementById("groups-total");
  const bottom = document.getElementById("groups-total-bottom");
  if (top) top.textContent = text;
  if (bottom) bottom.textContent = text;
}

// Show a simple message when there are no groups or on error.
function renderEmpty(message) {
  const list = document.getElementById("groups-list");
  if (!list) return;
  list.innerHTML = `<div class="groups-empty">${message}</div>`;
  setTotals(0);
}

// Call backend to delete a group and update the UI.
async function deleteGroup(groupId, rowEl) {
  if (!groupId) return;
  const confirmDelete = window.confirm("Delete this group? This cannot be undone.");
  if (!confirmDelete) return;

  try {
    const resp = await fetch(`/api/groups/${encodeURIComponent(groupId)}`, {
      method: "DELETE",
      headers: { "Accept": "application/json" },
      credentials: "include"
    });

    if (!resp.ok) {
      console.error("Delete group failed with status", resp.status);
      alert("Could not delete this group.");
      return;
    }

    if (rowEl && rowEl.parentElement) {
      rowEl.parentElement.removeChild(rowEl);
      const list = document.getElementById("groups-list");
      const remaining = list ? list.querySelectorAll(".group-row").length : 0;
      if (remaining === 0) {
        renderEmpty("You are not part of any groups yet.");
      } else {
        setTotals(remaining);
      }
    }
  } catch (err) {
    console.error("Error deleting group", err);
    alert("Could not delete this group.");
  }
}

// Render an array of group objects into the list container.
function renderGroups(groups) {
  const list = document.getElementById("groups-list");
  if (!list) return;

  if (!groups || !groups.length) {
    renderEmpty("You are not part of any groups yet.");
    return;
  }

  list.innerHTML = "";

  groups.forEach((g) => {
    const row = document.createElement("div");
    row.className = "group-row";

    // Make whole row navigate to the group detail page.
    row.addEventListener("click", () => {
      if (!g.id) return;
      window.location.href = `/group?group_id=${encodeURIComponent(g.id)}`;
    });

    const main = document.createElement("div");
    main.className = "group-row-main";

    const nameEl = document.createElement("div");
    nameEl.className = "group-name";
    nameEl.textContent = g.name || "Untitled group";

    const metaEl = document.createElement("div");
    metaEl.className = "group-meta";

    const memberCount = Array.isArray(g.members) ? g.members.length : 0;
    const created = g.created_at ? new Date(g.created_at) : null;
    const dateText = created
      ? created.toLocaleDateString(undefined, {
          year: "numeric",
          month: "short",
          day: "numeric"
        })
      : "";

    metaEl.textContent =
      `${memberCount} member` +
      (memberCount === 1 ? "" : "s") +
      (dateText ? ` • created ${dateText}` : "");

    main.appendChild(nameEl);
    main.appendChild(metaEl);
    row.appendChild(main);

    if (g.description) {
      const desc = document.createElement("div");
      desc.className = "group-meta";
      desc.textContent = g.description;
      row.appendChild(desc);
    }

    const actions = document.createElement("div");
    actions.style.marginTop = "6px";
    actions.style.display = "flex";
    actions.style.justifyContent = "flex-end";

    const deleteBtn = document.createElement("button");
    deleteBtn.type = "button";
    deleteBtn.textContent = "Delete";
    deleteBtn.className = "btn-outline";
    deleteBtn.style.fontSize = "0.8rem";

    deleteBtn.addEventListener("click", (evt) => {
      evt.stopPropagation();
      deleteGroup(g.id, row);
    });

    actions.appendChild(deleteBtn);
    row.appendChild(actions);

    list.appendChild(row);
  });

  setTotals(groups.length);
}

// Fetch groups from the backend and render them.
async function loadGroups() {
  try {
    const resp = await fetch("/api/groups", {
      method: "GET",
      credentials: "include"
    });

    if (!resp.ok) {
      renderEmpty("Could not load groups. Please try again.");
      return;
    }

    const data = await resp.json();
    const groups = Array.isArray(data) ? data : [];

    renderGroups(groups);
    wireSearch(groups);
  } catch (err) {
    renderEmpty("Could not load groups. Please try again.");
  }
}

// Simple search.
function wireSearch(groups) {
  const searchInput = document.getElementById("groups-search");
  const searchBtn = document.getElementById("groups-search-btn");
  const clearBtn = document.getElementById("groups-clear-btn");

  if (!searchInput || !searchBtn || !clearBtn) return;

  function applyFilter() {
    const q = searchInput.value.trim().toLowerCase();
    if (!q) {
      renderGroups(groups);
      return;
    }
    const filtered = groups.filter((g) => {
      const name = (g.name || "").toLowerCase();
      const desc = (g.description || "").toLowerCase();
      return name.includes(q) || desc.includes(q);
    });
    renderGroups(filtered);
  }

  searchBtn.addEventListener("click", applyFilter);

  clearBtn.addEventListener("click", () => {
    searchInput.value = "";
    renderGroups(groups);
  });
}

// Entry point.
(function initGroupsPage() {
  const list = document.getElementById("groups-list");
  if (list) {
    list.innerHTML = `<div class="groups-empty">Loading groups...</div>`;
  }
  setTotals(0);
  loadGroups();
})();
