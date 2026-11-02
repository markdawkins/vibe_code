"""
Log in to your own LinkedIn account and send ONE connection invite to a
person you name.

Setup:
    python -m pip install playwright
    playwright install chromium

Usage:
    python linkedin_send_invite.py
    (optional) export LINKEDIN_EMAIL='you@example.com'
               export LINKEDIN_PASSWORD='your-password'   # use single quotes

Flow:
    1. Prompts for the person's name
    2. Signs in (auto with env vars, otherwise manually in the browser)
    3. Searches LinkedIn people and lists the top matches
    4. You pick the right person and optionally add a short note
    5. You confirm, then the invite is sent

Notes:
- Deliberately handles one person per run (no bulk sending).
- LinkedIn's User Agreement restricts automation, and its free accounts have
  weekly invite limits. Use sparingly. Page layouts change, so selectors may
  need adjusting; screenshots are saved to help with that.
"""

import os
import re
import sys
from urllib.parse import quote

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

HOME_URL = "https://www.linkedin.com/feed/"
SESSION_DIR = "./linkedin_session"
LOGGED_IN_URL = re.compile(r"linkedin\.com/(feed|mynetwork|in/|messaging|notifications|search)")
NOTE_LIMIT = 300  # LinkedIn's note limit for free accounts


def on_login_page(page) -> bool:
    return any(k in page.url for k in ("/login", "/uas/", "authwall", "/signup", "checkpoint"))


