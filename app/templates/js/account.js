// templates/js/account.js
// Runs as a module inside <script type="module"> in account.html

const el = (id) => document.getElementById(id);
const show = (n) => n && n.classList.remove('hidden');
const hide = (n) => n && n.classList.add('hidden');

const authNotice   = el('authNotice');
const appArea      = el('appArea');
const full_name    = el('full_name');
const username     = el('username');
const email        = el('email');
const phone        = el('phone');
const currency     = el('display_currency');
const profileForm  = el('profileForm');
const profileStatus= el('profileStatus');
const logoutBtn    = el('logoutBtn');
const logoutStatus = el('logoutStatus');
const userIdLine   = el('userIdLine');

function setStatus(node, msg, ok = true) {
  node.textContent = msg || '';
  node.classList.toggle('ok', ok);
  node.classList.toggle('err', !ok);
}

function populateUser(u) {
  if (!u) return;
  email.value     = u.email || '';
  full_name.value = u.full_name || '';
  username.value  = u.username || '';
  phone.value     = u.phone || '';
  currency.value  = u.display_currency || 'USD';
  if (u.id) userIdLine.textContent = `User ID: ${u.id}`;
}

function hookMockMode() {
  hide(authNotice);
  show(appArea);
  populateUser(window.MOCK_USER);

  profileForm.addEventListener('submit', (e) => {
    e.preventDefault();
    if (!full_name.value.trim()) return setStatus(profileStatus, 'Name is required', false);
    if (!username.value.trim())  return setStatus(profileStatus, 'Username is required', false);
    if (phone.value && !phone.checkValidity()) return setStatus(profileStatus, 'Invalid phone', false);
    setStatus(profileStatus, 'Saved', true);
  });

  logoutBtn.addEventListener('click', () => {
    setStatus(logoutStatus, 'Logged out (mock)', true);
    show(authNotice); hide(appArea);
  });
}

async function hookRealMode() {
  let createClient;
  try {
    ({ createClient } = await import("https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm"));
  } catch (e) {
    console.error("Failed to load supabase-js:", e);
    show(authNotice); hide(appArea);
    return;
  }

  const url = window.SUPABASE_URL;
  const key = window.SUPABASE_KEY; // anon key only
  if (!url || !key) {
    console.error("Supabase keys missing in template");
    show(authNotice); hide(appArea);
    return;
  }

  const supabase = createClient(url, key);

  async function loadProfile(user) {
    const { data, error } = await supabase
      .from('profiles')
      .select('*')
      .eq('id', user.id)
      .single();

    if (error && error.code !== 'PGRST116') {
      setStatus(profileStatus, 'Failed to load profile', false);
      return;
    }
    populateUser({
      id: user.id,
      email: user.email,
      full_name: data?.full_name,
      username: data?.username,
      phone: data?.phone,
      display_currency: data?.display_currency || 'USD',
    });
  }

  async function saveProfile(user) {
    if (!full_name.value.trim()) return setStatus(profileStatus, 'Name is required', false);
    if (!username.value.trim())  return setStatus(profileStatus, 'Username is required', false);
    if (phone.value && !phone.checkValidity()) return setStatus(profileStatus, 'Invalid phone', false);

    const payload = {
      id: user.id,
      full_name: full_name.value.trim(),
      username: username.value.trim(),
      phone: phone.value.trim(),
      display_currency: currency.value,
    };

    const { error } = await supabase.from('profiles').upsert(payload);
    if (error) return setStatus(profileStatus, 'Save failed', false);
    setStatus(profileStatus, 'Saved', true);
  }

  const { data, error } = await supabase.auth.getSession();
  const user = data?.session?.user || null;
  if (error || !user) {
    show(authNotice); hide(appArea);
    return;
  }

  hide(authNotice); show(appArea);
  await loadProfile(user);

  profileForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    await saveProfile(user);
  });

  logoutBtn.addEventListener('click', async () => {
    const { error: signOutErr } = await supabase.auth.signOut();
    if (signOutErr) return setStatus(logoutStatus, 'Logout failed', false);
    setStatus(logoutStatus, 'Logged out', true);
    show(authNotice); hide(appArea);
  });
}

// boot
if (window.MOCK_MODE) {
  hookMockMode();
} else {
  hookRealMode();
}
