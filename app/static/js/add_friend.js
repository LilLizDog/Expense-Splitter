// Add Friend page: save a friend using backend cookie auth only.

const $ = (id) => document.getElementById(id);

/**
 * Show status message under Username.
 * kind: "info" | "ok" | "error"
 */
function setMessage(msg, kind = "info") {
  const el = document.getElementById("af-message");
  if (!el) return;

  el.textContent = msg || "";
  el.classList.remove("af-message--ok", "af-message--error");

  if (!msg) return;

  if (kind === "error") {
    el.classList.add("af-message--error");
  } else if (kind === "ok") {
    el.classList.add("af-message--ok");
  }
}

/**
 * Enable / disable Save Friend button.
 */
function updateButtonDisabled() {
  const first = $("af-first-name")?.value.trim();
  const last = $("af-last-name")?.value.trim();
  const username = $("af-username")?.value.trim();
  const btn = $("af-save-btn");
  if (!btn) return;

  btn.disabled = !(first && last && username);
}

/**
 * Handle Save Friend click.
 */
async function handleSaveClick() {
  const first = $("af-first-name")?.value.trim() || "";
  const last = $("af-last-name")?.value.trim() || "";
  const username = $("af-username")?.value.trim() || "";
  const notes = $("af-notes")?.value.trim() || "";
  const btn = $("af-save-btn");

  setMessage("");

  if (!first || !last || !username) {
    setMessage("First name, last name, and username are required.", "error");
    return;
  }

  if (btn) btn.disabled = true;

  try {
    setMessage("Saving friend...");

    const resp = await fetch("/api/friends/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include", // send cookies to backend
      body: JSON.stringify({
        username: username,
        note: notes || `${first} ${last}`,
      }),
    });

    if (resp.status === 401) {
      setMessage("Not authenticated. Please log in and try again.", "error");
      if (btn) btn.disabled = false;
      return;
    }

    if (resp.status === 404) {
      setMessage("No user found with that username.", "error");
      if (btn) btn.disabled = false;
      return;
    }

    if (!resp.ok) {
      let detail = "";
      try {
        const data = await resp.json();
        if (typeof data.detail === "string") detail = data.detail;
      } catch {
        // ignore parse errors
      }
      console.error("Add friend error:", resp.status, detail);
      setMessage(detail || "Could not save friend. Try again.", "error");
      if (btn) btn.disabled = false;
      return;
    }

    // Success
    setMessage("Friend added.", "ok");
    window.location.href = "/friends";
  } catch (err) {
    console.error("Unexpected error while saving friend:", err);
    setMessage("Unexpected error. Please try again.", "error");
    if (btn) btn.disabled = false;
  }
}

/**
 * Wire up listeners.
 */
document.addEventListener("DOMContentLoaded", () => {
  const first = $("af-first-name");
  const last = $("af-last-name");
  const username = $("af-username");
  const notes = $("af-notes");
  const btn = $("af-save-btn");

  [first, last, username, notes].forEach((el) => {
    if (!el) return;
    el.addEventListener("input", () => {
      setMessage("");
      updateButtonDisabled();
    });
  });

  if (btn) {
    btn.addEventListener("click", handleSaveClick);
    updateButtonDisabled();
  } else {
    console.warn("Add Friend save button not found.");
  }
});
