import csv
import subprocess
import sys
import os
from bs4 import BeautifulSoup
import datetime
import json
import time

# Define the base URLs as provided by the user
BASE_URL = "https://mortgages.cumortgage.net/start_up.asp"
SITEID_URL = "https://mortgages.cumortgage.net/default.asp?siteId="

def get_credit_union_links(script_dir, venv_python_path_for_list_fetch):
    fetch_list_script_path = os.path.join(script_dir, "playwright", "fetch_credit_union_list.py") 
    
    try:
        cmd = [venv_python_path_for_list_fetch, fetch_list_script_path, BASE_URL]
        process = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
        raw_output = process.stdout

        credit_unions = []
        for line in raw_output.strip().split('\n'):
            if '>' in line:
                site_id, union_name = line.split('>', 1)
                union_name = union_name.replace('-', '').replace(',', '').replace('.', '').replace("'", '').replace('\r', '')
                full_link = f"{SITEID_URL}{site_id}"
                credit_unions.append({'CreditUnion': union_name.strip(), 'Link': full_link.strip()})
        return credit_unions
    except subprocess.CalledProcessError as e:
        print(f"[ListFetcher] Error fetching credit union list: Stderr: {e.stderr}", file=sys.stderr)
        return []
    except subprocess.TimeoutExpired:
        print(f"[ListFetcher] Playwright list fetch script timed out.", file=sys.stderr)
        return []
    except Exception as e:
        print(f"[ListFetcher] An unexpected error occurred during list fetch: {e}", file=sys.stderr)
        return []

