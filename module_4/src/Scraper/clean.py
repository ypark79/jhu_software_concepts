"""Clean scraped GradCafe data and load into JSON/PostgreSQL."""

from urllib.request import urlopen, Request
import json
import re
import time
import os
from datetime import datetime
import psycopg

# Create batches of data to control volume of data being cleaned.
# Avoids overwhelming the LLM.
def chunked(lst, size):
    """Yield chunks of a list with a fixed size."""
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

# Get rid of unnecessary whitespace and make spacing uniform to avoid
# issues while parsing.
def clean_whitespace(text):
    """Normalize whitespace; return None for None input."""
    if text is None:
        return None

    # REGEX to make everything one space apart.
    text = re.sub(r"\s+", " ", str(text))
    return text.strip()


# Clean up the extracted Program data. Isolate it by eliminating any
# unnecessary data around it. Standardize the spacing as well.
# This avoids issues when the local LLM cleans the Program entries.
def clean_program_cell(program_text):
    """Strip extra info from the program cell."""
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


# This prevents any form of zero to represent an actual GRE score
# or GPA. If its any form of 0, then it means a score/GPA was not
# provided.
def normalize_zero(value):
    """Convert zero-like strings to None."""
    if value is None:
        return None

    val_str = str(value).strip()
    if val_str in {"0", "0.0", "0.00"}:
        return None

    return value

# Extract the data from the notes/comments section of each student
# application.
def extract_notes(text):
    """Extract the Notes section from result text."""
    if text is None:
        return None
    # REGEX code finds the word "Notes" and isolates all data
    # after that.
    # and before "Timeline." This will be the comments data.
    match = re.search(r"Notes\s+(.*?)\s+Timeline", text, re.DOTALL)
    if match:
        # Standardize spacing of the comments data.
        notes = match.group(1).strip()
        notes = re.sub(r"\s+", " ", notes)
        return notes
    return None


# Extract the data for the "Decision" section of each
# student application.
def extract_decision(text):
    """Extract decision text (Accepted/Rejected/etc.)."""
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
    """Extract notification date in MM/DD/YYYY format."""
    if text is None:
        return None
    # Search for "Notification on" and use REGEX code to extract
    # the date time group. Use REGEX to standardize the
    # date format as MM/DD/YYYY.
    match = re.search(r"Notification\s+on\s+(\d{2}/\d{2}/\d{4})", text)
    if match:
        return match.group(1)
    return None


# Search for the word "Degree Type" and standardize the format only
# allowing letters and periods.
def extract_degree_type(text):
    """Extract degree type (e.g., MS, PhD)."""
    if text is None:
        return None
    match = re.search(r"Degree\s+Type\s+([A-Za-z\.]+)", text)
    if match:
        return match.group(1)
    return None

# Search for "Degree's Country of Origin" and standardize if to Domestic
# and Foreign.
def extract_country_origin(text):
    """Extract country of origin (Domestic/International)."""
    if text is None:
        return None
    match = re.search(r"Degree's\s+Country\s+of\s+Origin\s+([A-Za-z]+)", text)
    if match:
        return match.group(1)
    return None


# Search for Undergrad GPA and extract score.Standardize score to
# single digit, period, and then one to two digits.
def extract_undergrad_gpa(text):
    """Extract undergrad GPA from text."""
    if text is None:
        return None
    match = re.search(r"Undergrad\s+GPA\s+([0-4]\.\d{1,2})", text)
    if match:
        return match.group(1)
    return None


# Search for General GRE score and standardize numbering.
def extract_gre_general(text):
    """Extract GRE general score from text."""
    if text is None:
        return None
    match = re.search(r"GRE\s+General:\s*([0-9]+)", text)
    if match:
        return match.group(1)
    return None


# Search for GRE verbal score and standardize numbering.
def extract_gre_verbal(text):
    """Extract GRE verbal score from text."""
    if text is None:
        return None
    match = re.search(r"GRE\s+Verbal:\s*([0-9]+)", text)
    if match:
        return match.group(1)
    return None


