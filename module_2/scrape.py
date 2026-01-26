import urllib3
from bs4 import BeautifulSoup

http = urllib3.PoolManager()

url = "https://www.thegradcafe.com/survey/"

http_response = http.request('GET', url)

html_text = http_response.data.decode('utf-8')

with open('website_html.html', 'w', encoding='utf-8') as f:
    f.write(html_text)

soup = BeautifulSoup(html_text, 'html.parser')

tr_cells = soup.find_all('tr')
tr_td_cells = []
for row in tr_cells:
    td_cells = row.find_all('td')
    if len(td_cells) > 0:
        tr_td_cells.append(row)

extracted_fields = []
for tr_td in tr_td_cells:
    cells = tr_td.find_all('td')

    td_data = []
    for td in cells:
        text = td.get_text(' ')
        text = text.strip()
        td_data.append(text)

    link_tag = tr_td.find('a')
    full_url = None
    if link_tag is not None:
        url_link = link_tag.get('href')
        full_url = 'https://www.thegradcafe.com' + url_link
    td_data.append(full_url)

    extracted_fields.append(td_data)

inputs_for_llm = []
for i in extracted_fields:
    university = i[0]
    program = i[1]
    llm_input = program + ', ' + university

    input_dict = {}
    input_dict['program'] = llm_input

    inputs_for_llm.append(input_dict)

print(extracted_fields[0])
