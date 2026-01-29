from urllib.request import urlopen, Request
import json
import re
import time


# -----------------------------
# Small helpers
# -----------------------------

def chunked(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def clean_whitespace(text):
    if text is None:
        return None
    text = re.sub(r"\s+", " ", str(text))
    return text.strip()


def clean_program_cell(program_text):
    if program_text is None:
        return None

    program_text = clean_whitespace(program_text)

    # If the cell contains decision info, split it off
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


def normalize_zero(value):
    if value is None:
        return None

    val_str = str(value).strip()
    if val_str in {"0", "0.0", "0.00"}:
        return None

    return value


# -----------------------------
# Validation filter (FIXED)
# -----------------------------


# -----------------------------
# Extractors from result_text_raw
# -----------------------------

def extract_notes(text):
    if text is None:
        return None
    match = re.search(r"Notes\s+(.*?)\s+Timeline", text, re.DOTALL)
    if match:
        notes = match.group(1).strip()
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
    if text is None:
        return None
    match = re.search(r"Notification\s+on\s+(\d{2}/\d{2}/\d{4})", text)
    if match:
        return match.group(1)
    return None


def extract_degree_type(text):
    if text is None:
        return None
    match = re.search(r"Degree\s+Type\s+([A-Za-z\.]+)", text)
    if match:
        return match.group(1)
    return None


def extract_country_origin(text):
    if text is None:
        return None
    match = re.search(r"Degree's\s+Country\s+of\s+Origin\s+([A-Za-z]+)", text)
    if match:
        return match.group(1)
    return None


def extract_undergrad_gpa(text):
    if text is None:
        return None
    match = re.search(r"Undergrad\s+GPA\s+([0-4]\.\d{1,2})", text)
    if match:
        return match.group(1)
    return None


def extract_gre_general(text):
    if text is None:
        return None
    match = re.search(r"GRE\s+General:\s*([0-9]+)", text)
    if match:
        return match.group(1)
    return None


def extract_gre_verbal(text):
    if text is None:
        return None
    match = re.search(r"GRE\s+Verbal:\s*([0-9]+)", text)
    if match:
        return match.group(1)
    return None


def extract_gre_aw(text):
    if text is None:
        return None
    match = re.search(r"Analytical\s+Writing:\s*([0-6](?:\.\d{1,2})?)", text)
    if match:
        return match.group(1)
    return None


def extract_term_year(text):
    if text is None:
        return None
    match = re.search(r"\b(Spring|Summer|Fall|Autumn|Winter)\s+(20\d{2})\b", text, re.IGNORECASE)
    if match:
        return match.group(1).title() + " " + match.group(2)
    return None


# -----------------------------
# Load / Save
# -----------------------------

def load_data(input_path="applicant_data.json"):
    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(final_rows, output_path="llm_extend_applicant_data.json"):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_rows, f, ensure_ascii=False, indent=2)


# -----------------------------
# LLM calling (DEDUPED for speed)
# -----------------------------

def _llm_post_rows(llm_url: str, rows_payload: list[dict], timeout_s: int = 300) -> list[dict]:
    """
    POST {'rows': [...]} to the local LLM.
    Returns the list under 'rows'.
    Retries included.
    """
    payload = {"rows": rows_payload}
    payload_bytes = json.dumps(payload).encode("utf-8")

    req = Request(
        llm_url,
        headers={"Content-Type": "application/json"},
        method="POST",
        data=payload_bytes
    )

    last_err = None
    for attempt in range(5):
        try:
            resp = urlopen(req, timeout=timeout_s)
            text = resp.read().decode("utf-8")
            obj = json.loads(text)
            out_rows = obj.get("rows")
            if out_rows is None:
                raise RuntimeError(f"LLM response missing 'rows': {obj}")
            return out_rows
        except Exception as e:
            last_err = e
            wait = 2 ** attempt
            print(f"LLM request failed ({e}). Retrying in {wait}s...")
            time.sleep(wait)

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

    CHUNK_SIZE = 300  # keep same safe chunk size
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
        final_row = {
            "program": row.get("program_clean"),
            "university": row.get("university_clean"),
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
        }

        final_rows.append(final_row)

    print(f"Final rows written: {len(final_rows)} / {len(extracted_fields_raw)}")
    return extracted_fields_raw, final_rows


def main():
    extracted_fields_raw = load_data("applicant_data.json")
    _, final_rows = clean_data(extracted_fields_raw)
    save_data(final_rows, "llm_extend_applicant_data.json")


if __name__ == "__main__":
    main()