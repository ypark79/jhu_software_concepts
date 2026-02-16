"""Run analysis queries and print results."""

from psycopg import sql
from db_connection import get_connection

def main():
    """Execute analysis queries and print results to the console."""
    # Use the centralized utility to open a session
    connection = get_connection()

    if connection is None:
        return

    with connection.cursor() as cur:
        # Number of entries that applied for Fall of 2026
        cur.execute("""
            SELECT COUNT(*)
            FROM applicants
            WHERE term ILIKE '%Fall 2026%'
            LIMIT 1;
        """)

        result = cur.fetchone()
        print("Entries for Fall 2026:", result[0])


        # Percentage of international applicants
        # Use FILTER to count only 'International' rows and then
        # divide by total count to get the percentage. ::DECIMAL is used
        # to convert the number into a decimal to avoid integer division
        # and enable decimal division to get an accurate percentage.
        cur.execute("""
            SELECT
                ROUND(
                    (COUNT(*) FILTER (WHERE us_or_international = 
                    'International'))::DECIMAL / 
                    NULLIF(COUNT(*), 0) * 100, 2
                )
            FROM applicants
            LIMIT 1;
        """)

        percentage = cur.fetchone()
        print(f"Percentage of international applicants: {percentage[0]}%")

        # Average GPA, GRE, GRE V, and GRE AW for those who
        # provided this data.
        # data. For those that did not, load_data.py ensured that empty
        # fields returned "NULL" for SQL.
        #
        # SQL AVG excludes NULL values, so AVG calculates the average
        # of all provided scores.
        # provided GPA/GRE scores. "::numeric" and ROUND are utilized to
        # ensure the averages are rounded to two decimal places.
        cur.execute("""
                    SELECT 
                        ROUND(AVG(gpa)::numeric, 2), 
                        ROUND(AVG(gre)::numeric, 2), 
                        ROUND(AVG(gre_v)::numeric, 2), 
                        ROUND(AVG(gre_aw)::numeric, 2) 
                    FROM applicants
                    LIMIT 1;
                """)

        averages = cur.fetchone()
        print(f"Average GPA: {averages[0]}")
        print(f"Average GRE: {averages[1]}")
        print(f"Average GRE V: {averages[2]}")
        print(f"Average GRE AW: {averages[3]}")



        # Average GPA of Fall 2026 American Students
        # Must filter out American students and application term.
        # The prompt does not specify, but we round the average to
        # two decimals using ROUND. ROUND will not work with a
        # FLOAT. "::numeric" converts the float to a decimal.
        # Add 'US' check and variations of the 2026 term.
        cur.execute("""
            SELECT ROUND(AVG(gpa)::numeric, 2)
            FROM applicants
            WHERE (us_or_international ILIKE 'Amer%' OR us_or_international 
            ILIKE 'US%')
            AND term ILIKE '%Fall 2026%'
            LIMIT 1;
        """)
        american_gpa_2026 = cur.fetchone()
        print(f"Average GPA of American/US students in Fall 2026: "
              f"{american_gpa_2026[0]}")


        # Percentage of Acceptances for the Fall 2025 term.
        # Numerator: Count rows where term is 'Fall 2025' AND
        # status contains 'Accepted'.
        # contains 'Accepted'. ILIKE accounts for case insensitivity.
        #
        # Denominator: Total count of all entries for 'Fall 2025'.
        # NULLIF prevents a crash by returning NULL if no Fall 2025
        # entries exist. ROUND and ::DECIMAL enable decimal division.
        cur.execute("""
            SELECT
                ROUND(
                    (
                        COUNT(*) FILTER (
                            WHERE term ILIKE '%Fall 2025%'
                            AND status ILIKE 'Accepted%'
                        )
                    )::DECIMAL /
                    NULLIF(
                        COUNT(*) FILTER (WHERE term ILIKE '%Fall 2025%'),
                        0
                    ) * 100,
                    2
                )
            FROM applicants
            LIMIT 1;
        """)

        acceptance_rate_2025 = cur.fetchone()

        if acceptance_rate_2025[0] is not None:
            print(f"Percentage of Accepted applicants for Fall 2025: "
                  f"{acceptance_rate_2025[0]}%")
        else:
            print("Percentage of Accepted applicants for Fall 2025: "
                  "N/A (No data for this term)")


        # Average GPA of Fall 2026 Acceptances
        # Filter for 'Fall 2026' and call AVG(). Account for case
        # insensitivity. For 'accepted' and enable rounding using
        # "::numeric"

        cur.execute("""
                SELECT ROUND(AVG(gpa)::numeric, 2)
                FROM applicants
                WHERE term ILIKE '%Fall 2026%' 
                AND status ILIKE 'Accepted%'
                LIMIT 1;
            """)

        avg_gpa_accepted_2026 = cur.fetchone()
        print(f"Average GPA of Fall 2026 Acceptances: "
              f"{avg_gpa_accepted_2026[0]}")


        # Number of applicants who applied to JHU for a MS in CS.
        # Based on load_data.py, the university name is stored in
        # 'llm_generated_university' and the major/program in
        # 'llm_generated_program'.
        # Account for different spellings of 'Johns Hopkins' and 'JHU'.
        cur.execute("""
            SELECT COUNT(*)
            FROM applicants
            WHERE (
                llm_generated_university ILIKE 'John%Hopkins%'
                OR llm_generated_university ILIKE '%JHU%'
            )
            AND (degree ILIKE 'Master%' OR degree = 'MS')
            AND llm_generated_program ILIKE '%Computer Science%'
            LIMIT 1;
        """)
        jhu_cs_masters_count = cur.fetchone()
        print(f"Number of applicants for JHU MS in CS: "
              f"{jhu_cs_masters_count[0]}")


        # Number of applicants from 2026 accepted to Georgetown,
        # MIT, Stanford, or CMU for a PhD in Computer Science.
        #
        # Status ILIKE 'Accepted%2026': Targets 2026 acceptances since
        # 'term' is null. Program: Checks for 'Computer Science' and
        # 'Phd' within the same string. Check variations of CMU and MIT.
        cur.execute("""
            SELECT COUNT(*)
            FROM applicants
            WHERE status ILIKE 'Accepted%'
            AND status LIKE '%/2026'
            AND (
                llm_generated_program ILIKE '%Computer Science%'
                AND (
                    llm_generated_program ILIKE '%Ph%d%'
                    OR degree ILIKE 'PhD%'
                )
            )
            AND (
                llm_generated_university ILIKE 'George%Town%'
                OR llm_generated_university ILIKE 'Stanford%'
                OR llm_generated_university ILIKE '%MIT%'
                OR llm_generated_university ILIKE
                    '%Massachusetts Institute of Technology%'
                OR llm_generated_university ILIKE 'Carnegie Mel%n%'
                OR llm_generated_university ILIKE '%CMU%'
            )
            LIMIT 1;
        """)
        top_tier_phd_count = cur.fetchone()
        print(f"Number of 2026 PhD CS acceptances "
              f"(GTown, MIT, Stanford, CMU): {top_tier_phd_count[0]}")

        # Answer to question 9 in assignment. First test: run the query
        # searching the "program" field from the original data.
        # Second test runs on llm_generated_program/university fields.
        # Here is the first test searching original data.
        cur.execute("""
            SELECT COUNT(*)
            FROM applicants
            WHERE status ILIKE 'Accepted%'
            AND status LIKE '%/2026'
            AND (
                program ILIKE '%Computer Science%'
                AND (program ILIKE '%Ph%d%' OR program ILIKE '%Doctor%')
            )
            AND (
                program ILIKE '%Georgetown%'
                OR program ILIKE '%Stanford%'
                OR program ILIKE '%MIT%'
                OR program ILIKE '%Massachusetts Institute of Technology%'
                OR program ILIKE '%Carnegie Mell%n%'
                OR program ILIKE '%CMU%'
            )
            LIMIT 1;
        """)
        original_fields_count = cur.fetchone()[0]

        # Here is the second test searching the llm_generated_program
        # and llm_generated_university fields.
        cur.execute("""
            SELECT COUNT(*)
            FROM applicants
            WHERE status ILIKE 'Accepted%'
            AND status LIKE '%/2026'
            AND (
                llm_generated_program ILIKE '%Computer Science%'
                AND (
                    llm_generated_program ILIKE '%Ph%d%'
                    OR degree ILIKE 'PhD%'
                )
            )
            AND (
                llm_generated_university ILIKE 'George%Town%'
                OR llm_generated_university ILIKE 'Stanford%'
                OR llm_generated_university ILIKE '%MIT%'
                OR llm_generated_university ILIKE
                    '%Massachusetts Institute of Technology%'
                OR llm_generated_university ILIKE 'Carnegie Mel%n%'
                OR llm_generated_university ILIKE '%CMU%'
            )
            LIMIT 1;
        """)
        llm_fields_count = cur.fetchone()[0]

        # Print results and the difference.
        print(f"PhD CS Acceptances (Original Fields): "
              f"{original_fields_count}")
        print(f"PhD CS Acceptances (LLM Fields):"
              f" {llm_fields_count}")
        print(f"Difference: {llm_fields_count - original_fields_count}.")


        # Self-Generated Question #1: How many American students
        # versus international students were accepted to JHU in 2026?
        cur.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE us_or_international = 'American') 
                AS american_count,
                COUNT(*) FILTER (WHERE us_or_international = 'International') 
                AS international_count
            FROM applicants
            WHERE (llm_generated_university ILIKE 'John%Hopkins%' OR 
            llm_generated_university ILIKE '%JHU%')
            AND status ILIKE 'Accepted%'
            AND status LIKE '%/2026'
            LIMIT 1;
        """)

        comparison = cur.fetchone()
        print("\nJHU 2026 Acceptance Comparison:")
        print(f" - American Students: {comparison[0]}")
        print(f" - International Students: {comparison[1]}")

        # Determine if JHU accepted more US or International students.
        if comparison[0] > comparison[1]:
            print(
                f"Result: JHU accepted {comparison[0] - comparison[1]} "
                f"more American students than International students.")
        elif comparison[1] > comparison[0]:
            print(
                f"Result: JHU accepted {comparison[1] - comparison[0]} "
                f"more International students than American students.")
        else:
            print("Result: JHU accepted an equal number of American "
                  "and International students.")



        # Self-Generated Question #2: Which university accepted the most
        # international students in 2026?
        cur.execute("""
            SELECT llm_generated_university, COUNT(*) as acceptance_count
            FROM applicants
            WHERE us_or_international = 'International'
            AND status ILIKE 'Accepted%'
            AND status LIKE '%/2026'
            GROUP BY llm_generated_university
            ORDER BY acceptance_count DESC
            LIMIT 1;
        """)

        top_intl_uni = cur.fetchone()

        print("\nUniversity with the most International acceptances "
              "in 2026:")
        if top_intl_uni:
            print(f" - {top_intl_uni[0]} with {top_intl_uni[1]} "
                  f"acceptances.")
        else:
            print(" - No international acceptances found for 2026.")

    connection.close()

# This is a test helper function to return one row as a dict with
# the required keys. This will facilitate the test in test_db_insert.py.
def get_sample_applicant_dict(table_name="applicants_db_test"):
    """Return one applicant row as a dict for testing.

    Args:
        table_name: Name of the table to query.

    Returns:
        dict or None: One row as a dict, or None if unavailable.
    """
    # Use the shared DB connection helper
    connection = get_connection()
    if connection is None:
        return None

    with connection.cursor() as cur:
        # Build SQL with Identifier so table name is safely quoted (no injection).
        # Statement and execution are separate; LIMIT 1 is inherent.
        stmt = sql.SQL("""
            SELECT
                p_id, result_id, program, comments, date_added, url, status,
                term, us_or_international, gpa, gre, gre_v, gre_aw, degree,
                llm_generated_program, llm_generated_university
            FROM {}
            LIMIT 1
        """).format(sql.Identifier(table_name))
        cur.execute(stmt)
        row = cur.fetchone()

    # Close the connection to the test database.
    connection.close()

    if row is None:
        return None

    # Build and return a dict with the required keys
    return {
        "p_id": row[0],
        "result_id": row[1],
        "program": row[2],
        "comments": row[3],
        "date_added": row[4],
        "url": row[5],
        "status": row[6],
        "term": row[7],
        "us_or_international": row[8],
        "gpa": row[9],
        "gre": row[10],
        "gre_v": row[11],
        "gre_aw": row[12],
        "degree": row[13],
        "llm_generated_program": row[14],
        "llm_generated_university": row[15],
    }

if __name__ == "__main__":
    main()
