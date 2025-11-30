// Handles loading and rendering the Friends page.
// Talks to /api/friends and /api/friends/groups.

document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("friends-search");
  const groupSelect = document.getElementById("friends-group-filter");
  const searchBtn = document.getElementById("friends-search-btn");
  const clearBtn = document.getElementById("friends-clear-btn");
  const addBtn = document.getElementById("friends-add-btn");
  const listEl = document.getElementById("friends-list");
  const totalEl = document.getElementById("friends-total");

  // Guard in case the template is not loaded correctly.
  if (!listEl || !totalEl) {
    console.warn("Friends page elements not found.");
    return;
  }

  // Build query string for the friends API call.
  function buildFriendsQuery() {
    const params = new URLSearchParams();
    const q = searchInput?.value?.trim();
    const group = groupSelect?.value?.trim();

    if (q) {
      params.set("q", q);
    }
    if (group) {
      params.set("group", group);
    }

    const qs = params.toString();
    return qs ? `?${qs}` : "";
  }

  // Load friend groups for the group filter dropdown.
  async function loadGroups() {
    if (!groupSelect) {
      return;
    }

    try {
      const resp = await fetch("/api/friends/groups");
      if (!resp.ok) {
        console.warn("Failed to load friend groups.");
        return;
      }

      const data = await resp.json();
      const groups = data.groups || [];

      groupSelect.innerHTML = "";
      const defaultOpt = document.createElement("option");
      defaultOpt.value = "";
      defaultOpt.textContent = "All groups";
      groupSelect.appendChild(defaultOpt);

      groups.forEach((g) => {
        const opt = document.createElement("option");
        opt.value = g;
        opt.textContent = g;
        groupSelect.appendChild(opt);
      });
    } catch (err) {
      console.error("Error loading friend groups:", err);
    }
  }

  // Render friends into the main list container.
  function renderFriends(friends) {
    listEl.innerHTML = "";

    if (!friends || friends.length === 0) {
      const empty = document.createElement("div");
      empty.className = "friends-empty";
      empty.textContent =
        "No friends match your filters. Try adjusting your search.";
      listEl.appendChild(empty);
    } else {
      friends.forEach((f) => {
        const row = document.createElement("div");
        row.className = "friend-row";

        const main = document.createElement("div");
        main.className = "friend-row-main";

        const name = document.createElement("span");
        name.className = "friend-name";
        name.textContent = f.name || "(No name)";

        const username = document.createElement("span");
        username.className = "friend-username";

        // Backend does not return username yet, so group is shown as a tag for now.
        if (f.group) {
          username.textContent = `· ${f.group}`;
        } else {
          username.textContent = "";
        }

        main.appendChild(name);
        if (username.textContent) {
          main.appendChild(username);
        }

        const email = document.createElement("div");
        email.className = "friend-email";
        email.textContent = f.email || "";

        row.appendChild(main);
        if (email.textContent) {
          row.appendChild(email);
        }

        listEl.appendChild(row);
      });
    }

    totalEl.textContent = `${friends.length} total`;
  }

  // Load friends from API and render them.
  async function loadFriends() {
    try {
      const qs = buildFriendsQuery();
      const resp = await fetch(`/api/friends/${qs}`);
      if (!resp.ok) {
        console.error("Failed to load friends:", resp.status);
        renderFriends([]);
        return;
      }

      const data = await resp.json();
      const friends = data.friends || [];

      friends.sort((a, b) => {
        const an = (a.name || "").toLowerCase();
        const bn = (b.name || "").toLowerCase();
        if (an < bn) return -1;
        if (an > bn) return 1;
        return 0;
      });

      renderFriends(friends);
    } catch (err) {
      console.error("Error loading friends:", err);
      renderFriends([]);
    }
  }

  // Attach handlers for search and clear buttons.
  if (searchBtn) {
    searchBtn.addEventListener("click", () => {
      loadFriends();
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      if (searchInput) searchInput.value = "";
      if (groupSelect) groupSelect.value = "";
      loadFriends();
    });
  }

  // Allow Enter key in the search box to trigger search.
  if (searchInput) {
    searchInput.addEventListener("keydown", (evt) => {
      if (evt.key === "Enter") {
        evt.preventDefault();
        loadFriends();
      }
    });
  }

  // Navigate to the Add Friend page when the button is clicked.
  if (addBtn) {
    addBtn.addEventListener("click", () => {
      window.location.href = "/friends/add";
    });
  }

  // Initial load for groups and friends.
  loadGroups();
  loadFriends();
});
