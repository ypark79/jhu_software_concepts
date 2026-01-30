from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
import json
from bs4 import BeautifulSoup
import time

# Separate the base domain of the URL to facilitate code entering
# different endpoints.
BASE_DOMAIN = "https://www.thegradcafe.com"
BASE_SURVEY_URL = f"{BASE_DOMAIN}/survey"

# Standardize the GET requests that are made by the code to the website.
# This makes the requests look like its coming from a user on a MAC
# using Mozilla. Avoids website from blocking requests due to
# suspicion of bots.
def _make_request(url: str, accept: str = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8") -> Request:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": accept,
        "Accept-Language": "en-US,en;q=0.9",
        # Reduces chances of losing connection with the website and code
        # crashing.
        "Connection": "keep-alive",
        "Referer": f"{BASE_DOMAIN}/survey/",
    }
    return Request(url, headers=headers, method="GET")

# Download html in bytes and decode into utf-8
def download_html(url: str) -> str:
    # Call _make_request function to execute a standardized GET
    req = _make_request(url)

    # Account for server or network errors due to high volume of data
    # scraping. Retry scrape with increasing amounts of wait time.
    for attempt in range(5):
        try:
            resp = urlopen(req, timeout=60)
            # errors guards against characters that utf-8 does not
            # recognize.
            return resp.read().decode("utf-8", errors="replace")
        # Addresses courses of action if code encounters server errors.
        # Code will exponentially increase wait time before attempting
        # again. Print status for awareness.
        except HTTPError as e:
            if 500 <= e.code < 600:
                wait = 2 ** attempt
                print(f"HTTP {e.code} for {url}. Retrying in {wait}s...")
                time.sleep(wait)
                continue
            raise
        # Addresses network and connection errors.
        except URLError as e:
            wait = 2 ** attempt
            print(f"Network error for {url}: {e}. Retrying in {wait}s...")
            time.sleep(wait)
            continue
    # If errors are not retryable or solvable, code will not try again.
    raise RuntimeError(f"Failed to download after retries: {url}")

# Convert html_text into beautifulsoup object to facilitate parsing.
def extract_text(html_text: str) -> str:
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text(" ").strip()

# All desired fields exist between <tr> and <td> tags. Ignore the <tr>
# <td> tags with no data. Pull all data between these tags.
def _extract_tr_rows_from_html(html_text: str) -> list:
    soup = BeautifulSoup(html_text, "html.parser")
    rows = []
    for tr in soup.find_all("tr"):
        if len(tr.find_all("td")) > 0:
            rows.append(tr)
    return rows

# Find all data within <td> tags in each <tr> row and clean to extract
# text.
def _row_dict_from_tr(tr) -> dict:
    cells = tr.find_all("td")
    td_data = []
    for td in cells:
        td_data.append(td.get_text(" ").strip())

    # Target links to each user's application. Half of the desired
    # fields exist in there. Target <a> tags with href attributes.
    link_tag = tr.find("a", href=lambda h: h and "/result/" in h)
    full_url = None
    if link_tag:
        href = link_tag.get("href")
        # Build out complete url to facilitate code accessing the
        # student application links during scraping.
        if href:
            full_url = href if href.startswith("http") else (BASE_DOMAIN + href)

    # Build initial dictionary with raw key-value pairs.
    return {
        # This data is from the student application page. Does not
        # include data inside each URL link to student apps.
        "university_raw": td_data[0] if len(td_data) > 0 else None,
        "program_raw": td_data[1] if len(td_data) > 1 else None,
        "date_added_raw": td_data[2] if len(td_data) > 2 else None,
        "status_raw": td_data[3] if len(td_data) > 3 else None,
        "comments_raw": td_data[4] if len(td_data) > 4 else None,
        "application_url_raw": full_url,
        # Data pulled from student application URLs will go in results
        # text raw.
        "result_text_raw": None,
    }

