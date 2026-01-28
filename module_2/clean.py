from urllib.request import urlopen, Request
import json
import re

def clean_whitespace(text):
    if text is None:
        return None

    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_decision(text):
    if text is None:
        return None
    match = re.search(r"Decision\s+(.+?)\s+Notification", text)
    if match:
        return match.group(1).strip()
    return None

def extract_notification_date(text):
    # Looks like: "Notification on 27/01/2026 via E-mail"
    if text is None:
        return None
    match = re.search(r"Notification\s+on\s+(\d{2}/\d{2}/\d{4})", text)
    if match:
        return match.group(1)
    return None

def extract_degree_type(text):
    # Looks like: "Degree Type PhD"
    if text is None:
        return None
    match = re.search(r"Degree\s+Type\s+([A-Za-z\.]+)", text)
    if match:
        return match.group(1)
    return None

def extract_country_origin(text):
    # Looks like: "Degree's Country of Origin International"
    if text is None:
        return None
    match = re.search(r"Degree's\s+Country\s+of\s+Origin\s+([A-Za-z]+)", text)
    if match:
        return match.group(1)
    return None

def extract_undergrad_gpa(text):
    # Looks like: "Undergrad GPA 3.92"
    if text is None:
        return None
    match = re.search(r"Undergrad\s+GPA\s+([0-4]\.\d{1,2})", text)
    if match:
        return match.group(1)
    return None

def extract_gre_general(text):
    # Looks like: "GRE General: 320" (sometimes 0)
    if text is None:
        return None
    match = re.search(r"GRE\s+General:\s*([0-9]+)", text)
    if match:
        return match.group(1)
    return None

def extract_gre_verbal(text):
    # Looks like: "GRE Verbal: 160"
    if text is None:
        return None
    match = re.search(r"GRE\s+Verbal:\s*([0-9]+)", text)
    if match:
        return match.group(1)
    return None

def extract_gre_aw(text):
    # Looks like: "Analytical Writing: 4.50"
    if text is None:
        return None
    match = re.search(r"Analytical\s+Writing:\s*([0-6](?:\.\d{1,2})?)", text)
    if match:
        return match.group(1)
    return None

def extract_term_year(text):
    # Sometimes appears in notes like "Fall 2026"
    if text is None:
        return None
    match = re.search(r"\b(Spring|Summer|Fall|Autumn|Winter)\s+(20\d{2})\b", text, re.IGNORECASE)
    if match:
        return match.group(1).title() + " " + match.group(2)
    return None

# Load raw scraped data from scrape.py
with open("raw.json", "r", encoding="utf-8") as f:
    extracted_fields_raw = json.load(f)

for row in extracted_fields_raw:
    row['program_raw'] = clean_whitespace(row.get('program_raw'))
    row['comments_raw'] = clean_whitespace(row.get('comments_raw'))
    row['status_raw'] = clean_whitespace(row.get('status_raw'))
    row['result_text_raw'] = clean_whitespace(row.get('result_text_raw'))

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

llm_cleaned = llm_response_python['rows']

for i in range(len(extracted_fields_raw)):
    extracted_fields_raw[i]['program_clean'] = llm_cleaned[i].get('llm-generated-program')
    extracted_fields_raw[i]['university_clean'] = llm_cleaned[i].get('llm-generated-university')

for row in extracted_fields_raw:
    text = row.get('result_text_raw')

    decision = extract_decision(text)
    notification_date = extract_notification_date(text)

    if decision is not None:
        decision = decision.title()
    row['Applicant Status'] = decision

    # Map accepted/rejected dates
    if decision == "Accepted":
        row['Accepted: Acceptance Date'] = notification_date
        row['Rejected: Rejection Date'] = None
    elif decision == "Rejected":
        row['Accepted: Acceptance Date'] = None
        row['Rejected: Rejection Date'] = notification_date
    else:
        row['Accepted: Acceptance Date'] = None
        row['Rejected: Rejection Date'] = None

    row['Masters or PhD (if available)'] = extract_degree_type(text)

    origin = extract_country_origin(text)
    if origin == "Domestic":
        origin = "American"

    row['International / American Student (if available)'] = origin
    row['GPA (if available)'] = extract_undergrad_gpa(text)
    row['GRE Score (if available)'] = extract_gre_general(text)
    row['GRE V Score (if available)'] = extract_gre_verbal(text)
    row['GRE AW (if available)'] = extract_gre_aw(text)
    row['Semester and Year of Program Start (if available)'] = extract_term_year(text)

for row in extracted_fields_raw:
    if 'result_text_raw' in row:
        del row['result_text_raw']

with open('clean.json', 'w', encoding='utf-8') as f:
    json.dump(extracted_fields_raw, f, ensure_ascii=False, indent=2)

print('Wrote clean.json')
print(extracted_fields_raw[0])