def scrape_mortgage_data(output_csv_filename, max_scrapes_per_run=None):
    script_dir = os.path.dirname(__file__)
    log_file_path = os.path.join(script_dir, "processed.log")
    output_csv_path_abs = os.path.join(script_dir, output_csv_filename)

    venv_python_path = os.path.join(os.path.expanduser("~"), ".venv", "bin", "python") 

    processed_urls = set()
    if os.path.exists(log_file_path):
        with open(log_file_path, mode='r', encoding='utf-8') as lf:
            for line in lf:
                if "SUCCESS" in line:
                    try:
                        parts = line.split(" for ", 1)
                        if len(parts) > 1:
                            url_part = parts[1].split(" - SUCCESS", 1)
                            if len(url_part) > 0:
                                processed_urls.add(url_part[0].strip())
                    except Exception as e:
                        pass 

    with open(log_file_path, mode='a', encoding='utf-8') as log_file:
        def log_message(message, status="INFO", url=""):
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {message}"
            if url:
                log_entry += f" for {url}"
            if status:
                log_entry += f" - {status}"
            log_file.write(f"{log_entry}\n")
            log_file.flush()

        log_message("Starting to fetch credit union list...")
        credit_unions_to_scrape = get_credit_union_links(script_dir, venv_python_path) 
        if not credit_unions_to_scrape:
            log_message("Failed to get credit union list. Aborting scraping.", status="ERROR")
            return
        log_message(f"Fetched {len(credit_unions_to_scrape)} credit unions.")

        fieldnames = ['CreditUnion', 'Link', 'Rates(30Years)', 'BestRate']
        csv_file_exists = os.path.exists(output_csv_path_abs)
        output_file_mode = 'a' if csv_file_exists else 'w'

        with open(output_csv_path_abs, mode=output_file_mode, newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            if not csv_file_exists:
                writer.writerow(fieldnames)

            scraped_count = 0
            for row_data in credit_unions_to_scrape:
                if max_scrapes_per_run is not None and scraped_count >= max_scrapes_per_run:
                    log_message(f"Reached max_scrapes_per_run limit of {max_scrapes_per_run}. Pausing for 2 minutes...", status="INFO")
                    time.sleep(120)  # Pause for 2 minutes
                    log_message("Resuming scraping after pause.", status="INFO")
                    scraped_count = 0  # Reset count for the next batch

                credit_union = row_data['CreditUnion']
                link = row_data['Link']

                if link in processed_urls:
                    log_message(f"Skipping already processed credit union: {credit_union}", status="SKIPPED", url=link)
                    continue

                rates_30_years = "None"
                best_rate = "None"
                scrape_status = "ERROR"
                scrape_error_message = "Unknown error"

                log_message(f"Scraping data for {credit_union}", url=link)

                scrape_result = {}
                try:
                    scrape_single_script_path = os.path.join(script_dir, 'playwright', 'scrape_single_url.py') 
                    
                    cmd = [venv_python_path, scrape_single_script_path, credit_union, link]
                    
                    log_message(f"Running scrape_single_url.py for {credit_union} via subprocess", status="INFO", url=link) 
                    process = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=120) 
                    raw_output = process.stdout
                    
                    if raw_output:
                        try:
                            scrape_result = json.loads(raw_output)
                            rates_30_years = scrape_result.get('rates_30_years', 'None')
                            best_rate = scrape_result.get('best_rate', 'None')
                            scrape_status = scrape_result.get('status', 'ERROR')
                            scrape_error_message = scrape_result.get('error_message', 'Unknown error')

                        except json.JSONDecodeError as e:
                            log_message(f"Error decoding scrape_single_url.py response: {e}. Raw response: {raw_output}", status="ERROR", url=link)
                            continue 
                    else:
                        log_message(f"scrape_single_url.py returned no output for {credit_union}", status="ERROR", url=link)
                        continue 

                except subprocess.TimeoutExpired:
                    log_message(f"scrape_single_url.py timed out for {credit_union}", status="ERROR", url=link)
                    continue 
                except subprocess.CalledProcessError as e:
                    log_message(f"scrape_single_url.py failed for {credit_union}. Stderr: {e.stderr}", status="ERROR", url=link)
                    continue 
                except FileNotFoundError:
                    log_message(f"Error: scrape_single_url.py or python executable not found.", status="ERROR", url=link)
                    continue 
                except Exception as e:
                    log_message(f"An unexpected error during scrape_single_url.py call: {e}", status="ERROR", url=link)
                    continue 
                
                if scrape_status != "SUCCESS":
                    log_message(f"Scraping failed for {credit_union}: {scrape_error_message}", status="ERROR", url=link)
                    continue 

                updated_row = [credit_union, link, rates_30_years, best_rate]
                writer.writerow(updated_row)
                outfile.flush() 
                log_message(f"Successfully scraped and processed {credit_union}", status="SUCCESS", url=link)
                scraped_count += 1

        log_message(f"Scraping complete. Results saved to {output_csv_filename}", status="INFO")

        # After scraping is complete, convert CSV to HTML
        log_message("Converting CSV to HTML...", status="INFO")
        try:
            convert_script_path = os.path.join(script_dir, "convert_csv_to_html.py")
            cmd = [venv_python_path, convert_script_path]
            subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
            log_message("CSV to HTML conversion complete.", status="SUCCESS")
        except subprocess.CalledProcessError as e:
            log_message(f"Error converting CSV to HTML: Stderr: {e.stderr}", status="ERROR")
        except subprocess.TimeoutExpired:
            log_message("CSV to HTML conversion timed out.", status="ERROR")
        except FileNotFoundError:
            log_message("Error: convert_csv_to_html.py script not found.", status="ERROR")
        except Exception as e:
            log_message(f"An unexpected error occurred during HTML conversion: {e}", status="ERROR")

if __name__ == "__main__":
    # Set a limit for the number of scrapes per run to avoid resource exhaustion
    # The script will pick up where it left off on subsequent runs due to processed.log
    MAX_SCRAPES_PER_RUN = 20  # You can adjust this value
    scrape_mortgage_data("mortgage_rates.csv", max_scrapes_per_run=MAX_SCRAPES_PER_RUN)
