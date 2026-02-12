import asyncio
import argparse
from playwright.async_api import async_playwright

async def main(url: str, max_retries=3):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-crash-reporter",
                "--disable-extensions",
                "--single-process",
                "--no-zygote"
            ]
        )
        page = await browser.new_page()
        #await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        for attempt in range(1, max_retries + 1):
            print(f"🌀 Attempt {attempt} to load: {url}")
            try:
                # Limit each navigation attempt to 30 seconds
                await asyncio.wait_for(
                    page.goto(url, wait_until="domcontentloaded", timeout=30000),
                    timeout=35
                )
                print("Page title:", await page.content())
                await browser.close()

            except asyncio.TimeoutError:
                print(f"⏱️ Attempt {attempt} timed out. Retrying...")
            except Exception as e:
                print(f"⚠️ Attempt {attempt} failed: {e}")

            if attempt < max_retries:
                print("🔄 Reloading before next try...")
                try:
                    await asyncio.wait_for(page.reload(wait_until="domcontentloaded", timeout=20000), timeout=25)
                except:
                    pass
                await asyncio.sleep(2)
            else:
                print("❌ All attempts failed or timed out.")

        await browser.close()
        return None
 #       print("Page title:", await page.content())
 #       await browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch a page content with Playwright")
    parser.add_argument("url", help="The URL to open")
    args = parser.parse_args()

    asyncio.run(main(args.url))
