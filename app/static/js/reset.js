// Reset flow: one page handles both sending email and setting new password

const $ = (id) => document.getElementById(id);
const show = (el, msg=null) => { if (msg!==null) el.textContent = msg; el.style.display = "block"; };
const hide = (el) => el.style.display = "none";

function hasRecoveryToken() {
  // Supabase sends tokens in URL hash after redirect: #access_token=...&refresh_token=...&type=recovery
  const hash = new URLSearchParams(window.location.hash.slice(1));
  return hash.get("type") === "recovery" && hash.get("access_token") && hash.get("refresh_token");
}

async function trySetSessionFromHash() {
  const hash = new URLSearchParams(window.location.hash.slice(1));
  const access_token = hash.get("access_token");
  const refresh_token = hash.get("refresh_token");
  if (!access_token || !refresh_token) return false;

  const { error } = await window.sb.auth.setSession({ access_token, refresh_token });
  return !error;
}

function switchToRequestMode() {
  $("title").textContent = "Reset password";
  $("subtitle").textContent = "Enter your email to receive a reset link.";
  $("request-form").style.display = "grid";
  $("set-form").style.display = "none";
}

function switchToSetMode() {
  $("title").textContent = "Set a new password";
  $("subtitle").textContent = "Enter your new password below.";
  $("request-form").style.display = "none";
  $("set-form").style.display = "grid";
}

async function main() {
  hide($("ok")); hide($("err"));
  // If the user came from the email link, set the recovery session and show the "set password" form
  if (hasRecoveryToken()) {
    const ok = await trySetSessionFromHash();
    if (ok) {
      switchToSetMode();
    } else {
      switchToRequestMode();
      show($("err"), "Recovery link invalid or expired. Request a new one.");
    }
  } else {
    switchToRequestMode();
  }
}

$("request-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  hide($("ok")); hide($("err"));
  const email = $("email")?.value?.trim();
  if (!email) return show($("err"), "Please enter your email.");
  const redirectTo = `${window.location.origin}/reset`;
  const { error } = await window.sb.auth.resetPasswordForEmail(email, { redirectTo });
  if (error) return show($("err"), error.message || "Could not send reset email.");
  show($("ok"), "Reset link sent. Check your inbox.");
});

$("set-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  hide($("ok")); hide($("err"));
  const p1 = $("new_password")?.value || "";
  const p2 = $("confirm_password")?.value || "";
  if (p1.length < 8) return show($("err"), "Password must be at least 8 characters.");
  if (p1 !== p2) return show($("err"), "Passwords do not match.");

  const { error } = await window.sb.auth.updateUser({ password: p1 });
  if (error) return show($("err"), error.message || "Could not update password.");

  show($("ok"), "Password updated. Redirecting to Login…");
  // Clear the hash and send user to login
  setTimeout(() => { window.location.href = "/login"; }, 1200);
});

main();
