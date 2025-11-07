// If no session, redirect to login
(async () => {
  const { data } = await window.sb.auth.getSession();
  if (!data?.session) window.location.href = "/login";
})();
