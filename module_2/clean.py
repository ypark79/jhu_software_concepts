from urllib.request import urlopen, Request
import json
import re

def chunked(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

def clean_whitespace(text):
    if text is None:
        return None

    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def clean_program_cell(program_text):
    if program_text is None:
        return None

    # Collapse whitespace first
    program_text = clean_whitespace(program_text)

    # If the cell contains decision info, split it off
    split_words = [" Accepted", " Rejected", " Interview", " Wait", " Fall ", " Spring ", " Summer ", " Winter ", " International", " Domestic", " GPA", " Gpa", " GRE"]
    for w in split_words:
        idx = program_text.find(w)
        if idx != -1:
            program_text = program_text[:idx].strip()
            break

    return program_text
def normalize_zero(value):
    if value is None:
        return None

    # Convert to string for uniform checking
    val_str = str(value).strip()

    if val_str in {"0", "0.0", "0.00"}:
        return None

    return value

def is_valid_row(row):
    program = row.get("program")
    university = row.get("university")
    url = row.get("url")
    status = row.get("status")

    # Must have core fields
    if not program or not university or not url:
        return False

    # Program should not look like status text
    bad_program_tokens = ["Accepted", "Rejected", "Interview", "International", "Domestic", "GPA", "GRE"]
    for tok in bad_program_tokens:
        if tok in program:
            return False

    # University should look like a real institution
    if "University" not in university and "College" not in university and "Institute" not in university:
        return False

    return True

def extract_notes(text):
    # Extracts content between "Notes" and "Timeline"
    if text is None:
        return None

    match = re.search(r"Notes\s+(.*?)\s+Timeline", text, re.DOTALL)
    if match:
        notes = match.group(1).strip()
        # Clean excessive spaces
        notes = re.sub(r"\s+", " ", notes)
        return notes
    return None

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
def load_data(input_path="applicant_data.json"):
    # Load raw scraped data from scrape.py
    with open(input_path, "r", encoding="utf-8") as f:
        extracted_fields_raw = json.load(f)

    return extracted_fields_raw

def clean_data(extracted_fields_raw, llm_url="http://127.0.0.1:8000/standardize"):

    for row in extracted_fields_raw:
        row['program_raw'] = clean_whitespace(row.get('program_raw'))
        row['comments_raw'] = clean_whitespace(row.get('comments_raw'))
        row['status_raw'] = clean_whitespace(row.get('status_raw'))
        row['result_text_raw'] = clean_whitespace(row.get('result_text_raw'))

    for row in extracted_fields_raw:
        row['program_raw'] = clean_program_cell(row.get('program_raw'))

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
    CHUNK_SIZE = 300  # safe size for overnight run

    llm_cleaned = []

    for batch in chunked(inputs_for_llm, CHUNK_SIZE):
        payload = {'rows': batch}
        payload_json = json.dumps(payload)
        payload_bytes = payload_json.encode('utf-8')

        llm_request = Request(
            llm_url,
            headers={'Content-Type': 'application/json'},
            method='POST',
            data=payload_bytes
        )

        llm_response = urlopen(llm_request, timeout=300)
        llm_response_text = llm_response.read().decode('utf-8')
        llm_response_python = json.loads(llm_response_text)

        batch_cleaned = llm_response_python.get('rows')
        if batch_cleaned is None:
            raise RuntimeError(f"LLM response missing 'rows': {llm_response_python}")

        llm_cleaned.extend(batch_cleaned)

    for i in range(len(extracted_fields_raw)):
        extracted_fields_raw[i]['program_clean'] = llm_cleaned[i].get('llm-generated-program')
        extracted_fields_raw[i]['university_clean'] = llm_cleaned[i].get('llm-generated-university')

    for row in extracted_fields_raw:
        text = row.get('result_text_raw')

        decision = extract_decision(text)
        notification_date = extract_notification_date(text)

        if decision is not None:
            decision = decision.title()
        if decision is not None and notification_date is not None:
            row['Applicant Status'] = f"{decision} on {notification_date}"
        elif decision is not None:
            row['Applicant Status'] = decision
        else:
            row['Applicant Status'] = None

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

        row['Comments (if available)'] = extract_notes(text)
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

    final_rows = []

    for row in extracted_fields_raw:
        final_row = {}

        final_row["program"] = row.get("program_clean")
        final_row["university"] = row.get("university_clean")
        final_row["comments"] = row.get("Comments (if available)")
        final_row["date_added"] = row.get("date_added_raw")
        final_row["url"] = row.get("application_url_raw")

        # Status: Accepted / Rejected
        final_row["status"] = row.get("Applicant Status")

        # Term (semester + year)
        final_row["term"] = row.get("Semester and Year of Program Start (if available)")

        # US / International
        final_row["US/International"] = row.get("International / American Student (if available)")

        # GRE
        final_row["GRE Score"] = normalize_zero(row.get("GRE Score (if available)"))
        final_row["GRE V Score"] = normalize_zero(row.get("GRE V Score (if available)"))

        # Degree
        final_row["Degree"] = row.get("Masters or PhD (if available)")

        # GPA
        final_row["GPA"] = normalize_zero(row.get("GPA (if available)"))

        # GRE AW
        final_row["GRE AW"] = normalize_zero(row.get("GRE AW (if available)"))

        if is_valid_row(final_row):
            final_rows.append(final_row)
    return extracted_fields_raw, final_rows

def save_data(final_rows, output_path="llm_extend_applicant_data.json"):
    # Write final structured output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_rows, f, ensure_ascii=False, indent=2)

def main():
    extracted_fields_raw = load_data("applicant_data.json")
    extracted_fields_raw, final_rows = clean_data(extracted_fields_raw)
    save_data(final_rows, "llm_extend_applicant_data.json")

if __name__ == "__main__":
    main()
