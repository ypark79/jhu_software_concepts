import urllib3
import json
from bs4 import BeautifulSoup

# Use urllib3 to make the connection to the website.
http = urllib3.PoolManager()

url = "https://www.thegradcafe.com/survey/"

# Request the html from the website and convert it to html.
http_response = http.request('GET', url)
html_text = http_response.data.decode('utf-8')

# Write the html to a file in order to analyze it to find target tags
# that contain the desired information.
with open('website_html.html', 'w', encoding='utf-8') as f:
    f.write(html_text)

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
        full_url = 'https://www.thegradcafe.com' + url_link
    td_data.append(full_url)

    extracted_fields.append(td_data)

# The provided llm expects json dictionaries as "program, university."
# Extract the university and program fields and format as a dictionary.
# Consolidate all dictionaries in a list to prepare the data to be sent
# to the provided llm.
inputs_for_llm = []
for i in extracted_fields:
    university = i[0]
    program = i[1]
    # Need to account for if a university or a program is not provided
    if university is None:
        university = ''
    if program is None:
        program = ''
    llm_input = program + ', ' + university

    input_dict = {}
    input_dict['program'] = llm_input

    inputs_for_llm.append(input_dict)

# The provided llm expects the inputs to be in a json dictionary with
# key: "rows" and the values being the list of dictionaries extracted
# from the data scraping code above.
payload = {}
payload['rows'] = inputs_for_llm

# Convert the scraped data into json and then into bytes before pushing
# to the llm server.
payload_json = json.dumps(payload)
payload_bytes = payload_json.encode('utf-8')

# Send the data to the server and establish the variable for its response.
llm_response = http.request('POST', 'http://127.0.0.1:8000/standardize', body=payload_bytes, headers={'Content-Type': 'application/json'})

# Convert the llm's response into text and then into python.
llm_response_text = llm_response.data.decode('utf-8')
llm_response_python = json.loads(llm_response_text)

cleaned_entry = llm_response_python['rows']
print(cleaned_entry[0])

