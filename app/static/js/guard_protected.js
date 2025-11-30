// Guard for pages that require a Supabase session.

document.addEventListener("DOMContentLoaded", async () => {
  if (!window.sb || !window.sb.auth) {
    console.warn("Supabase client not available on protected page");
    return;
  }

  try {
    const { data, error } = await window.sb.auth.getSession();
    const session = data?.session;

    console.debug(
      "guard_protected session:",
      session ? "OK" : "NO SESSION",
      error || ""
    );

    if (!session) {
      window.location.href = "/login";
    }
  } catch (err) {
    console.error("Error while checking session on protected page:", err);
    window.location.href = "/login";
  }
});