def ensure_logged_in(page, email, password) -> None:
    page.goto(HOME_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    if not on_login_page(page):
        return

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


def search_people(page, name: str, limit: int = 5):
    """Return up to `limit` (display_text, profile_url) tuples from people search."""
    url = f"https://www.linkedin.com/search/results/people/?keywords={quote(name)}"
    page.goto(url, wait_until="domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=15_000)
    except PWTimeout:
        pass
    page.wait_for_timeout(2500)

    results, seen = [], set()
    for link in page.locator("a[href*='/in/']").all():
        href = (link.get_attribute("href") or "").split("?")[0].rstrip("/")
        if "/in/" not in href or href in seen:
            continue
        lines = [l.strip() for l in link.inner_text().splitlines() if l.strip()]
        if not lines:
            continue
        seen.add(href)
        results.append((lines[0], href))
        if len(results) >= limit:
            break
    return results


def click_connect(page) -> bool:
    """Click the Connect button on a profile page (directly or via the More menu)."""
    top = page.locator("main").first

    # Direct "Connect" button/link in the profile header.
    direct = top.locator(
        "a[aria-label*='to connect'], button[aria-label*='to connect']"
    ).first
    if direct.count():
        direct.click()
        return True

    by_role = top.get_by_role("button", name=re.compile(r"^Connect$", re.I)).first
    if by_role.count():
        by_role.click()
        return True

    # Otherwise it may be tucked into the "More" menu.
    more = top.get_by_role("button", name=re.compile(r"^More", re.I)).first
    if more.count():
        more.click()
        page.wait_for_timeout(800)
        item = page.get_by_role("menuitem", name=re.compile(r"Connect", re.I)).first
        if item.count():
            item.click()
            return True
        # Some layouts render menu entries as plain divs.
        item = page.locator("div[role='menu'] >> text=/^Connect$/i").first
        if item.count():
            item.click()
            return True
    return False


def already_connected_or_pending(page) -> str | None:
    main = page.locator("main").first
    for label in ("Pending", "Message"):
        if main.get_by_role("button", name=re.compile(f"^{label}", re.I)).count() and \
                not main.locator("a[aria-label*='to connect'], button[aria-label*='to connect']").count():
            return label
    return None


def dump_dialogs(page) -> None:
    """Print the text of every dialog and visible button to help debugging."""
    page.screenshot(path="invite_dialog_problem.png", full_page=True)
    dialogs = page.get_by_role("dialog")
    print(f"\n[debug] {dialogs.count()} dialog(s) on the page:")
    for i in range(dialogs.count()):
        text = " | ".join(l.strip() for l in dialogs.nth(i).inner_text().splitlines() if l.strip())
        print(f"  dialog {i + 1}: {text[:400]}")
    names = []
    for b in page.get_by_role("button").all():
        try:
            if b.is_visible():
                label = (b.get_attribute("aria-label") or b.inner_text() or "").strip()
                if label:
                    names.append(label.replace("\n", " ")[:50])
        except Exception:
            pass
    print(f"[debug] visible buttons: {names[:40]}")
    print("[debug] screenshot saved: invite_dialog_problem.png\n")


def click_button(page, patterns, timeout: int = 6000) -> bool:
    """Click the first visible button whose name matches any regex in `patterns`."""
    for pat in patterns:
        btn = page.get_by_role("button", name=re.compile(pat, re.I)).last
        try:
            btn.wait_for(state="visible", timeout=timeout)
            btn.click(timeout=timeout)
            return True
        except PWTimeout:
            continue
    return False


def send_invite(page, note: str) -> bool:
    page.wait_for_timeout(2000)
    try:
        page.get_by_role("dialog").first.wait_for(timeout=8000)
    except PWTimeout:
        dump_dialogs(page)
        return False

    dialog_text = " ".join(
        page.get_by_role("dialog").nth(i).inner_text()
        for i in range(page.get_by_role("dialog").count())
    ).lower()

    # Email-verification prompt: LinkedIn wants the person's email; we can't proceed.
    if "email" in dialog_text and ("verify" in dialog_text or "enter" in dialog_text) \
            and "add a note" not in dialog_text:
        print("LinkedIn is asking for this person's email address to connect. "
              "Cannot continue automatically.")
        dump_dialogs(page)
        return False

    if note:
        if not click_button(page, [r"^Add a note"]):
            dump_dialogs(page)
            return False
        page.wait_for_timeout(500)
        box = page.locator("textarea:visible").first
        try:
            box.wait_for(timeout=5000)
        except PWTimeout:
            dump_dialogs(page)
            return False
        box.fill(note)
        sent = click_button(page, [r"^Send( invitation| now)?$", r"^Send"])
    else:
        sent = click_button(page, [r"Send without a note", r"^Send( invitation| now)?$", r"^Send"])

    if not sent:
        dump_dialogs(page)
        return False
    page.wait_for_timeout(2000)
    return True


def main() -> None:
    name = input("Name of the LinkedIn user to invite: ").strip()
    if not name:
        sys.exit("No name entered.")

    email = os.environ.get("LINKEDIN_EMAIL")
    password = os.environ.get("LINKEDIN_PASSWORD")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(SESSION_DIR, headless=False)
        page = context.new_page()

        try:
            ensure_logged_in(page, email, password)

            matches = search_people(page, name)
            if not matches:
                page.screenshot(path="search_results.png", full_page=True)
                sys.exit("No matches found. See search_results.png.")

            print("\nTop matches:")
            for i, (label, url) in enumerate(matches, 1):
                print(f"  {i}. {label}  -  {url}")
            choice = input("\nPick a number (or press Enter to cancel): ").strip()
            if not choice.isdigit() or not (1 <= int(choice) <= len(matches)):
                sys.exit("Cancelled.")
            label, profile_url = matches[int(choice) - 1]

            note = input(f"Optional note (max {NOTE_LIMIT} chars, Enter to skip): ").strip()
            if len(note) > NOTE_LIMIT:
                note = note[:NOTE_LIMIT]
                print(f"Note trimmed to {NOTE_LIMIT} characters.")

            confirm = input(f"\nSend connection invite to '{label}'? (yes/no): ").strip().lower()
            if confirm not in ("y", "yes"):
                sys.exit("Cancelled. Nothing was sent.")

            page.goto(profile_url, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            state = already_connected_or_pending(page)
            if state:
                page.screenshot(path="profile_state.png")
                sys.exit(f"No Connect option found (profile shows '{state}'). "
                         "You may already be connected or an invite is pending.")

            if not click_connect(page):
                page.screenshot(path="profile_state.png", full_page=True)
                sys.exit("Could not find a Connect button. See profile_state.png.")

            if send_invite(page, note):
                page.screenshot(path="invite_sent.png")
                print(f"\nInvite sent to {label}. (Screenshot: invite_sent.png)")
            else:
                page.screenshot(path="invite_dialog_problem.png", full_page=True)
                print("The invite dialog did not appear as expected. "
                      "See invite_dialog_problem.png; the invite may not have been sent.")
        finally:
            page.wait_for_timeout(3000)
            context.close()


if __name__ == "__main__":
    main()
