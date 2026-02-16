import asyncio
import argparse
import sys
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def scrape_single_url(credit_union: str, url: str) -> dict:
    result = {'credit_union': credit_union, 'link': url, 'rates_30_years': "None", 'best_rate': "None", 'status': "ERROR", 'error_message': "Unknown error"}

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
            await page.goto(url, wait_until="domcontentloaded", timeout=60000) # 60 seconds timeout for page load
            
            try:
                await page.wait_for_selector('#rate_box', timeout=15000) # Wait up to 15 seconds for the element
            except Exception:
                # If rate_box is not found, we still proceed to get content, it might be in static HTML
                pass # No need to log warning here, main script handles None rates

            html_content = await page.content()
            
            if not html_content:
                result['error_message'] = "No HTML content returned from Playwright"
                return result

            try:
                soup = BeautifulSoup(html_content, 'html.parser')
                rate_box = soup.find('div', id='rate_box')
                
                if rate_box:
                    all_extracted_rates_info = []
                    for table in rate_box.find_all('table', recursive=True):
                        caption_tag = table.find('caption')
                        if caption_tag:
                            loan_type = caption_tag.text.strip()
                            loan_type = loan_type.replace(' - Conforming', '').replace(' - Jumbo', '').strip()

                            for row_data in table.find_all('tr'):
                                interest_rate_span = row_data.find('span', class_="sr-only", string="Interest Rate")
                                apr_span = row_data.find('span', class_="sr-only", string="APR")

                                if interest_rate_span and interest_rate_span.next_sibling:
                                    rate_str = interest_rate_span.next_sibling.strip()
                                    if rate_str.endswith('%'):
                                        numeric_rate = None
                                        try:
                                            numeric_rate = float(rate_str.strip('%'))
                                        except ValueError:
                                            pass

                                    apr_str = "N/A"
                                    if apr_span and apr_span.next_sibling:
                                        apr_str = apr_span.next_sibling.strip()

                                    all_extracted_rates_info.append((loan_type, rate_str, apr_str, numeric_rate))

                    if all_extracted_rates_info:
                        formatted_rates_30_years = []
                        all_numeric_rates = []
                        for loan_type, rate_str, _, numeric_rate in all_extracted_rates_info:
                            formatted_rates_30_years.append(f"{loan_type}-{rate_str}")
                            if numeric_rate is not None:
                                all_numeric_rates.append((numeric_rate, f"{loan_type}-{rate_str}"))

                        result['rates_30_years'] = "|".join(formatted_rates_30_years)

                        if all_numeric_rates:
                            best_rate_info = min(all_numeric_rates, key=lambda item: item[0])
                            result['best_rate'] = best_rate_info[1]
                        else:
                            result['best_rate'] = "None"

                    else:
                        result['rates_30_years'] = "None"
                        result['best_rate'] = "None"
                
                result['status'] = "SUCCESS"
                result['error_message'] = ""
                return result

            except Exception as e:
                result['error_message'] = f"Error parsing HTML: {e}"
                return result

        except Exception as e:
            result['error_message'] = f"Error fetching URL with Playwright: {e}"
            return result
        finally:
            await browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape mortgage data for a single URL using Playwright")
    parser.add_argument("credit_union", help="Name of the credit union")
    parser.add_argument("url", help="The URL to scrape")
    args = parser.parse_args()
    
    scrape_result = asyncio.run(scrape_single_url(args.credit_union, args.url))
    print(json.dumps(scrape_result)) # Output JSON result
