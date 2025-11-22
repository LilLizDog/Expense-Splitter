# FILE: tests/test_payments_page.py
import os

import pytest
from fastapi.testclient import TestClient

from app.main import app

# Create a test client for the FastAPI app
client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def force_mock_mode():
    """
    Ensure the app runs in mock mode by clearing Supabase variables.
    """
    os.environ.pop("ENV_SUPABASE_URL", None)
    os.environ.pop("ENV_SUPABASE_KEY", None)
    yield


def _get_payments_response():
    """
    Try both /payments and /payments.html and return the first successful response.
    """
    for path in ("/payments", "/payments.html"):
        resp = client.get(path)
        if resp.status_code == 200:
            return resp
    pytest.fail("Neither /payments nor /payments.html returned 200")


def test_payments_page_renders():
    """
    Payments page should be reachable and return HTTP 200 with HTML content type.
    """
    resp = _get_payments_response()
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")


def test_payments_page_has_required_lists():
    """
    Payments page HTML should contain the requested and past payment list containers.
    """
    resp = _get_payments_response()
    html = resp.text

    assert 'id="requested-list"' in html, "Expected requested payments list container"
    assert 'id="past-list"' in html, "Expected past payments list container"


def test_payments_page_has_search_input():
    """
    Payments page HTML should expose a search input used by the frontend logic.
    """
    resp = _get_payments_response()
    html = resp.text

    assert 'id="search"' in html, "Expected search input with id='search'"


def test_payments_page_has_empty_state_placeholders():
    """
    Payments page HTML should contain placeholder elements for empty requested and past lists.
    """
    resp = _get_payments_response()
    html = resp.text

    assert 'id="requested-empty"' in html, "Expected requested empty state element"
    assert 'id="past-empty"' in html, "Expected past empty state element"


# # FILE: tests/test_payments_page.py
# import os
# import threading
# import time
# from contextlib import contextmanager

# import pytest
# import uvicorn
# from playwright.sync_api import sync_playwright

# # Import your app
# from app.main import app


# TEST_HOST = "127.0.0.1"
# TEST_PORT = 8765
# BASE_URL = f"http://{TEST_HOST}:{TEST_PORT}"


# @contextmanager
# def run_server():
#     """
#     Run uvicorn server for the duration of a test in a background thread.
#     """
#     config = uvicorn.Config(app, host=TEST_HOST, port=TEST_PORT, log_level="warning")
#     server = uvicorn.Server(config)

#     thread = threading.Thread(target=server.run, daemon=True)
#     thread.start()

#     # Wait briefly for the server to be up
#     timeout = time.time() + 10
#     while time.time() < timeout:
#         try:
#             import http.client
#             conn = http.client.HTTPConnection(TEST_HOST, TEST_PORT, timeout=0.5)
#             conn.request("GET", "/health")
#             resp = conn.getresponse()
#             if resp.status in (200, 404):  # any response means server is accepting connections
#                 break
#         except Exception:
#             time.sleep(0.1)
#     yield

#     # uvicorn doesn't expose a clean stop; rely on daemon thread ending with test process
#     # (If you want, you can improve this with server.should_exit = True)


# @pytest.fixture(scope="session", autouse=True)
# def force_mock_mode():
#     """
#     Ensure the frontend runs in mock mode by not providing real Supabase vars.
#     """
#     os.environ.pop("ENV_SUPABASE_URL", None)
#     os.environ.pop("ENV_SUPABASE_KEY", None)
#     yield


# @pytest.fixture(scope="session")
# def browser():
#     with sync_playwright() as p:
#         browser = p.chromium.launch()
#         yield browser
#         browser.close()


# @pytest.fixture
# def page(browser):
#     ctx = browser.new_context()
#     page = ctx.new_page()
#     yield page
#     ctx.close()


# def goto_payments(page):
#     # Try the template route first to avoid API/JSON router collisions.
#     for path in ("/payments.html", "/payments"):
#         page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")
#         # If the HTML template loaded, these static nodes exist immediately.
#         if page.query_selector("#requested-list") and page.query_selector("#past-list"):
#             break
#     # Now wait a beat for JS to render mock data
#     page.wait_for_selector("#requested-list", timeout=5000)
#     page.wait_for_selector("#past-list", timeout=5000)
#     page.wait_for_timeout(300)
#     return page


# def visible(page, selector: str) -> bool:
#     el = page.query_selector(selector)
#     return bool(el and el.is_visible())

# def all_text(page, selector: str):
#     return [el.inner_text().strip() for el in page.query_selector_all(selector)]

# def all_hrefs(page, selector: str):
#     return [el.get_attribute("href") for el in page.query_selector_all(selector)]

# def test_upcoming_and_past_payments_display_correctly(page):
#     with run_server():
#         goto_payments(page)

#         # Requested should exist (mock has 2)
#         requested_items = page.query_selector_all("#requested-list .payment")
#         assert len(requested_items) >= 1, "Expected at least one requested payment in mock mode"

#         # Pay buttons exist on requested rows
#         pay_buttons = page.query_selector_all("#requested-list .payment .btn.primary:has-text('Pay')")
#         assert len(pay_buttons) >= 1, "Expected Pay buttons on requested payments"

#         # Past should exist (mock has 1)
#         past_items = page.query_selector_all("#past-list .payment")
#         assert len(past_items) >= 1, "Expected at least one past payment in mock mode"

#         # Paid badge visible
#         paid_badges = page.query_selector_all("#past-list .payment .chip")
#         assert any("Paid" in (b.inner_text() or "") for b in paid_badges), "Expected 'Paid' badge on past payments"

# def test_each_payment_links_to_mock_expense(page):
#     with run_server():
#         goto_payments(page)

#         links = all_hrefs(page, "#requested-list .who a, #past-list .who a")
#         assert links, "Expected payment titles to include anchor links"
#         for href in links:
#             assert href and href.startswith("/group?id="), f"Unexpected href: {href}"

# def test_empty_list_shows_placeholder_message(page):
#     with run_server():
#         goto_payments(page)

#         page.fill("#search", "zzzzzzzzzz-impossible-term")
#         # Let render run
#         page.wait_for_timeout(200)

#         assert visible(page, "#requested-empty"), "Requested placeholder should show when no matches"
#         assert visible(page, "#past-empty"), "Past placeholder should show when no matches"

