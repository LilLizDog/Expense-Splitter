// Login: email+password → session in sessionStorage → go to /dashboard

const $ = (id) => document.getElementById(id);
const show = (el, msg=null) => { if (msg!==null) el.textContent = msg; el.style.display = "block"; };
const hide = (el) => el.style.display = "none";

async function handleLogin(e){
  e.preventDefault();
  hide($("login-error"));

  const email = $("email")?.value?.trim() || "";
  const password = $("password")?.value || "";
  if (!email || !password) return show($("login-error"), "Enter email and password.");

  const { error } = await window.sb.auth.signInWithPassword({ email, password });
  if (error) return show($("login-error"), error.message || "Login failed. Try again.");

  // success → dashboard
  window.location.href = "/dashboard";
}

// Attach to form
const form = document.querySelector("form#login-form") || document.querySelector("form");
if (form) form.addEventListener("submit", handleLogin);