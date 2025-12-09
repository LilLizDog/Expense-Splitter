// FILE: static/js/group.js
// Group detail page: load group, edit name/description, manage members, add member, leave group.


// Helper for JSON fetch with credentials.
async function fetchJson(url, options = {}) {
  const res = await fetch(url, {
    credentials: "include",
    headers: { Accept: "application/json", ...(options.headers || {}) },
    ...options,
  });

  if (!res.ok) {
    throw new Error(`HTTP ${res.status} for ${url}`);
  }

  return res.json();
}


// Pick best visible name.
function pickMemberName(u) {
  return (
    u.name ??
    u.full_name ??
    u.username ??
    u.email ??
    "Member"
  );
}


// Render members into UL.
function renderMembers(container, members) {
  if (!container) return;
  if (!members || !members.length) {
    container.innerHTML =
      '<li class="muted">No members found for this group.</li>';
    return;
  }
  container.innerHTML = "";
  members.forEach((u) => {
    const li = document.createElement("li");
    li.textContent = pickMemberName(u);
    container.appendChild(li);
  });
}


// Load friends for dropdown.
async function loadFriendsForDropdown(selectEl) {
  if (!selectEl) return;
  try {
    const resp = await fetch("/api/friends/", {
      credentials: "include",
      headers: { Accept: "application/json" },
    });
    if (!resp.ok) return;


    const data = await resp.json();
    const friends = Array.isArray(data.friends) ? data.friends : [];


    selectEl.innerHTML = "";
    const defaultOpt = document.createElement("option");
    defaultOpt.value = "";
    defaultOpt.textContent = "Select a friend";
    selectEl.appendChild(defaultOpt);


    friends.forEach((f) => {
      const opt = document.createElement("option");
      opt.value = f.id;
      opt.textContent = f.name || f.email || "(Friend)";
      selectEl.appendChild(opt);
    });
  } catch (err) {
    console.error("Error loading friends:", err);
  }
}


async function initGroupPage() {
  // Get group id from query string.
  const params = new URLSearchParams(window.location.search);
  let groupId = params.get("group_id");

  // Fallback to /group/<id> pattern if needed.
  if (!groupId) {
    const match = window.location.pathname.match(/\/group\/([^/]+)/);
    if (match) {
      groupId = match[1];
    }
  }


  if (!groupId) {
    window.location.href = "/groups";
    return;
  }


  const nameInput = document.getElementById("group-name-input");
  const descInput = document.getElementById("group-desc-input");
  const dateEl = document.getElementById("group-date");
  const membersEl = document.getElementById("group-members");
  const saveBtn = document.getElementById("group-save-btn");
  const addSelect = document.getElementById("group-add-member-select");
  const addBtn = document.getElementById("group-add-member-btn");
  const leaveBtn = document.getElementById("leave-group-btn");
  const tripInput = document.getElementById("trip-description");


  // Load group info.
  try {
    const group = await fetchJson(`/api/groups/${encodeURIComponent(groupId)}`);
    const nameEl = document.getElementById("group-name");
const descEl = document.getElementById("group-desc");


// Set displayed name/description
if (nameEl) nameEl.textContent = group.name ?? "Group";
if (descEl) descEl.textContent = group.description || "";


// Also load description into trip description textarea
const tripDescInput = document.getElementById("trip-description");
if (tripDescInput) tripDescInput.value = group.description || "";




    if (dateEl && group.created_at) {
      dateEl.textContent = new Date(group.created_at).toLocaleDateString();
    }
  } catch (err) {
    console.error("Failed to load group:", err);
    alert("Group not found.");
    window.location.href = "/groups";
    return;
  }


  // Load members.
  async function refreshMembers() {
    try {
      const data = await fetchJson(
        `/api/groups/${encodeURIComponent(groupId)}/members`
      );
      const members = Array.isArray(data?.members)
        ? data.members
        : data.data || [];
      renderMembers(membersEl, members);
    } catch (err) {
      console.error("Failed to load members:", err);
      if (membersEl) {
        membersEl.innerHTML =
          '<li class="muted">Error loading members.</li>';
      }
    }
  }
  await refreshMembers();


  // Load friends for dropdown.
  loadFriendsForDropdown(addSelect);


  // Save group (name + description).
  if (saveBtn) {
    saveBtn.addEventListener("click", async () => {
      const newName = nameEl ? nameEl.textContent.trim() : "";
      const newDesc = tripInput ? tripInput.value : null;


      if (!newName) {
        alert("Group name cannot be empty.");
        return;
      }


      try {
        const body = { name: newName, description: newDesc };
        const res = await fetch(
          `/api/groups/${encodeURIComponent(groupId)}`,
          {
            method: "PATCH",
            credentials: "include",
            headers: {
              Accept: "application/json",
              "Content-Type": "application/json",
            },
            body: JSON.stringify(body),
          }
        );


        if (!res.ok) {
          alert("Could not save changes.");
          return;
        }


        await res.json();
        alert("Group updated.");
      } catch (err) {
        console.error("Error updating group:", err);
        alert("Could not save changes.");
      }
    });
  }


  // Add member to group.
  if (addBtn && addSelect) {
    addBtn.addEventListener("click", async () => {
      const rawId = addSelect.value;
      if (!rawId) {
        alert("Select a friend to add.");
        return;
      }


      const friendLinkId = parseInt(rawId, 10);
      if (!Number.isFinite(friendLinkId)) {
        alert("Invalid friend.");
        return;
      }


      try {
        const res = await fetch(
          `/api/groups/${encodeURIComponent(groupId)}/members`,
          {
            method: "POST",
            credentials: "include",
            headers: {
              Accept: "application/json",
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ friend_link_id: friendLinkId }),
          }
        );


        if (!res.ok) {
          alert("Could not add this member.");
          return;
        }


        await refreshMembers();
      } catch (err) {
        console.error("Add member error:", err);
        alert("Could not add this member.");
      }
    });
  }


  // Leave group.
  if (leaveBtn) {
    leaveBtn.addEventListener("click", async () => {
      if (!confirm("Are you sure you want to leave this group?")) return;


      try {
        const res = await fetch(
          `/api/groups/${encodeURIComponent(groupId)}/leave`,
          {
            method: "POST",
            credentials: "include",
            headers: { Accept: "application/json" },
          }
        );


        if (!res.ok) {
          alert("Could not leave group.");
          return;
        }


        alert("You left the group.");
        window.location.href = "/groups";
      } catch (err) {
        console.error("Leave group error:", err);
        alert("Could not leave group.");
      }
    });
  }
}


document.addEventListener("DOMContentLoaded", initGroupPage);
