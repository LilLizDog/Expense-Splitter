// Login: email+password → Supabase session → redirect to /dashboard

// Helper to get elements by id
const $ = (id) => document.getElementById(id);

// Show an error message in a given element
const show = (el, msg = null) => {
  if (!el) return;
  if (msg !== null) el.textContent = msg;
  el.style.display = "block";
};

// Hide a given element
const hide = (el) => {
  if (!el) return;
  el.style.display = "none";
};

// Handle login form submit
async function handleLogin(e) {
  e.preventDefault();

  const errorBox = $("login-error");
  hide(errorBox);

  const emailField = $("email");
  const passwordField = $("password");

  const email = emailField?.value?.trim() || "";
  const password = passwordField?.value || "";

  if (!email || !password) {
    show(errorBox, "Enter email and password.");
    return;
  }

  // Make sure Supabase client is available
  if (!window.sb || !window.sb.auth) {
    show(errorBox, "Auth client is not initialized. Please refresh the page.");
    return;
  }

  try {
    const { error } = await window.sb.auth.signInWithPassword({ email, password });
    if (error) {
      show(errorBox, error.message || "Login failed. Try again.");
      return;
    }

    // Successful login
    window.location.href = "/dashboard";
  } catch (err) {
    console.error("Login error:", err);
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
