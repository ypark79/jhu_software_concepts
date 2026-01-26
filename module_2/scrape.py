import urllib3
from bs4 import BeautifulSoup

http = urllib3.PoolManager()

url = "https://www.thegradcafe.com/survey/"

http_response = http.request('GET', url)

html_conversion = http_response.data.decode('utf-8')

with open('website_html.html', 'w', encoding='utf-8') as f:
    f.write(html_conversion))

soup = BeautifulSoup(html_conversion, 'html.parser')

rows = soup.find_all('tr')
data_rows = []
for r in rows:
    if r.find('td') is not None:
        data_rows.append(r)

singe_row = data_rows[0]
cells = singe_row.find_all('td')

print(cells)









