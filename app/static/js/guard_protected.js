// Simple Supabase based guard for protected pages.
// Redirects to /login if there is no active Supabase session.

document.addEventListener("DOMContentLoaded", async () => {
  // If Supabase client is missing, do not lock the user out accidentally.
  if (!window.sb || !window.sb.auth) {
    console.warn("Supabase client not available on protected page");
    return;
  }

  try {
    const { data, error } = await window.sb.auth.getSession();
    const session = data?.session;

    console.log("Protected page session check:", session ? "OK" : "NO SESSION", error || "");

    if (!session) {
      window.location.href = "/login";
    }
  } catch (err) {
    console.error("Error while checking session on protected page:", err);
    window.location.href = "/login";
  }
});
