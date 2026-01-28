from urllib.request import urlopen, Request
import json
from bs4 import BeautifulSoup
import time

url = "https://www.thegradcafe.com/survey/"

# Request the html from the website and convert it to html.
def download_html(url):
    get_request = Request(url, headers={'User-Agent': 'Mozilla/5.0'}, method='GET')
    response = urlopen(get_request, timeout = 60)
    html_text = response.read().decode("utf-8")
    return html_text

def extract_text(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    text = soup.get_text(' ')
    text = text.strip()
    return text

def scrape_data():
    html_text = download_html(url)

    # Create a BeautifulSoup object to parse through the extracted html from
    # the website.
    soup = BeautifulSoup(html_text, 'html.parser')

    # Isolate all the info inside <tr> tags. Then isolate all the data within
    # that is inside <td> tags.
    tr_cells = soup.find_all('tr')
    tr_td_cells = []
    for row in tr_cells:
        td_cells = row.find_all('td')
        # Account for rows that do not have desired data.
        if len(td_cells) > 0:
            tr_td_cells.append(row)

    # Extract the text within the <td> tags. Strip out the newlines to
    # isolate just the desired fields.
    extracted_fields = []
    for tr_td in tr_td_cells:
        cells = tr_td.find_all('td')

        td_data = []
        for td in cells:
            text = td.get_text(' ')
            text = text.strip()
            td_data.append(text)

        # The <tr>/<td> extraction does not extract the ULR links to the
        # students' applications inside <a href>. Search for all <a> tags
        # and then isolate all <a> tags with href in it.
        link_tag = tr_td.find('a')
        full_url = None
        if link_tag is not None:
            url_link = link_tag.get('href')
            if url_link:
                full_url = 'https://www.thegradcafe.com' + url_link
        td_data.append(full_url)

        extracted_fields.append(td_data)

    extracted_fields_raw = []
    for row in extracted_fields:
        row_dict = {}

        # University
        if len(row) > 0:
            row_dict['university_raw'] = row[0]
        else:
            row_dict['university_raw'] = None

        # Program
        if len(row) > 1:
            row_dict['program_raw'] = row[1]
        else:
            row_dict['program_raw'] = None

        # Data data added to website
        if len(row) > 2:
            row_dict['date_added_raw'] = row[2]
        else:
            row_dict['date_added_raw'] = None

        # Decision status
        if len(row) > 3:
            row_dict['status_raw'] = row[3]
        else:
            row_dict['status_raw'] = None

        # Comments
        if len(row) > 4:
            row_dict['comments_raw'] = row[4]
        else:
            row_dict['comments_raw'] = None

        # Application
        if len(row) > 5:
            row_dict['application_url_raw'] = row[5]
        else:
            row_dict['application_url_raw'] = None

        extracted_fields_raw.append(row_dict)

    for row in extracted_fields_raw:
        application_url = row['application_url_raw']
        row['result_text_raw'] = None
        if application_url is not None:
            try:
                result_html = download_html(application_url)
                result_text = extract_text(result_html)
                row['result_text_raw'] = result_text
            except Exception:
                row['result_text_raw'] = None
            time.sleep(0.1)

    return extracted_fields_raw

def save_data(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii = False, indent=2)

if __name__ == "__main__":
    all_rows = []
    page = 1
    TARGET = 30000

    while len(all_rows) < TARGET:
        # Change the global URL that scrape_data() uses
        if page == 1:
            url = "https://www.thegradcafe.com/survey/"
        else:
            url = f"https://www.thegradcafe.com/survey/?page={page}"

        print("Scraping:", url)

        page_rows = scrape_data()   # <-- your existing function (unchanged)
        all_rows.extend(page_rows)

        print("Total rows so far:", len(all_rows))

        page += 1
        time.sleep(0.2)  # polite delay so you don't get blocked

    save_data(all_rows[:TARGET], "applicant_data.json")
    print("Done. Saved 30,000 rows to applicant_data.json")


