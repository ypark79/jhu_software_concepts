from db_connection import get_connection

def main():
    # Use the centralized utility to open a session
    connection = get_connection()

    if connection is None:
        return


    with connection.cursor() as cur:
        # Number of entries that applied for Fall of 2026
        cur.execute("""
            SELECT COUNT(*)
            FROM applicants
            WHERE term ILIKE '%2026%' OR status ILIKE '%2026%';
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
                    (COUNT(*) FILTER (WHERE us_or_international = 'International'))::DECIMAL / 
                    COUNT(*) * 100, 2
                )
            FROM applicants;
        """)

        percentage = cur.fetchone()
        print(f"Percentage of international applicants: {percentage[0]}%")

        # Average GPA, GRE, GRE V, and GRE AW for those who provided this
        # data. For those that did not, load_data.py ensured that empty
        # fields returned "NULL" for SQL.
        #
        # SQL AVG excludes NULL values, so AVG calculates the average of all
        # provided GPA/GRE scores. "::numeric" and ROUND are utilized to
        # ensure the averages are rounded to two decimal places.
        cur.execute("""
                    SELECT 
                        AVG(gpa), 
                        AVG(gre), 
                        AVG(gre_v), 
                        AVG(gre_aw)
                    FROM applicants;
                """)

        averages = cur.fetchone()
        print(f"Average GPA: {averages[0]}")
        print(f"Average GRE: {averages[1]}")
        print(f"Average GRE V: {averages[2]}")
        print(f"Average GRE AW: {averages[3]}")



        # Average GPA of Fall 2026 American Students
        # Must filter out American students and application term.
        # The prompt does not specify, but assumption is to round the average
        # to two decimals using ROUND. However, ROUND will not work with a
        # FLOAT. "::numeric" converts the float to a decimal to enable ROUND.
        # Add 'US' check and variations of the 2026 term.
        cur.execute("""
            SELECT AVG(gpa)
            FROM applicants
            WHERE (us_or_international ILIKE 'Amer%' OR us_or_international ILIKE 'US%')
            AND (term ILIKE '%2026%' OR status ILIKE '%2026%');
        """)
        american_gpa_2026 = cur.fetchone()
        print(f"Average GPA of American/US students in Fall 2026: {american_gpa_2026[0]}")



        # Percentage of Acceptances for the Fall 2025 term.
        # Numerator: Count rows where the term is 'Fall 2025' AND the status
        # contains 'Accepted'. ILIKE accounts for case insensitivity.
        #
        # Denominator: Total count of all entries for 'Fall 2025'.
        # NULLIF prevents a crash by returning NULL if no Fall 2025 entries exist.
        # Same use of ROUND and ::DECIMAL to enable decimal division.
        cur.execute("""
                   SELECT
                       ROUND(
                           (COUNT(*) FILTER (WHERE term = 'Fall 2025' AND status ILIKE 'Accepted%'))::DECIMAL / 
                           NULLIF(COUNT(*) FILTER (WHERE term = 'Fall 2025'), 0) * 100, 2
                       )
                   FROM applicants;
               """)

        acceptance_rate_2025 = cur.fetchone()

        if acceptance_rate_2025[0] is not None:
            print(f"Percentage of Accepted applicants for Fall 2025: {acceptance_rate_2025[0]}%")
        else:
            print("Percentage of Accepted applicants for Fall 2025: N/A (No data for this term)")

        # Average GPA of Fall 2026 Acceptances
        # Filter for 'Fall 2026' and call AVG(). Account for case insensitivity.
        # for 'accepted' and enable rounding using "::numeric"

        cur.execute("""
                SELECT AVG(gpa)
                FROM applicants
                WHERE term = 'Fall 2026' 
                AND status ILIKE 'Accepted%';
            """)

        avg_gpa_accepted_2026 = cur.fetchone()
        print(f"Average GPA of Fall 2026 Acceptances: {avg_gpa_accepted_2026[0]}")

        # Number of applicants who applied to JHU for a MS in CS.
        # Based on load_data.py, the university name is stored in
        # 'llm_generated_university' and the major/program in
        # 'llm_generated_program'.
        # Account for different spellings of 'Johns Hopkins' and 'JHU'.
        cur.execute("""
            SELECT COUNT(*)
            FROM applicants
            WHERE (llm_generated_university ILIKE 'John%Hopkins%' OR llm_generated_university ILIKE '%JHU%')
            AND (degree ILIKE 'Master%' OR degree = 'MS')
            AND llm_generated_program ILIKE '%Computer Science%';
        """)
        jhu_cs_masters_count = cur.fetchone()
        print(f"Number of applicants for JHU MS in CS: {jhu_cs_masters_count[0]}")


        # Number of applicants from 2026 that were accepted to Georgetown,
        # MIT, Stanford, or CMU for a PhD in Computer Science.
        #
        # Status ILIKE 'Accepted%2026': Targets 2026 acceptances since 'term' is null.
        # Program: Checks for 'Computer Science' and 'Phd' within the same string
        # Check for variations of CMU and MIT.

        cur.execute("""
                   SELECT COUNT(*)
                   FROM applicants
                   WHERE status ILIKE 'Accepted%2026'
                   AND (llm_generated_program ILIKE '%Computer Science%' AND (llm_generated_program ILIKE '%Ph%d%' OR degree ILIKE 'PhD%'))
                   AND (
                       llm_generated_university ILIKE 'George%Town%' 
                       OR llm_generated_university ILIKE 'Stanford%' 
                       OR llm_generated_university ILIKE '%MIT%'
                       OR llm_generated_university ILIKE '%Massachusetts Institute of Technology%'
                       OR llm_generated_university ILIKE 'Carnegie Mel%n%'
                       OR llm_generated_university ILIKE '%CMU%'
                   );
               """)
        top_tier_phd_count = cur.fetchone()
        print(f"Number of 2026 PhD CS acceptances (GTown, MIT, Stanford, CMU): {top_tier_phd_count[0]}")

        # Answer to question 9 in assignment. First test: run the query
        # searching the "program" field from the original data. Second Test
        # will run the search on the llm_generated_program/unversity fields.
        # Here is the first test searching original data.
        cur.execute("""
                    SELECT COUNT(*)
                    FROM applicants
                    WHERE status ILIKE 'Accepted%2026'
                    AND (program ILIKE '%Computer Science%' AND (program ILIKE '%Ph%d%' OR program ILIKE '%Doctor%'))
                    AND (
                        program ILIKE '%Georgetown%' 
                        OR program ILIKE '%Stanford%' 
                        OR program ILIKE '%MIT%'
                        OR program ILIKE '%Massachusetts Institute of Technology%'
                        OR program ILIKE '%Carnegie Mell%n%'
                        OR program ILIKE '%CMU%'
                    );
                """)
        original_fields_count = cur.fetchone()[0]

        # Here is the second test searching the llm_generated_program
        # and llm_generated_university fields.
        cur.execute("""
                    SELECT COUNT(*)
                    FROM applicants
                    WHERE status ILIKE 'Accepted%2026'
                    AND (llm_generated_program ILIKE '%Computer Science%' AND (llm_generated_program ILIKE '%Ph%d%' OR degree ILIKE 'PhD%'))
                    AND (
                        llm_generated_university ILIKE 'George%Town%' 
                        OR llm_generated_university ILIKE 'Stanford%' 
                        OR llm_generated_university ILIKE '%MIT%'
                        OR llm_generated_university ILIKE 'Massachusetts Institute of Technology%'
                        OR llm_generated_university ILIKE 'Carnegie Mel%n%'
                        OR llm_generated_university ILIKE '%CMU%'
                    );
                """)
        llm_fields_count = cur.fetchone()[0]

        # Print results.
        print(f"PhD CS Acceptances (Original Fields): {original_fields_count}")
        print(f"PhD CS Acceptances (LLM Fields): {llm_fields_count}")
        print(f"Difference: {llm_fields_count - original_fields_count}.")


    connection.close()


if __name__ == "__main__":
    main()