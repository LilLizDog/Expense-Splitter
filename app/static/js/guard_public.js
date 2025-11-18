// If user is already logged in, skip login/signup pages
const { data } = await window.sb.auth.getSession();
if (data?.session) window.location.href = "/dashboard";