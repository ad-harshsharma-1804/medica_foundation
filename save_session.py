# inject_and_save_session.py

import json
from playwright.sync_api import sync_playwright

COOKIE_FILE = "cookie.json"
STORAGE_FILE = "storage.json"
TARGET_DOMAIN = "https://www.medicafoundation.org"

def inject_cookies_and_save_storage():
    with open(COOKIE_FILE, "r") as f:
        cookies = json.load(f)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=False)
        context = browser.new_context()

        # ✅ Inject cookies
        context.add_cookies(cookies)

        # 🔁 Load the target domain once to activate the cookies
        page = context.new_page()
        page.goto(TARGET_DOMAIN)
        input("✅ Verify you're in and then press ENTER to save session...")

        # 💾 Save storage state including cookies + local storage
        context.storage_state(path=STORAGE_FILE)
        print(f"🎉 storage.json saved and ready to reuse.")

        browser.close()

if __name__ == "__main__":
    inject_cookies_and_save_storage()
