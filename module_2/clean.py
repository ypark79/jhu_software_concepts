from urllib.request import urlopen, Request
import json
import re
import time

# Create batches of data to control volume of data being cleaned.
# Avoids overwhelming the LLM.
def chunked(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

# Get rid of unnecessary whitespace and make spacing uniform to avoid
# issues while parsing.
def clean_whitespace(text):
    if text is None:
        return None

    # REGEX to make everything one space apart.
    text = re.sub(r"\s+", " ", str(text))
    return text.strip()


# Clean up the extracted Program data. Isolate it by eliminating any
# unnecessary data around it. Standardize the spacing as well. This avoid
# issues when the local LLM cleans the Program entries.
def clean_program_cell(program_text):
    if program_text is None:
        return None

    program_text = clean_whitespace(program_text)

    # Remove all data not related to the student's program.
    split_words = [
        " Accepted", " Rejected", " Interview", " Wait",
        " Fall ", " Spring ", " Summer ", " Winter ",
        " International", " Domestic", " GPA", " Gpa", " GRE"
    ]
    for w in split_words:
        idx = program_text.find(w)
        if idx != -1:
            program_text = program_text[:idx].strip()
            break

    return program_text


# Standardize the zeroes and decimals of all GPA test scores and GPAs.
def normalize_zero(value):
    if value is None:
        return None

    val_str = str(value).strip()
    if val_str in {"0", "0.0", "0.00"}:
        return None

    return value

# Extract the data from the notes/comments section of each student
# application.
def extract_notes(text):
    if text is None:
        return None
    # REGEX code to finds the word "Notes" and isolates all data after that
    # and before "Timeline." This will be the comments data.
    match = re.search(r"Notes\s+(.*?)\s+Timeline", text, re.DOTALL)
    if match:
        # Standardize spacing of the comments data.
        notes = match.group(1).strip()
        notes = re.sub(r"\s+", " ", notes)
        return notes
    return None


# Extract the data for the "Decision" section of each student application.
def extract_decision(text):
    if text is None:
        return None
    # Find all the "Decision" text and isolate everything after it and
    # before "Notification.
    match = re.search(r"Decision\s+(.+?)\s+Notification", text)
    if match:
        return match.group(1).strip()
    return None


# Extract the students' notification_date data.
def extract_notification_date(text):
    if text is None:
        return None
    # Search for the word "Notification on" and use REGEX code to extract
    # the date time group. Use REGEX to standardize date format is MM/DD/YYYY.
    match = re.search(r"Notification\s+on\s+(\d{2}/\d{2}/\d{4})", text)
    if match:
        return match.group(1)
    return None


# Search for the word "Degree Type" and standardize the format only
# allowing letters and periods.
def extract_degree_type(text):
    if text is None:
        return None
    match = re.search(r"Degree\s+Type\s+([A-Za-z\.]+)", text)
    if match:
        return match.group(1)
    return None

# Search for "Degree's Country of Origin" and standardize if to Domestic
# and Foreign.
def extract_country_origin(text):
    if text is None:
        return None
    match = re.search(r"Degree's\s+Country\s+of\s+Origin\s+([A-Za-z]+)", text)
    if match:
        return match.group(1)
    return None


# Search for Undergrad GPA and extract score.Standardize score to
# single digit, period, and then one to two digits.
def extract_undergrad_gpa(text):
    if text is None:
        return None
    match = re.search(r"Undergrad\s+GPA\s+([0-4]\.\d{1,2})", text)
    if match:
        return match.group(1)
    return None


# Search for General GRE score and standardize numbering.
def extract_gre_general(text):
    if text is None:
        return None
    match = re.search(r"GRE\s+General:\s*([0-9]+)", text)
    if match:
        return match.group(1)
    return None


# Search for GRE verbal score and standardize numbering.
def extract_gre_verbal(text):
    if text is None:
        return None
    match = re.search(r"GRE\s+Verbal:\s*([0-9]+)", text)
    if match:
        return match.group(1)
    return None


# Search GRE Analytical Writing score and standardize numbering to one
# digit, period, one digit.
def extract_gre_aw(text):
    if text is None:
        return None
    match = re.search(r"Analytical\s+Writing:\s*([0-6](?:\.\d{1,2})?)", text)
    if match:
        return match.group(1)
    return None


# Search for the academic term and year. Standardize with "term" and 4
# digit year.
def extract_term_year(text):
    if text is None:
        return None
    match = re.search(r"\b(Spring|Summer|Fall|Autumn|Winter)\s+(20\d{2})\b", text, re.IGNORECASE)
    if match:
        return match.group(1).title() + " " + match.group(2)
    return None


# Loads the dirty dataset produced by scrape.py and converts to Python
# to prepare data to be cleaned.
def load_data(input_path="raw_scraped_data.json"):
    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)


