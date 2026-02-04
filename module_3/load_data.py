import json
from datetime import datetime
from db_connection import get_connection

# JSON file was put into a subfolder named Data for organization.
json_file = "data/llm_extend_applicant_data.json"

# Convert date entries from strings into Python date objects to enable
# PostgreSQL compatibility.
def parse_date(date_str):

    if not date_str:
        return None
    try:
        return datetime.strptime(str(date_str).strip(), "%B %d, %Y").date()
    except ValueError:
        return None

# Convert GPA/GRE entries from strings into Python floats to enable
# PostgreSQL compatibility.
def try_float(value):

    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def main():
    # Use the centralized utility from db_connection.py to open a session
    connection = get_connection()

    if connection is None:
        print("Database connection failed. Aborting load.")
        return

    # Create the table structure for the database first. Match the field names
    # and data types with the sample in the assignment.
    try:
        with connection.cursor() as cur:
            # Create the 'applicants' table schema if it doesn't exist.
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

            # TRUNCATE TABLE empties the table of all previous entries.
            # Allows to repopulate the module_3 table with fresh data.
            cur.execute("TRUNCATE TABLE applicants;")
            print("Table cleared. Starting fresh data load...")

            # Load data from llm_extend_applicant_data.json
            with open(json_file, "r", encoding="utf-8") as f:

                data = json.load(f)

            inserted = 0

            # Iterate through JSON objects and map them to the table columns
            # Loop through the rows and set p_id to start as 1 to assign
            # unique IDs to each applicant.
            for p_id, row in enumerate(data, start=1):
                # Use parameterized query placeholders (%s) to avoid
                # issues with apostrophes and 'None' values. psycopg automatically
                # resolves these issues. psychopg automatically fixes apostrophes
                # and turns None into NULL for SQL insertion. Use 15 placeholders
                # to match 15 entries.

                sql = """
                    INSERT INTO applicants VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    );
                """

                # Extract values from the JSON dictionary using the exact keys
                # seen in the 'llm_extend_applicant_data.json' file.
                values = (
                    p_id,
                    row.get("program"),
                    row.get("comments"),
                    parse_date(row.get("date_added")),
                    row.get("url"),
                    row.get("status"),
                    row.get("term"),
                    row.get("US/International"),
                    try_float(row.get("GPA")),
                    try_float(row.get("GRE Score")),
                    try_float(row.get("GRE V Score")),
                    try_float(row.get("GRE AW")),
                    row.get("Degree"),
                    row.get("llm-generated-program"),
                    row.get("llm-generated-university")
                )

                cur.execute(sql, values)
                inserted += 1

        # Commit inserts into database.
        connection.commit()
        print(f"Successfully loaded {inserted} rows into 'applicants'.")

    except Exception as e:
        # If an error occurs (e.g., schema mismatch), rollback the transaction
        print(f"An error occurred during data load: {e}")
        connection.rollback()
    finally:
        # Close the connection regardless of success or failure
        connection.close()


if __name__ == "__main__":
    main()

