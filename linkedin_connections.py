"""
Log in to your own LinkedIn account and display your connections count.

Setup:
    python -m pip install playwright
    playwright install chromium

Usage:
    export LINKEDIN_EMAIL="you@example.com"
    export LINKEDIN_PASSWORD="your-password"
    python linkedin_connections.py

If the env vars are not set, the script waits for you to sign in manually
in the browser window. The session is saved in ./linkedin_session.

Note: automating LinkedIn may violate its User Agreement; use sparingly.
"""

import os
import re
import sys

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

PROFILE_URL = "https://www.linkedin.com/in/markdawkins/"
CONNECTIONS_URL = "https://www.linkedin.com/mynetwork/invite-connect/connections/"
SESSION_DIR = "./linkedin_session"

PATTERNS = [
    r"([\d,\.]+\+?)\s*connections?\b",
    r"\bconnections?\b\s*[:\-]?\s*([\d,\.]+\+?)",
]

LOGGED_IN_URL = re.compile(r"linkedin\.com/(feed|mynetwork|in/|messaging|notifications)")


def on_login_page(page) -> bool:
    return any(k in page.url for k in ("/login", "/uas/", "authwall", "/signup", "checkpoint"))


def ensure_logged_in(page, email, password) -> None:
    """Go to the connections page; sign in if LinkedIn redirects to a login form."""
    page.goto(CONNECTIONS_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    if not on_login_page(page):
        return  # already signed in

    if email and password:
        print("Not signed in. Filling in credentials...")
        page.fill("input[name='session_key']", email)
        page.fill("input[name='session_password']", password)
        page.click("button[type='submit']")
    else:
        print("Not signed in. Please sign in manually in the browser window...")

    print("Complete any 2FA / CAPTCHA in the browser if prompted (waiting up to 5 minutes).")
    try:
        page.wait_for_url(LOGGED_IN_URL, timeout=300_000)
    except PWTimeout:
        sys.exit("Sign-in did not complete in time.")


def find_count(text: str):
    for pattern in PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def get_connections_count(page):
    if "mynetwork/invite-connect/connections" not in page.url:
        page.goto(CONNECTIONS_URL, wait_until="domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=15_000)
    except PWTimeout:
        pass
    page.wait_for_timeout(3000)
    page.mouse.wheel(0, 600)
    page.wait_for_timeout(1500)

    print(f"Current URL:  {page.url}")
    print(f"Page title:   {page.title()}")

    text = page.inner_text("body")
    with open("connections_page.txt", "w", encoding="utf-8") as f:
        f.write(text)
    page.screenshot(path="connections_page.png", full_page=True)

    count = find_count(text)
    if count:
        return count

    print("Not found on connections page; trying profile page (may show '500+').")
    page.goto(PROFILE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    return find_count(page.inner_text("body"))


def main() -> None:
    email = os.environ.get("LINKEDIN_EMAIL")
    password = os.environ.get("LINKEDIN_PASSWORD")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(SESSION_DIR, headless=False)
        page = context.new_page()

        ensure_logged_in(page, email, password)
        count = get_connections_count(page)

        if count:
            print(f"Connections: {count}")
        else:
            print("Still could not find the count.")
            print("Check connections_page.png and connections_page.txt to see what loaded.")

        page.wait_for_timeout(5000)
        context.close()


if __name__ == "__main__":
    main()
