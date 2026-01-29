from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
import json
from bs4 import BeautifulSoup
import time

BASE_DOMAIN = "https://www.thegradcafe.com"
BASE_SURVEY_URL = f"{BASE_DOMAIN}/survey"

# ------------------------ Networking ------------------------
# ----
def _make_request(url: str, accept: str = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8") -> Request:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": accept,
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Referer": f"{BASE_DOMAIN}/survey/",
    }
    return Request(url, headers=headers, method="GET")


def download_html(url: str) -> str:
    req = _make_request(url)

    for attempt in range(5):
        try:
            resp = urlopen(req, timeout=60)
            return resp.read().decode("utf-8", errors="replace")

        except HTTPError as e:
            if 500 <= e.code < 600:
                wait = 2 ** attempt
                print(f"HTTP {e.code} for {url}. Retrying in {wait}s...")
                time.sleep(wait)
                continue
            raise

        except URLError as e:
            wait = 2 ** attempt
            print(f"Network error for {url}: {e}. Retrying in {wait}s...")
            time.sleep(wait)
            continue

    raise RuntimeError(f"Failed to download after retries: {url}")


# ------------------------ Parsing helpers ------------------------

def extract_text(html_text: str) -> str:
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text(" ").strip()


def _extract_tr_rows_from_html(html_text: str) -> list:
    soup = BeautifulSoup(html_text, "html.parser")
    rows = []
    for tr in soup.find_all("tr"):
        if len(tr.find_all("td")) > 0:
            rows.append(tr)
    return rows


def _row_dict_from_tr(tr) -> dict:
    cells = tr.find_all("td")
    td_data = []
    for td in cells:
        td_data.append(td.get_text(" ").strip())

    link_tag = tr.find("a", href=lambda h: h and "/result/" in h)
    full_url = None
    if link_tag:
        href = link_tag.get("href")
        if href:
            full_url = href if href.startswith("http") else (BASE_DOMAIN + href)

    return {
        "university_raw": td_data[0] if len(td_data) > 0 else None,
        "program_raw": td_data[1] if len(td_data) > 1 else None,
        "date_added_raw": td_data[2] if len(td_data) > 2 else None,
        "status_raw": td_data[3] if len(td_data) > 3 else None,
        "comments_raw": td_data[4] if len(td_data) > 4 else None,
        "application_url_raw": full_url,
        "result_text_raw": None,
    }


# ------------------------ Main scraper ------------------------

def scrape_data(page_url: str, page_num: int) -> list[dict]:
    html_text = download_html(page_url)

    tr_rows = _extract_tr_rows_from_html(html_text)

    if not tr_rows:
        return []

    extracted = []
    for tr in tr_rows:
        row = _row_dict_from_tr(tr)
        if row.get("application_url_raw") is None:
            continue
        extracted.append(row)

    # Fetch detail page text for each /result/ entry
    for row in extracted:
        application_url = row.get("application_url_raw")
        if application_url:
            try:
                result_html = download_html(application_url)
                row["result_text_raw"] = extract_text(result_html)
            except Exception:
                row["result_text_raw"] = None

            time.sleep(0.20)

    return extracted


def save_data(data, filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_data(filename: str) -> list[dict]:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except Exception:
        return []


# ------------------------ Runner ------------------------

if __name__ == "__main__":
    TARGET = 30000  # set to 30000 for final run
    CHECKPOINT_FILE = "applicant_data_checkpoint.json"
    FINAL_FILE = "applicant_data.json"
    CHECKPOINT_EVERY_PAGES = 10

    all_rows = load_data(CHECKPOINT_FILE)
    print(f"Resuming with {len(all_rows)} entries from checkpoint.")

    page = (len(all_rows) // 50) + 1 if all_rows else 1
    empty_pages = 0

    while len(all_rows) < TARGET:
        page_url = f"{BASE_SURVEY_URL}/" if page == 1 else f"{BASE_SURVEY_URL}/?page={page}"
        print("Scraping:", page_url)

        try:
            page_rows = scrape_data(page_url, page)
        except Exception as e:
            print(f"Page scrape failed ({page_url}): {e}. Backing off 15s...")
            time.sleep(15)
            page += 1
            continue

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

        all_rows.extend(page_rows)
        print("Total entries so far:", len(all_rows))

        if page % CHECKPOINT_EVERY_PAGES == 0:
            save_data(all_rows, CHECKPOINT_FILE)
            print(f"Checkpoint saved: {CHECKPOINT_FILE}")

        page += 1
        time.sleep(0.75)

    save_data(all_rows, CHECKPOINT_FILE)
    save_data(all_rows[:TARGET], FINAL_FILE)
    saved_n = min(len(all_rows), TARGET)
    print(f"Done. Saved {saved_n} entries to {FINAL_FILE}")