# Takes final cleaned data set, converts to JSON and writes to the file
# name as outlined in assignment instructions.
def save_data(final_rows, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_rows, f, ensure_ascii=False, indent=2)


# Sends batches of data in chunks to the local LLM provided by instructor
# to avoid overwhelming the LLM.
#
# Stands by for results to come back, parses the data, and then sends
# another chunk
def _llm_post_rows(llm_url: str, rows_payload: list[dict], timeout_s: int = 300) -> list[dict]:

    # Prepare payload for LLM as per format expected in app.py.
    # Convert to JSON and then to bytes to send over to LLM.
    payload = {"rows": rows_payload}
    payload_bytes = json.dumps(payload).encode("utf-8")

    # HTTP POST request.
    req = Request(
        llm_url,
        headers={"Content-Type": "application/json"},
        method="POST",
        data=payload_bytes
    )

    # Execute multiple retries in the case LLM fails or crashes.
    # Keep track of error explanations to help troubleshoot failures.
    last_err = None

    # Send HTTP request to LLM to get response. Decode JSON
    # into Python and prints error.
    for attempt in range(5):
        try:
            resp = urlopen(req, timeout=timeout_s)
            text = resp.read().decode("utf-8")
            obj = json.loads(text)
            out_rows = obj.get("rows")
            if out_rows is None:
                raise RuntimeError(f"LLM response missing 'rows': {obj}")
            return out_rows
        # Identifies errors after attempts and records error.
        except Exception as e:
            last_err = e
            wait = 2 ** attempt
            print(f"LLM request failed ({e}). Retrying in {wait}s...")
            time.sleep(wait)
    # Final error that cannot be resolved.
    raise RuntimeError(f"LLM batch failed after retries: {last_err}")


