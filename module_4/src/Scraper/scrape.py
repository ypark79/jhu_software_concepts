from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
import json
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime, timedelta

# Separate the base domain of the URL to facilitate code entering
# different endpoints.
base_domain = "https://www.thegradcafe.com"
base_survey_url = f"{base_domain}/survey"

# Standardize the GET requests that are made by the code to the website.
# This makes the requests look like its coming from a user on a MAC
# using Mozilla. Avoids website from blocking requests due to
# suspicion of bots.
def _make_request(url: str, accept: str = "text/html,application/xhtml+xml,"
                                          "application/xml;q=0.9,*/*;q="
                                          "0.8") -> Request:
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
        "Referer": f"{base_domain}/survey/",
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


# Pull the unique result ID from URLs like:
# https://www.thegradcafe.com/result/994157
# Use this to avoid re-scraping the same entry.

def extract_result_id(url: str):
    if not url:
        return None
    match = re.search(r"/result/(\d+)", url)
    return int(match.group(1)) if match else None


# Convert GradCafe date string (e.g., "January 31, 2026")
# into a datetime object so we can filter only recent posts.
def parse_date_added(date_string: str):
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string.strip(), "%B %d, %Y")
    except ValueError:
        return None

TERM_RE = re.compile(r"\b(Spring|Summer|Fall|Autumn|Winter)\s+(20\d{2})\b",
                     re.IGNORECASE)

def extract_term_from_text(text: str):
    if not text:
        return None
    m = TERM_RE.search(text)
    if not m:
        return None
    term = m.group(1).title()
    if term == "Autumn":
        term = "Fall"
    year = m.group(2)
    return f"{term} {year}"

# Infer the term and year due to mod 2 outputs failing to scrape the term
# field.
def infer_term_from_row(program_text: str, status_text: str,
                        comments_text: str):
    combined = (f"{program_text or ''} {status_text or ''} "
                f"{comments_text or ''}")

    match = re.search(r"\b(Fall|Autumn)\s+(20\d{2})\b",
                      combined, re.IGNORECASE)
    if match:
        term = match.group(1).title()
        if term == "Autumn":
            term = "Fall"
        year = match.group(2)
        return f"{term} {year}"

    return None

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
    full_url = None
    result_id = None
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
            full_url = href if href.startswith("http") \
                else (base_domain + href)

        # Extract the unique ID from the URL so we can de-duplicate later
        result_id = extract_result_id(full_url)


    return {
        "result_id": result_id,
        "university_raw": td_data[0] if len(td_data) > 0 else None,
        "program_raw": td_data[1] if len(td_data) > 1 else None,
        "date_added_raw": td_data[2] if len(td_data) > 2 else None,
        "status_raw": td_data[3] if len(td_data) > 3 else None,
        "comments_raw": td_data[4] if len(td_data) > 4 else None,
        "application_url_raw": full_url,
        "result_text_raw": None,
    }

# Fixing scraper to properly extract term data.
def extract_term_from_detail_row(detail_text: str):

    if not detail_text:
        return None

    match = re.search(r"\b(Spring|Summer|Fall|Autumn|Winter)\s+(20\d{2})\b",
                      detail_text, re.IGNORECASE)
    if not match:
        return None

    term = match.group(1).title()
    if term == "Autumn":
        term = "Fall"
    year = match.group(2)
    return f"{term} {year}"