# Primary data scraper function.
def scrape_data(page_url: str, page_num: int) -> list[dict]:
    html_text = download_html(page_url)

    tr_rows = _extract_tr_rows_from_html(html_text)
    # Addresses empty pages.
    if not tr_rows:
        return []

    extracted = []
    for tr in tr_rows:
        row = _row_dict_from_tr(tr)
        # Extract all data except for the links.
        if row.get("application_url_raw") is None:
            continue
        extracted.append(row)

    # Extract data from each student application link and put into
    # results_text_raw for cleaning later.
    for row in extracted:
        application_url = row.get("application_url_raw")
        if application_url:
            try:
                result_html = download_html(application_url)
                row["result_text_raw"] = extract_text(result_html)
            # Guards against links that fail or server/network failures.
            except Exception:
                row["result_text_raw"] = None
            time.sleep(0.20)
    return extracted


# Convert dirty data into json and write to a file.
def save_data(data, filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Safety measure in the case anything crashes while scraping. Allows
# code to pick up where it left off before the crash to avoid
# starting from nothing.
def load_data(filename: str) -> list[dict]:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except Exception:
        return []

# Code execution portion.
if __name__ == "__main__":
    # Ensure to scrape 30,000 complete entries
    TARGET = 30000  # set to 30000 for final run

    # Safety measure in case the code/server crashes. Allows code to
    # pick up where it left off.
    CHECKPOINT_FILE = "raw_scraped_data_checkpoint.json"

    # This will be the dirty output from scrape.py and will be used
    # by clean.py.
    FINAL_FILE = "raw_scraped_data.json"

    # Safety measure. Saves progress every 10 pages.
    CHECKPOINT_EVERY_PAGES = 10

    # Safety measure that loads all scraped data before crash. Identify
    # what page the start on if code/server crashes.
    all_rows = load_data(CHECKPOINT_FILE)
    print(f"Resuming with {len(all_rows)} entries from checkpoint.")
    page = (len(all_rows) // 50) + 1 if all_rows else 1

    # Keep track of empty pages and use as a trigger to save work.
    empty_pages = 0

    # Initiate overarching while loop to scrape 30,000 entries.
    while len(all_rows) < TARGET:
        # Distinguish between the URL for the first page and subsequent
        # pages. Print progress.
        page_url = f"{BASE_SURVEY_URL}/" if page == 1 else f"{BASE_SURVEY_URL}/?page={page}"
        print("Scraping:", page_url)

        # Retry process in case server does not respond. Print location
        # of errors. Allow code to continue if page fails.
        try:
            page_rows = scrape_data(page_url, page)
        except Exception as e:
            print(f"Page scrape failed ({page_url}): {e}. Backing off 15s...")
            time.sleep(15)
            page += 1
            continue

        # Account for the possibility of empty pages. Limit to 5 empty pages.
        # Ensure to save progress.
        if not page_rows:
            empty_pages += 1
            print(f"No usable rows on {page_url}. Backing off 10s... ({empty_pages}/5)")
            time.sleep(10)

            if empty_pages >= 5:
                print("Too many empty pages in a row. Saving checkpoint and exiting.")
                save_data(all_rows, CHECKPOINT_FILE)
                break

            page += 1
            continue
        else:
            empty_pages = 0

        # Take all rows scraped from a page and add to dataset.
        all_rows.extend(page_rows)
        print("Total entries so far:", len(all_rows))

        # Save progress in a checkpoint file to avoid losing work.
        if page % CHECKPOINT_EVERY_PAGES == 0:
            save_data(all_rows, CHECKPOINT_FILE)
            print(f"Checkpoint saved: {CHECKPOINT_FILE}")

        # Pace the frequency of sever requests to avoid crashing.
        page += 1
        time.sleep(0.75)

    # Save checkpoint file for safety and final dataset is complete.
    # Print status to indicate completion.
    save_data(all_rows, CHECKPOINT_FILE)
    save_data(all_rows[:TARGET], FINAL_FILE)
    saved_n = min(len(all_rows), TARGET)
    print(f"Done. Saved {saved_n} entries to {FINAL_FILE}")