import psycopg

database_name = "module_3"

def main():
    connection = psycopg.connect(dbname=database_name, host="localhost")

    with connection.cursor() as cur:
        # Number of entries that applied for Fall of 2026
        cur.execute("""
            SELECT COUNT(*)
            FROM applicants
            WHERE term = 'Fall 2026';
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
                        ROUND(AVG(gpa)::numeric, 2), 
                        ROUND(AVG(gre)::numeric, 2), 
                        ROUND(AVG(gre_v)::numeric, 2), 
                        ROUND(AVG(gre_aw)::numeric, 2)
                    FROM applicants;
                """)

        averages = cur.fetchone()
        print(f"Average GPA: {averages[0]}")
        print(f"Average GRE: {averages[1]}")
        print(f"Average GRE V: {averages[2]}")
        print(f"Average GRE AW: {averages[3]}")



    connection.close()


if __name__ == "__main__":
    main()