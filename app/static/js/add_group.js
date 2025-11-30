// static/js/add_group.js
// Add group page: load friends, handle member selection, and submit group.

const $ = (id) => document.getElementById(id);

/**
 * Fetch JSON with cookies included.
 */
async function fetchJson(url, options = {}) {
  const res = await fetch(url, {
    credentials: "include",
    headers: { Accept: "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  return res.json();
}

/**
 * Normalize friends payload shape.
 */
function normalizeFriends(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.friends)) return data.friends;
  if (Array.isArray(data?.data)) return data.data;
  return [];
}

/**
 * Pick an id to send for each friend.
 * For now this falls back to numeric id, because that is what your
 * /api/friends/ endpoint is returning.
 */
function pickFriendId(f) {
  return (
    f.friend_user_id || // if you ever add this later
    f.user_id ||        // alternate auth field
    f.id                // current numeric friend row id
  );
}

/**
 * Pick display name.
 */
function pickName(f) {
  return (
    f.friend_name ||
    f.name ||
    f.username ||
    f.email ||
    "Friend"
  );
}

document.addEventListener("DOMContentLoaded", async () => {
  const form = $("addGroupForm");
  const nameEl = $("groupName");
  const dateEl = $("groupDate");
  const btn = $("memberBtn");
  const panel = $("memberPanel");
  const list = $("memberList");
  const search = $("memberSearch");
  const selectAll = $("memberSelectAll");
  const done = $("memberDone");
  const clear = $("memberClear");
  const hiddenWrap = $("memberHiddenInputs");
  const saveBtn = $("saveGroupBtn");
  const descEl = $("groupDesc");

  // Set date to today.
  const today = new Date();
  dateEl.value = today.toISOString().split("T")[0];

  let friends = [];
  let open = false;

  /**
   * Enable or disable Save button.
   */
  function updateSave() {
    saveBtn.disabled = !nameEl.value.trim();
  }

  /**
   * Selected ids from checkboxes.
   */
  function getChecked() {
    return [...list.querySelectorAll(".chk:checked")].map((c) => c.value);
  }

  /**
   * Mirror selected ids into hidden inputs.
   */
  function syncHidden() {
    hiddenWrap.innerHTML = "";
    getChecked().forEach((id) => {
      const i = document.createElement("input");
      i.type = "hidden";
      i.name = "member_ids";
      i.value = id;
      hiddenWrap.appendChild(i);
    });
  }

  /**
   * Show count label on button.
   */
  function syncSummary() {
    const count = getChecked().length;
    btn.textContent = count ? `${count} selected` : "Select members";
  }

  /**
   * Keep Select all checkbox in sync.
   */
  function syncSelectAll() {
    const all = [...list.querySelectorAll(".chk")];
    selectAll.checked = all.length > 0 && all.every((c) => c.checked);
  }

  /**
   * Render list of friends in dropdown.
   */
  function renderFriends() {
    if (!friends.length) {
      list.innerHTML =
        '<div class="muted" style="padding:8px;">No friends found</div>';
      btn.disabled = true;
      return;
    }

    list.innerHTML = friends
      .map((f) => {
        const id = pickFriendId(f);
        const name = pickName(f);
        return `
          <label class="dd-item">
            <input type="checkbox" class="chk" value="${id}">
            <span>${name}</span>
          </label>
        `;
      })
      .join("");

    btn.disabled = false;
    btn.textContent = "Select members";
  }

  // Load friends for picker.
  try {
    const data = await fetchJson("/api/friends/");
    const raw = normalizeFriends(data);
    friends = raw.filter((f) => pickFriendId(f));
    console.log("Friends rows for groups:", friends);
    renderFriends();
  } catch (err) {
    console.error("Error loading friends for groups:", err);
    btn.textContent = "Error loading friends";
    btn.disabled = true;
  }

  // Open or close dropdown.
  btn.addEventListener("click", () => {
    open = !open;
    panel.classList.toggle("hidden", !open);
    btn.setAttribute("aria-expanded", String(open));
  });

  // Close on outside click.
  document.addEventListener("click", (e) => {
    if (!open) return;
    if (e.target === btn || panel.contains(e.target)) return;
    panel.classList.add("hidden");
    open = false;
  });

  // Handle checkbox changes.
  list.addEventListener("change", () => {
    syncSelectAll();
    syncSummary();
    syncHidden();
  });

  // Handle Select all.
  selectAll.addEventListener("change", () => {
    list.querySelectorAll(".chk").forEach((c) => {
      c.checked = selectAll.checked;
    });
    syncSummary();
    syncHidden();
  });

  // Search filter.
  if (search) {
    search.addEventListener("input", () => {
      const q = search.value.toLowerCase();
      [...list.querySelectorAll(".dd-item")].forEach((item) => {
        const name = item.textContent.toLowerCase();
        item.style.display = name.includes(q) ? "" : "none";
      });
    });
  }

  // Clear all.
  if (clear) {
    clear.addEventListener("click", () => {
      list.querySelectorAll(".chk").forEach((c) => {
        c.checked = false;
      });
      syncSelectAll();
      syncSummary();
      syncHidden();
    });
  }

  // Done closes panel.
  if (done) {
    done.addEventListener("click", () => {
      panel.classList.add("hidden");
      open = false;
    });
  }

  // Enable Save when there is a name.
  nameEl.addEventListener("input", updateSave);
  updateSave();

  /**
   * Submit handler.
   * Sends member_ids as whatever id we get from /api/friends/.
   */
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const name = nameEl.value.trim();
    const description = descEl.value.trim();
    const member_ids = getChecked();

    if (!name) return;

    saveBtn.disabled = true;
    const previousLabel = saveBtn.textContent;
    saveBtn.textContent = "Saving...";

    try {
      const payload = { name, description, member_ids };
      console.log("Create group payload:", payload);

      const res = await fetch("/api/groups/", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const json = await res.json().catch(() => ({}));
      console.log("Create group response:", res.status, json);

      if (!res.ok) {
        const msg =
          json.detail ||
          json.error ||
          `Create failed (status ${res.status})`;
        throw new Error(msg);
      }

      window.location.href = "/groups";
    } catch (err) {
      console.error("Create group failed:", err);
      alert(err.message || "Error creating group");
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = previousLabel;
      updateSave();
    }
  });
});