def clean_data(extracted_fields_raw, llm_url="http://127.0.0.1:8000/standardize"):
    # 1) Whitespace cleanup
    for row in extracted_fields_raw:
        row["program_raw"] = clean_whitespace(row.get("program_raw"))
        row["comments_raw"] = clean_whitespace(row.get("comments_raw"))
        row["status_raw"] = clean_whitespace(row.get("status_raw"))
        row["result_text_raw"] = clean_whitespace(row.get("result_text_raw"))

    # 2) Program cell cleanup
    for row in extracted_fields_raw:
        row["program_raw"] = clean_program_cell(row.get("program_raw"))

    # 3) Build LLM input strings
    # LLM expects key 'program' but your instructor LLM splits it into program/university.
    llm_inputs = []
    llm_key_to_indices = {}  # dedupe map: llm_input_string -> [row indices]

    for i, row in enumerate(extracted_fields_raw):
        uni = row.get("university_raw") or ""
        prog = row.get("program_raw") or ""
        llm_input_str = f"{prog}, {uni}".strip().strip(",")

        llm_inputs.append(llm_input_str)

        if llm_input_str not in llm_key_to_indices:
            llm_key_to_indices[llm_input_str] = []
        llm_key_to_indices[llm_input_str].append(i)

    # 4) DEDUPE before calling LLM (big speed improvement)
    unique_llm_inputs = list(llm_key_to_indices.keys())

    print(f"LLM inputs total: {len(llm_inputs)}")
    print(f"LLM inputs unique (deduped): {len(unique_llm_inputs)}")

    # Prepare LLM payload rows: [{"program": "..."}]
    unique_payload_rows = [{"program": s} for s in unique_llm_inputs]

    CHUNK_SIZE = 100  # keep same safe chunk size
    unique_results = []  # results aligned with unique_payload_rows order

    for batch in chunked(unique_payload_rows, CHUNK_SIZE):
        cleaned_batch = _llm_post_rows(llm_url, batch, timeout_s=300)
        unique_results.extend(cleaned_batch)
        print(f"Progress (unique LLM): {len(unique_results)} / {len(unique_payload_rows)}")

    # 5) Map unique LLM outputs back to all original rows
    # Build dict: llm_input_str -> (program_clean, university_clean)
    llm_lookup = {}
    for i, row_out in enumerate(unique_results):
        src_key = unique_llm_inputs[i]
        prog_clean = row_out.get("llm-generated-program")
        uni_clean = row_out.get("llm-generated-university")
        llm_lookup[src_key] = (prog_clean, uni_clean)

    for i, src in enumerate(llm_inputs):
        prog_clean, uni_clean = llm_lookup.get(src, (None, None))
        extracted_fields_raw[i]["program_clean"] = prog_clean
        extracted_fields_raw[i]["university_clean"] = uni_clean

    # 6) Extract fields from result_text_raw
    for row in extracted_fields_raw:
        text = row.get("result_text_raw")

        decision = extract_decision(text)
        notification_date = extract_notification_date(text)

        if decision is not None:
            decision = decision.title()

        if decision is not None and notification_date is not None:
            row["Applicant Status"] = f"{decision} on {notification_date}"
        elif decision is not None:
            row["Applicant Status"] = decision
        else:
            row["Applicant Status"] = None

        if decision == "Accepted":
            row["Accepted: Acceptance Date"] = notification_date
            row["Rejected: Rejection Date"] = None
        elif decision == "Rejected":
            row["Accepted: Acceptance Date"] = None
            row["Rejected: Rejection Date"] = notification_date
        else:
            row["Accepted: Acceptance Date"] = None
            row["Rejected: Rejection Date"] = None

        row["Masters or PhD (if available)"] = extract_degree_type(text)

        origin = extract_country_origin(text)
        if origin == "Domestic":
            origin = "American"

        row["Comments (if available)"] = extract_notes(text)
        row["International / American Student (if available)"] = origin
        row["GPA (if available)"] = extract_undergrad_gpa(text)
        row["GRE Score (if available)"] = extract_gre_general(text)
        row["GRE V Score (if available)"] = extract_gre_verbal(text)
        row["GRE AW (if available)"] = extract_gre_aw(text)
        row["Semester and Year of Program Start (if available)"] = extract_term_year(text)

    # 7) Remove large raw field before writing clean.json (optional but helps file size)
    for row in extracted_fields_raw:
        if "result_text_raw" in row:
            del row["result_text_raw"]

    # Intermediate output (helpful for debugging + assignment transparency)
    with open("clean.json", "w", encoding="utf-8") as f:
        json.dump(extracted_fields_raw, f, ensure_ascii=False, indent=2)

    # 8) Build final output rows in the required format

    final_rows = []

    for row in extracted_fields_raw:

        prog = row.get("program_clean")
        uni = row.get("university_clean")

        # Combine program + university into one field (comma-separated)
        if prog and uni:
            combined_program = f"{prog}, {uni}"
        elif prog:
            combined_program = prog
        elif uni:
            combined_program = uni
        else:
            combined_program = None

        final_row = {
            "program": combined_program,
            "comments": row.get("Comments (if available)"),
            "date_added": row.get("date_added_raw"),
            "url": row.get("application_url_raw"),
            "status": row.get("Applicant Status"),
            "term": row.get("Semester and Year of Program Start (if available)"),
            "US/International": row.get("International / American Student (if available)"),
            "GRE Score": normalize_zero(row.get("GRE Score (if available)")),
            "GRE V Score": normalize_zero(row.get("GRE V Score (if available)")),
            "Degree": row.get("Masters or PhD (if available)"),
            "GPA": normalize_zero(row.get("GPA (if available)")),
            "GRE AW": normalize_zero(row.get("GRE AW (if available)")),
            "llm-generated-program": row.get("program_clean"),
            "llm-generated-university": row.get("university_clean"),
        }

        final_rows.append(final_row)

    final_rows_no_llm = []
    for r in final_rows:
        r2 = dict(r)
        r2.pop("llm-generated-program", None)
        r2.pop("llm-generated-university", None)
        final_rows_no_llm.append(r2)

    print(f"Final rows written: {len(final_rows)} / {len(extracted_fields_raw)}")
    return extracted_fields_raw, final_rows, final_rows_no_llm


def main():
    extracted_fields_raw, final_rows, final_rows_no_llm = clean_data(
        load_data("raw_scraped_data.json")
    )

    # submission file 1 (includes llm-generated fields)
    save_data(final_rows, "llm_extend_applicant_data.json")

    # submission file 2 (final dataset without llm-generated fields)
    save_data(final_rows_no_llm, "applicant_data.json")


if __name__ == "__main__":
    main()