import asyncio
import argparse
from playwright.async_api import async_playwright
import sys

async def fetch_dynamic_html(url: str) -> str | None:
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
        try:
            print(f"[Playwright] Navigating to: {url}", file=sys.stderr)
            # Use 'networkidle' to wait for network to be idle, max 2 connections for 500ms
            await page.goto(url, wait_until="domcontentloaded", timeout=60000) # 60 seconds timeout for page load, less prone to hangs
            print(f"[Playwright] Page loaded. Waiting for '#rate_box' element (max 15s)...", file=sys.stderr)
            try:
                # Wait for the main rate box to appear, indicating dynamic content is likely loaded
                await page.wait_for_selector('#rate_box', timeout=15000) # Wait up to 15 seconds for the element
                print(f"[Playwright] '#rate_box' element found. Proceeding with content capture.", file=sys.stderr)
            except Exception as e:
                print(f"[Playwright] Warning: '#rate_box' not found within 15 seconds for {url}. Proceeding without it. Error: {e}", file=sys.stderr)

            content = await page.content()
            print(f"[Playwright] Fetched content length: {len(content)}", file=sys.stderr)
            return content
        except Exception as e:
            print(f"[Playwright] Error fetching {url}: {e}", file=sys.stderr)
            return None
        finally:
            await browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch dynamic HTML content using Playwright")
    parser.add_argument("url", help="The URL to fetch")
    args = parser.parse_args()
    
    html_content = asyncio.run(fetch_dynamic_html(args.url))
    if html_content:
        print(html_content) # Print to stdout so the main script can capture it