# Primary data scraper function.
# Updated to stop scraping when it identifies a results_id that already
# exists in the original JSON file.
def scrape_data(page_url: str, existing_ids: set) -> tuple[list[dict], bool]:
    html_text = download_html(page_url)

    tr_rows = _extract_tr_rows_from_html(html_text)
    # Addresses empty pages.
    if not tr_rows:
        return [], False

    extracted = []
    stop_now = False
    i = 0
    while i < len(tr_rows):
        tr = tr_rows[i]
        row = _row_dict_from_tr(tr)

        # If the row has no URL,  cannot scrape the detail page
        if row.get("application_url_raw") is None:
            i += 1
            continue

        rid = row.get("result_id")
        if rid is None:
            i += 1
            continue

        # Stop when we hit an ID we already have
        if rid in existing_ids:
            stop_now = True
            break

        # Look at the NEXT tr for detail info
        term_found = None
        if i + 1 < len(tr_rows):
            next_tr = tr_rows[i + 1]
            next_tds = next_tr.find_all("td")

            # Detail row usually has ONE td with lots of text
            if len(next_tds) == 1:
                detail_text = next_tds[0].get_text(" ", strip=True)
                term_found = extract_term_from_detail_row(detail_text)

        # Save it on the row
        row["term_inferred"] = term_found

        extracted.append(row)

        # Move to the next row.
        # If we consumed the detail row, skip it by jumping +2.
        if term_found is not None:
            i += 2
        else:
            i += 1
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
    return extracted, stop_now


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
    # Set target to 1000 just in case so code does not run forever.
    target = 1000  # safety cap so it never runs forever


    # This will be the dirty output from scrape.py and will be used
    # by clean.py.
    final_file = "raw_scraped_data.json"


    # Safety measure that loads all scraped data before crash. Identify
    # what page the start on if code/server crashes.
    # Start fresh each run (no checkpoint resume)
    all_rows = []


    # Load IDs from the large master dataset to avoid
    # scraping entries that already exist.
    MASTER_DATA_FILE = "llm_extend_applicant_data.json"

    existing_ids = set()

    try:
        master_data = load_data(MASTER_DATA_FILE)

        for row in master_data:
            rid = extract_result_id(row.get("url") or row.get("application_url_raw"))
            if rid is not None:
                existing_ids.add(rid)

        print(f"Loaded {len(existing_ids)} known IDs from master dataset.")

    except FileNotFoundError:  # pragma: no cover  # handled earlier in load_data()
        print("Master dataset not found. Continuing without ID filtering.")

    page = 1

    # Keep track of empty pages and use as a trigger to save work.
    empty_pages = 0

    # Scrape only NEW entries (stop when we hit an existing ID).
    while len(all_rows) < target:
        # Distinguish between the URL for the first page and subsequent
        # pages. Print progress.
        page_url = f"{base_survey_url}/" if page == 1 else \
            f"{base_survey_url}/?page={page}"
        print("Scraping:", page_url)

        # Retry process in case server does not respond. Print location
        # of errors. Allow code to continue if page fails.
        try:
            # Updated call for existing results_ids.
            page_rows, stop_now = scrape_data(page_url, existing_ids)
        except Exception as e:  # pragma: no cover  # defensive branch; hard to trigger in tests
            print(f"Page scrape failed ({page_url}): {e}. Backing off 15s...")
            time.sleep(15)
            page += 1
            continue

        # Account for the possibility of empty pages. Limit to 5 empty pages.
        # Ensure to save progress.
        if not page_rows:
            empty_pages += 1
            print(f"No usable rows on {page_url}. Backing off 10s... "
                  f"({empty_pages}/5)")
            time.sleep(10)

            if empty_pages >= 5:
                print("Too many empty pages in a row. Exiting early.")
                break

            page += 1
            continue
        else:
            empty_pages = 0

        # Take all rows scraped from a page and add to dataset.
        # Scraper stops when previously scraped data exists.
        all_rows.extend(page_rows)

        # Add new IDs so duplicates are not processed again
        for r in page_rows:
            rid = r.get("result_id")
            if rid is not None:
                existing_ids.add(rid)

        # Existing stop logic
        if stop_now:  # pragma: no cover  # unreachable with current scrape_data flow
            print("Reached previously scraped data. Stopping.")
            break

        print("Total entries so far:", len(all_rows))


        # Pace the frequency of sever requests to avoid crashing.
        page += 1
        time.sleep(0.75)

    # Print status to indicate completion.
    save_data(all_rows[:target], final_file)
    saved_n = min(len(all_rows), target)
    print(f"Done. Saved {saved_n} entries to {final_file}")