# Search GRE Analytical Writing score and standardize numbering to one
# digit, period, one digit.
def extract_gre_aw(text):
    """Extract GRE analytical writing score from text."""
    if text is None:
        return None
    match = re.search(r"Analytical\s+Writing:\s*([0-6](?:\.\d{1,2})?)", text)
    if match:
        return match.group(1)
    return None


# Search for the academic term and year. Standardize with "term" and 4
# digit year.
def extract_term_year(text):
    """Extract term and year, normalizing Autumn to Fall."""
    if text is None:
        return None
    match = re.search(r"\b(Spring|Summer|Fall|Autumn|Winter)\s+"
                      r"(20\d{2})\b", text, re.IGNORECASE)
    if match:
        term = match.group(1).title()
        if term == "Autumn":
            term = "Fall"
        return f"{term} {match.group(2)}"
    return None


# Loads the dirty dataset produced by scrape.py and converts to Python
# to prepare data to be cleaned.
def load_data(input_path="raw_scraped_data.json"):
    """Load raw scraped rows from JSON."""
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except Exception:
        return []


# Takes final cleaned data set, converts to JSON and writes to the file
# name as outlined in assignment instructions.
def save_data(final_rows, output_path):
    """Save cleaned rows to JSON."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_rows, f, ensure_ascii=False, indent=2)


# Sends batches of data in chunks to the local LLM
# provided by the instructor.
# to avoid overwhelming the LLM.
#
# Stands by for results to come back, parses the data, and then sends
# another chunk
def _llm_post_rows(llm_url: str, rows_payload: list[dict],
                   timeout_s: int = 300) -> list[dict]:
    """Send rows to the local LLM and return cleaned results."""

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

# Takes raw dataset rows from scrape.py, extracts desired entry
# text, extracts desired entry text from "Notes" section inside
# student URL links, sends program and university names to local
# LLM (app.py) to clean, and produces two json outputs.
def clean_data(extracted_fields_raw,
               llm_url="http://127.0.0.1:8000/standardize"):
    """Clean raw rows and return cleaned outputs."""

    # Standardize formatting by calling clean_whitespace to remove
    # unnecessary whitespace and standardize spacing.
    for row in extracted_fields_raw:
        row["program_raw"] = clean_whitespace(row.get("program_raw"))
        row["comments_raw"] = clean_whitespace(row.get("comments_raw"))
        row["status_raw"] = clean_whitespace(row.get("status_raw"))
        row["result_text_raw"] = clean_whitespace(row.get("result_text_raw"))

    # Extract and clean Program data
    for row in extracted_fields_raw:
        row["program_raw"] = clean_program_cell(row.get("program_raw"))

    # Prepare and package program and university data to send to app.py
    # Execute deduplication to ensure program-university pairs are sent
    # to llm only once.
    llm_inputs = []

    # Create a dictionary where the key is a program-university pair.
    # The value is a list of row indices where that pair appears.
    # This ensures only one program-uni pair goes into the local LLM.
    # Once cleaned, results are mapped back to all matching rows.
    llm_key_to_indices = {}

    # Iterate over all scraped rows of uncleaned data. Enumerate
    # to add an index for mapping later in code.
    for i, row in enumerate(extracted_fields_raw):
        # Extract university and program names from raw data
        # and account when info is not available.
        uni = row.get("university_raw") or ""
        prog = row.get("program_raw") or ""

        # Pair up the program and university to ensure they're printed
        # in the outputs as per the assignment sample output.
        llm_input_str = f"{prog}, {uni}".strip().strip(",")

        llm_inputs.append(llm_input_str)

        # This facilitates deduplication to ensure only one prog-uni
        # pair gets sent to the local llm. This portion of code
        # tracks all the rows in which a unique program-university
        # pair exists.
        if llm_input_str not in llm_key_to_indices:
            llm_key_to_indices[llm_input_str] = []
        llm_key_to_indices[llm_input_str].append(i)

    # The keys are the prog-uni pairs. keys() method pulls out all
    # these pairs and list() puts them in a list. These will be the
    # deduplicated prog-uni pairs that are sent into the local llm.
    unique_llm_inputs = list(llm_key_to_indices.keys())

    # Print total inputs vs unique (deduped) inputs to show how much the
    # LLM workload is reduced by deduplication.
    print(f"LLM inputs total: {len(llm_inputs)}")
    print(f"LLM inputs unique (deduped): {len(unique_llm_inputs)}")

    # Package each unique "program, university" string under
    # the key "program"
    # to match the input format expected by the local LLM (app.py).
    unique_payload_rows = [{"program": s} for s in unique_llm_inputs]

    # Through trial and error, batch size of 100 allows clean run of all
    # 30,000 entries.
    chunk_size = 100
    # Results aligned with unique_payload_rows order
    unique_results = []

    # Call def chunked() to send batches of 100 of the prog-uni pairs
    # to the local LLM. Call def _llm_post_rows to receive the cleaned
    # batch and then add to unique_results. Print progress check.
    for batch in chunked(unique_payload_rows, chunk_size):
        cleaned_batch = _llm_post_rows(llm_url, batch, timeout_s=300)
        unique_results.extend(cleaned_batch)
        print(f"Progress (unique LLM): "
              f"{len(unique_results)} / {len(unique_payload_rows)}")

    # Create a lookup of original prog-uni pairs to cleaned pairs.
    # This lets us map cleaned results back to all matching rows.
    llm_lookup = {}
    for i, row_out in enumerate(unique_results):
        # Connect original prog-uni pair to the llm-cleaned pair.
        src_key = unique_llm_inputs[i]
        prog_clean = row_out.get("llm-generated-program")
        uni_clean = row_out.get("llm-generated-university")
        # Store original prog-uni and post-llm cleaned prog uni-pair
        # into dictionary
        llm_lookup[src_key] = (prog_clean, uni_clean)

    # Use llm lookup dictionary to produce the llm-cleaned programs
    # and universities
    for i, src in enumerate(llm_inputs):
        prog_clean, uni_clean = llm_lookup.get(src, (None, None))
        extracted_fields_raw[i]["program_clean"] = prog_clean
        extracted_fields_raw[i]["university_clean"] = uni_clean

    # This block of code is going to extract and clean the required
    # data fields pulled from the raw "notes" section from the URLs
    # in the student applications.
    for row in extracted_fields_raw:
        text = row.get("result_text_raw")

        # Call extract_decision() function to pull out decision text if
        # student was accepted or not. Same for notification_date
        decision = extract_decision(text)
        notification_date = extract_notification_date(text)

        # Standardizes formatting of the word "accepted" by using
        # the title function (capitalizes first letter and rest of the
        # word is lower case.
        if decision is not None:
            decision = decision.title()

        # Standardizes formatting of decision and notification_date
        # as per the assignment sample output. If both data fields
        # exist, they are paired. If only decision exists, then it
        # will say "Accepted".
        # "Accepted"
        if decision is not None and notification_date is not None:
            row["Applicant Status"] = f"{decision} on {notification_date}"
        elif decision is not None:
            row["Applicant Status"] = decision
        else:
            row["Applicant Status"] = None

        # Populate accepted/rejected with their respective dates in the
        # dictionary.
        if decision == "Accepted":
            row["Accepted: Acceptance Date"] = notification_date
            row["Rejected: Rejection Date"] = None
        elif decision == "Rejected":
            row["Accepted: Acceptance Date"] = None
            row["Rejected: Rejection Date"] = notification_date
        else:
            row["Accepted: Acceptance Date"] = None
            row["Rejected: Rejection Date"] = None

        # call extract_degree_type() to extract type of degree text
        row["Masters or PhD (if available)"] = extract_degree_type(text)

        # Format origin of degree to be either Domestic or American
        # as per assignment sample output.
        origin = extract_country_origin(text)
        if origin == "Domestic":
            origin = "American"

        # Extra remaining fields and populate dictionary.
        row["Comments (if available)"] = extract_notes(text)
        row["International / American Student (if available)"] = origin
        row["GPA (if available)"] = extract_undergrad_gpa(text)
        row["GRE Score (if available)"] = extract_gre_general(text)
        row["GRE V Score (if available)"] = extract_gre_verbal(text)
        row["GRE AW (if available)"] = extract_gre_aw(text)
        term = row.get("term_inferred") or extract_term_year(text)
        row["Semester and Year of Program Start (if available)"] = term

    # Final step to package data and print the two required json files.
    final_rows = []

    for row in extracted_fields_raw:

        prog = row.get("program_clean")
        uni = row.get("university_clean")

        # Combine the program and university to match sample output.
        # Account for unavailable data fields.
        if prog and uni:
            combined_program = f"{prog}, {uni}"
        elif prog:
            combined_program = prog
        elif uni:
            combined_program = uni
        else:
            combined_program = None

        # Final rows required to generate the two required json files.
        final_row = {
            "result_id": row.get("result_id"),
            "program": combined_program,
            "comments": row.get("Comments (if available)"),
            "date_added": row.get("date_added_raw"),
            "url": row.get("application_url_raw"),
            "status": row.get("Applicant Status"),
            "term": row.get("Semester and Year of Program Start "
                            "(if available)"),
            "US/International": row.get("International / American Student "
                                        "(if available)"),
            "GRE Score": normalize_zero(row.get("GRE Score "
                                                "(if available)")),
            "GRE V Score": normalize_zero(row.get("GRE V Score "
                                                  "(if available)")),
            "Degree": row.get("Masters or PhD (if available)"),
            "GPA": normalize_zero(row.get("GPA (if available)")),
            "GRE AW": normalize_zero(row.get("GRE AW (if available)")),
            "llm-generated-program": row.get("program_clean"),
            "llm-generated-university": row.get("university_clean"),
        }

        final_rows.append(final_row)

    # applicant_data.json does not have the llm-generated program
    # and university. Use .pop() to remove them.
    final_rows_no_llm = []
    for r in final_rows:
        r2 = dict(r)
        r2.pop("llm-generated-program", None)
        r2.pop("llm-generated-university", None)
        final_rows_no_llm.append(r2)

    # Verify the same number of rows were produced.
    print(f"Final rows written: "
          f"{len(final_rows)} / {len(extracted_fields_raw)}")
    return extracted_fields_raw, final_rows, final_rows_no_llm

# Convert date strings into Python date objects so they can be inserted
# into PostgreSQL. If no date is provided, code will return NONE
# in Python and database will store as NULL.
def _parse_date(date_str):
    """Parse a date string into a date; return None if invalid."""

    if not date_str:
        return None

    try:
        return datetime.strptime(
            date_str.strip(),
            "%B %d, %Y"
        ).date()
    except Exception:
        # If parsing fails, store NULL instead of crashing
        return None

# Convert string numbers into floats.
def _to_float(x):
    """Convert to float; return None if invalid."""

    if x is None:
        return None

    try:
        return float(x)
    except Exception:
        return None

# Add newly scraped data to the oriignal 30K entry JSON file.
# Add newly scraped data to the original master JSON file.
def append_rows_to_master(new_rows,
                          master_path="llm_extend_applicant_data.json"):
    """Append new rows to the master JSON file with dedupe."""

    master_rows = load_data(master_path)

    existing_ids = {
        r.get("result_id")
        for r in master_rows
        if r.get("result_id") is not None
    }

    rows_to_add = []

    # Only add rows not already in master file
    for r in new_rows:
        rid = r.get("result_id")
        if rid is None:
            continue

        if rid not in existing_ids:
            rows_to_add.append(r)
            existing_ids.add(rid)

    # Put newest rows at the top
    master_rows = rows_to_add + master_rows

    save_data(master_rows, master_path)
    print(f"Appended {len(rows_to_add)} new rows to master JSON")

    # Return newly added rows
    return rows_to_add

# Insert cleaned new entries from gradcafe into PostgreSQL applicant
# database automatically once cleaning is complete.
# Only newly acquired rows will get inserted to avoid duplicates.

def insert_rows_into_postgres(rows, table_name="applicants"):
    """Insert cleaned rows into PostgreSQL with upsert."""

    # If there is nothing new to insert, stop early.
    if not rows:
        print("No new rows to insert into Postgres.")
        return 0

    # Database connection settings.
    # These default values work for local setup,
    # but environment variables can override them.
    dbname = os.getenv("PGDATABASE", "module_3")
    user = os.getenv("PGUSER", "youngminpark")
    password = os.getenv("PGPASSWORD")  # often None locally
    host = os.getenv("PGHOST", "localhost")
    port = int(os.getenv("PGPORT", "5432"))

    # Connect to PostgreSQL
    conn = psycopg.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port,
    )

    # SQL insert statement.
    # ON CONFLICT prevents duplicates.
    sql = f"""
    INSERT INTO {table_name} (
        result_id,
        program,
        comments,
        date_added,
        url,
        status,
        term,
        us_or_international,
        gpa,
        gre,
        gre_v,
        gre_aw,
        degree,
        llm_generated_program,
        llm_generated_university
    )
    VALUES (
        %(result_id)s,
        %(program)s,
        %(comments)s,
        %(date_added)s,
        %(url)s,
        %(status)s,
        %(term)s,
        %(us_or_international)s,
        %(gpa)s,
        %(gre)s,
        %(gre_v)s,
        %(gre_aw)s,
        %(degree)s,
        %(llm_generated_program)s,
        %(llm_generated_university)s
    )
    ON CONFLICT (result_id) DO UPDATE SET
    term = COALESCE(applicants.term, EXCLUDED.term),
    us_or_international = COALESCE(applicants.us_or_international, 
    EXCLUDED.us_or_international),
    gpa = COALESCE(applicants.gpa, EXCLUDED.gpa),
    gre = COALESCE(applicants.gre, EXCLUDED.gre),
    gre_v = COALESCE(applicants.gre_v, EXCLUDED.gre_v),
    gre_aw = COALESCE(applicants.gre_aw, EXCLUDED.gre_aw),
    degree = COALESCE(applicants.degree, EXCLUDED.degree),
    llm_generated_program = COALESCE(
        applicants.llm_generated_program,
        EXCLUDED.llm_generated_program
    ),
    llm_generated_university = COALESCE(
        applicants.llm_generated_university,
        EXCLUDED.llm_generated_university
    );
    """

    inserted = 0

    try:
        # "with conn" auto-commits changes safely
        with conn:
            # Cursor is used to execute SQL commands
            with conn.cursor() as cur:

                # Insert each cleaned row
                for i, r in enumerate(rows, start=1):
                    # Skip rows that do not have a unique result_id.
                    rid = r.get("result_id")
                    if rid is None:
                        continue

                    # Convert JSON data into database-ready values
                    params = {
                        "result_id": rid,
                        "program": r.get("program"),
                        "comments": r.get("comments"),
                        "date_added": _parse_date(r.get("date_added")),
                        "url": r.get("url"),
                        "status": r.get("status"),
                        "term": r.get("term"),
                        "us_or_international": r.get("US/International"),
                        "gpa": _to_float(r.get("GPA")),
                        "gre": _to_float(r.get("GRE Score")),
                        "gre_v": _to_float(r.get("GRE V Score")),
                        "gre_aw": _to_float(r.get("GRE AW")),
                        "degree": r.get("Degree"),
                        "llm_generated_program": r.get(
                            "llm-generated-program"
                        ),
                        "llm_generated_university": r.get(
                            "llm-generated-university"
                        ),
                    }

                    cur.execute(sql, params)
                    inserted += cur.rowcount

                    # Progress print.
                    if i % 100 == 0 or i == len(rows):
                        print(f"Postgres progress: {i}/{len(rows)} "
                              f"rows processed")

        print(f"Inserted {inserted} new rows into PostgreSQL.")
        return inserted

    finally:
        # Close connection
        conn.close()

def main():
    """Run clean -> append -> save -> insert pipeline."""
    # Clean newly scraped rows
    extracted_fields_raw, final_rows, final_rows_no_llm = clean_data(
        load_data("raw_scraped_data.json")
    )

    # Update master JSON file
    new_rows_added = append_rows_to_master(
        final_rows,
        "llm_extend_applicant_data.json"
    )

    # Keeping original final output for mod_2 just in case.
    save_data(final_rows_no_llm, "applicant_data.json")

    # Push only new rows to database
    insert_rows_into_postgres(final_rows)


if __name__ == "__main__":
    main()