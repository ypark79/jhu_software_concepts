from urllib.request import urlopen, Request
import json

# Load raw scraped data from scrape.py
with open("raw.json", "r", encoding="utf-8") as f:
    extracted_fields_raw = json.load(f)


# The provided llm expects json dictionaries as "program, university."
# Extract the university and program fields and format as a dictionary.
# Consolidate all dictionaries in a list to prepare the data to be sent
# to the provided llm.
inputs_for_llm = []
for row in extracted_fields_raw:
    university = row.get('university_raw')
    program = row.get('program_raw')

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
llm_url =  'http://127.0.0.1:8000/standardize'
llm_request = Request(llm_url, headers={'Content-Type': 'application/json'}, method='POST', data=payload_bytes)

llm_response = urlopen(llm_request)
llm_response_text = llm_response.read().decode('utf-8')
llm_response_python = json.loads(llm_response_text)

cleaned_entry = llm_response_python['rows']
print(cleaned_entry[0])