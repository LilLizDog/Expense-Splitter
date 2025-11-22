// signup.js

const $ = (id) => document.getElementById(id);
const show = (el, msg=null) => { if (msg!==null) el.textContent = msg; el.style.display = "block"; };
const hide = (el) => el.style.display = "none";

async function handleSignup(e){
  e.preventDefault();
  hide($("signup-success"));
  hide($("signup-error"));

  const first = $("first_name")?.value?.trim() || "";
  const last = $("last_name")?.value?.trim() || "";
  const full = `${first} ${last}`.trim();
  const email = $("email")?.value?.trim() || "";
  const password = $("password")?.value || "";
  const confirm = $("confirm_password")?.value || "";
  const dob = $("dob")?.value || "";

  if(!full || !email || !password || !dob)
    return show($("signup-error"), "Please fill all required fields.");

  if(password !== confirm)
    return show($("signup-error"), "Passwords do not match.");

  const { error } = await window.sb.auth.signUp({
    email,
    password,
    options: {
      email_confirm: true,
      data: { full_name: full, first_name: first, last_name: last, dob }
    }
  });

  if (error) return show($("signup-error"), error.message || "Signup failed.");

  show($("signup-success"), "Account created. Redirecting...");
  setTimeout(() => window.location.href = "/login", 1500);
}

const form = document.querySelector("#signup-form");
if(form) form.addEventListener("submit", handleSignup);