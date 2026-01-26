import urllib3
from bs4 import BeautifulSoup

http = urllib3.PoolManager()

url = "https://www.thegradcafe.com/survey/"

http_response = http.request('GET', url)

html_text = http_response.data.decode('utf-8')

with open('website_html.html', 'w', encoding='utf-8') as f:
    f.write(html_text)

soup = BeautifulSoup(html_text, 'html.parser')

tr_rows = soup.find_all('tr')
tr_td_rows = []
for line in tr_rows:
    td_cells = line.find_all('td')
    if len(td_cells) > 0:
        tr_td_rows.append(line)

print(tr_td_rows[0])








