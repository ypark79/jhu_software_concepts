import json
import psycopg
from datetime import datetime

database_name = "module_3"
json_file = "llm_extend_applicant_data.json"

# Ensure all data in JSON file are acceptable by SQL
#
# If data is not provided, JSON file says "null" and python will read
# as "None." "NULL" must be returned for SQL.
#
# JSON file has the dates as a string. Must be converted into an
# actual date using datetime.
def fix_date(date_str):
    if date_str is None:
        return "NULL"
    try:
        d = datetime.strptime(str(date_str).strip(), "%B %d, %Y").date()
        return f"'{d}'"
    except ValueError:
        return "NULL"

# Convert strings into floats for specified data fields.
def fix_float(num_value):
    if num_value is None:
        return "NULL"

    try:
        return str(float(num_value))
    except ValueError:
        return "NULL"

def fix_text(value):
    if value is None:
        return "NULL"
    # If the data field has a word with an apostrophe, it will isolate that
    # word and forget about the rest of the entry. This replaces all
    # apostrophes with a double apostrophe so the whole entry is
    # captured.
    text = str(value).replace("'", "''")
    return f"'{text}'"

def main():
    connection = psycopg.connect(dbname = database_name, host = "localhost")
    with connection.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS applicants (
            p_id INTEGER PRIMARY KEY,
            program TEXT,
            comments TEXT,
            date_added DATE,
            url TEXT,
            status TEXT,
            term TEXT,
            us_or_international TEXT,
            gpa FLOAT,
            gre FLOAT,
            gre_v FLOAT,
            gre_aw FLOAT,
            degree TEXT,
            llm_generated_program TEXT,
            llm_generated_university TEXT
        );
        """)

        with open(json_file, "r", encoding = "utf-8") as f:
            data = json.load(f)

        inserted = 0

        for p_id, row in enumerate(data, start=1):

            sql = f"""
            INSERT INTO applicants VALUES (
                {p_id},
                {fix_text(row.get("program"))},
                {fix_text(row.get("comments"))},
                {fix_date(row.get("date_added"))},
                {fix_text(row.get("url"))},
                {fix_text(row.get("status"))},
                {fix_text(row.get("term"))},
                {fix_text(row.get("US/International"))},
                {fix_float(row.get("GPA"))},
                {fix_float(row.get("GRE Score"))},
                {fix_float(row.get("GRE V Score"))},
                {fix_float(row.get("GRE AW"))},
                {fix_text(row.get("Degree"))},
                {fix_text(row.get("llm-generated-program"))},
                {fix_text(row.get("llm-generated-university"))}
            );
            """

            cur.execute(sql)
            inserted += 1

    connection.commit()
    connection.close()

    print(f"Loaded {inserted} rows into applicants.")

if __name__ == "__main__":
    main()

