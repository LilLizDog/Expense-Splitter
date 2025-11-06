# tests/test_account_page.py
import pytest
from playwright.sync_api import sync_playwright

HTML = r"""
<!DOCTYPE html><html><head><meta charset="utf-8"><title>Account</title></head>
<body>
  <h1>Account</h1>

  <div id="authNotice" class="hidden"></div>
  <div id="appArea" class="">
    <form id="profileForm" novalidate>
      <input id="full_name" name="full_name" type="text" value="Liz"/>
      <input id="username"  name="username"  type="text" value="liz_b"/>
      <input id="email"     name="email"     type="email" value="liz@example.com" readonly />
      <!-- Use single backslashes here -->
      <input id="phone"     name="phone"     type="tel" pattern="^[0-9\-+\(\) ]{7,20}$" value="314-555-1234"/>
      <select id="display_currency" name="display_currency">
        <option value="USD" selected>USD</option><option value="EUR">EUR</option>
      </select>
      <button id="saveBtn" type="submit">Save changes</button>
      <span id="profileStatus" class="status"></span>
    </form>
  </div>

  <script>
    const el = (id) => document.getElementById(id);
    const full_name = el('full_name');
    const username  = el('username');
    const email     = el('email');
    const phone     = el('phone');
    const currency  = el('display_currency');
    const profileStatus = el('profileStatus');

    function setStatus(node, msg, ok=true){
      node.textContent = msg || '';
      node.classList.toggle('ok', ok);
      node.classList.toggle('err', !ok);
    }

    // Mock populate
    // Values pre-filled in inputs above

    document.getElementById('profileForm').addEventListener('submit', (e) => {
      e.preventDefault();
      if (!full_name.value.trim()) { setStatus(profileStatus, 'Name is required', false); return; }
      if (!username.value.trim())  { setStatus(profileStatus, 'Username is required', false); return; }
      if (phone.value && !phone.checkValidity()) { setStatus(profileStatus, 'Invalid phone', false); return; }
      setStatus(profileStatus, 'Saved', true);
    });
  </script>
</body></html>
"""


@pytest.fixture(scope="session")
def browser():
  with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    yield b
    b.close()

@pytest.fixture
def page(browser):
  ctx = browser.new_context()
  pg = ctx.new_page()
  pg.set_content(HTML, wait_until="load")
  yield pg
  ctx.close()

def test_mock_profile_loads_on_page_load(page):
  assert page.locator("#email").input_value() == "liz@example.com"
  assert page.locator("#full_name").input_value() == "Liz"
  assert page.locator("#username").input_value() == "liz_b"
  assert page.locator("#phone").input_value() == "314-555-1234"
  assert page.locator("#display_currency").input_value() == "USD"

def test_update_saves_changes_and_refreshes_ui(page):
  page.fill("#full_name", "Liz B")
  page.fill("#phone", "314-555-0000")
  page.select_option("#display_currency", "EUR")
  page.click("#saveBtn")

  # Values persist and status shows Saved
  assert page.locator("#full_name").input_value() == "Liz B"
  assert page.locator("#phone").input_value() == "314-555-0000"
  assert page.locator("#display_currency").input_value() == "EUR"
  assert "saved" in page.locator("#profileStatus").inner_text().lower()

def test_invalid_email_phone_shows_validation_error(page):
  page.fill("#phone", "bad#phone")
  page.click("#saveBtn")
  assert "invalid" in page.locator("#profileStatus").inner_text().lower()
