// Login: create Supabase session and tell backend to set cookies, then go to /dashboard.

// Helper: get element by id
const $ = (id) => document.getElementById(id);

// Helper: show an error box with message
const show = (el, msg = null) => {
  if (!el) return;
  if (msg !== null) el.textContent = msg;
  el.style.display = "block";
};

// Helper: hide an element
const hide = (el) => {
  if (!el) return;
  el.style.display = "none";
};

// Handle login form submit
async function handleLogin(e) {
  e.preventDefault();

  const errorBox = $("login-error");
  hide(errorBox);

  const emailEl = $("email");
  const passwordEl = $("password");

  const email = emailEl?.value?.trim() || "";
  const password = passwordEl?.value || "";

  if (!email || !password) {
    show(errorBox, "Enter email and password.");
    return;
  }

  if (!window.sb || !window.sb.auth) {
    show(errorBox, "Auth client is not initialized. Please refresh the page.");
    return;
  }

  try {
    // Step 1: Supabase JS login so the client has a session
    const { data, error } = await window.sb.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      console.error("Supabase login error:", error);
      show(errorBox, error.message || "Login failed. Try again.");
      return;
    }

    console.debug("Supabase session after login:", data?.session);

    // Step 2: tell backend to set HttpOnly cookies using form-encoded data
    const form = new FormData();
    form.append("email", email);
    form.append("password", password);

    const res = await fetch("/auth/login", {
      method: "POST",
      body: form, // important: no JSON and no manual Content-Type header
    });

    if (!res.ok) {
      let msg = "Login failed on server. Try again.";

      try {
        const json = await res.json();
        if (typeof json.detail === "string") {
          msg = json.detail;
        }
      } catch {
        // ignore parse errors, keep default message
      }

      console.error("Backend /auth/login error:", res.status, msg);
      show(errorBox, msg);
      return;
    }

    // Step 3: everything succeeded → go to dashboard
    window.location.href = "/dashboard";
  } catch (err) {
    console.error("Unexpected login error:", err);
    show(errorBox, "Unexpected error. Please try again.");
  }
}

// Attach handler when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("form#login-form");
  if (!form) {
    console.warn("Login form not found");
    return;
  }
  form.addEventListener("submit", handleLogin);
});
