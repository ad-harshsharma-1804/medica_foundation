# collect_cookies_cdp.py

import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="chrome",  # ✅ Uses installed Google Chrome
            headless=False
        )
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://www.medicafoundation.org/")
        print("🧑‍💻 Please solve the Cloudflare challenge manually.")
        input("✅ Press ENTER after you're fully inside the site...")

        # ✅ Save cookies (includes HttpOnly like cf_clearance)
        cookies = await context.cookies()
        with open("cookies_playwright.json", "w") as f:
            json.dump(cookies, f, indent=2)

        print("🍪 Cookies saved to cookies_playwright.json")
        await browser.close()

asyncio.run(main())
