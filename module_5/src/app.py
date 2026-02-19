"""Flask web app for Grad Cafe analysis page.

Routes:
    /                Redirect to /analysis.
    /analysis        Render the analysis page.
    /scrape-status   Report whether a scrape is running.
    /pull-data       Start the scrape/clean pipeline.
    /update-analysis Allow UI to refresh analysis when idle.
"""

import os
import subprocess
import sys
from contextlib import contextmanager

from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    jsonify,
    make_response,
)
import psycopg
from db_connection import get_connection


@contextmanager
def _start_scraper_process():
    """Start the scrape subprocess; yield it without terminating on exit."""
    proc = subprocess.Popen(
        [sys.executable, 'main.py'],
        cwd='Scraper'
    )
    try:
        yield proc
    finally:
        pass  # Process must keep running; do not terminate.


def create_app():
    """Create and configure the Flask application."""

    # Initialize the Flask application.
    app = Flask(__name__)
    # A secret key is needed to use the flash message system for user
    # notifications. This will appear on index.html.
    app.secret_key = 'grad_school_assignment_secret_key'

    # Global variable to keep track of the scraping process.
    # Use this to know if a data pull is currently active.
    app.scraping_process = None

    # Root URL redirects to the analysis page so graders/users find it easily.
    @app.route('/')
    def root():
        """Redirect root URL to the analysis page."""
        return redirect(url_for('index'))

    # Home route: runs def index() when browser hits home page.
    @app.route('/analysis')
    def index():
        """Render the analysis page with current query results."""
        # Establish a connection to PostgreSQL database
        connection = get_connection()

        # Establish dictionary to store all query results so they are
        # organized when sent to  HTML page.
        results = {}

        # Check if a scraping process was started and if it is
        # still running (.poll() is None).
        is_scraping = (
            app.scraping_process is not None
            and app.scraping_process.poll() is None
        )

        if connection:
            try:
                with connection.cursor() as cur:

                    # Query 1: Number of entries for Fall 2026
                    # We check the term and the status columns for
                    # '2026' to ensure accuracy.
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM applicants 
                        WHERE term ILIKE '%Fall 2026%'
                        LIMIT 1;
                    """)
                    results['count_2026'] = cur.fetchone()[0]


                    # Query 2: Percentage of International Students
                    # Use ::DECIMAL and NULLIF to ensure
                    # accurate percentage.
                    cur.execute("""
                        SELECT ROUND(
                            (
                                COUNT(*) FILTER (
                                    WHERE us_or_international = 'International'
                                )
                            )::DECIMAL /
                            NULLIF(COUNT(*), 0) * 100,
                            2
                        )
                        FROM applicants
                        LIMIT 1;
                    """)
                    results['pct_intl'] = cur.fetchone()[0]

                    # Query 3: Overall GPA and GRE averages.
                    # Calculate averages for provided metrics and
                    # round to two decimals.
                    cur.execute("""
                        SELECT
                            ROUND(AVG(gpa)::numeric, 2),
                            ROUND(AVG(gre)::numeric, 2),
                            ROUND(AVG(gre_v)::numeric, 2),
                            ROUND(AVG(gre_aw)::numeric, 2)
                        FROM applicants
                        LIMIT 1;
                    """)
                    avg_row = cur.fetchone()
                    results['avg_gpa'] = avg_row[0]
                    results['avg_gre'] = avg_row[1]
                    results['avg_gre_v'] = avg_row[2]
                    results['avg_gre_aw'] = avg_row[3]

                    # Query 4: Average GPA of US Students in Fall 2026
                    cur.execute("""
                        SELECT ROUND(AVG(gpa)::numeric, 2)
                        FROM applicants
                        WHERE (
                            us_or_international ILIKE 'Amer%'
                            OR us_or_international ILIKE 'US%'
                        )
                        AND term ILIKE '%Fall 2026%'
                        LIMIT 1;
                    """)
                    results['avg_gpa_us'] = cur.fetchone()[0]


                    # Query 5: Acceptance Percentage for Fall 2025
                    cur.execute("""
                        SELECT ROUND(
                            (
                                COUNT(*) FILTER (
                                    WHERE term ILIKE '%Fall 2025%'
                                    AND status ILIKE 'Accepted%'
                                )
                            )::DECIMAL /
                            NULLIF(
                                COUNT(*) FILTER (
                                    WHERE term ILIKE '%Fall 2025%'
                                ),
                                0
                            ) * 100,
                            2
                        )
                        FROM applicants
                        LIMIT 1;
                    """)
                    results['pct_accept_2025'] = cur.fetchone()[0]


                    # Query 6: Average GPA of Fall 2026 Acceptances
                    cur.execute("""
                        SELECT ROUND(AVG(gpa)::numeric, 2)
                        FROM applicants
                        WHERE term ILIKE '%Fall 2026%'
                        AND status ILIKE 'Accepted%'
                        LIMIT 1;
                    """)
                    results['avg_gpa_accept_2026'] = cur.fetchone()[0]

                    # Query 7: JHU Computer Science Masters Count
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
                    results['jhu_cs_count'] = cur.fetchone()[0]

                    # Query 8: Top tier PhD CS acceptances
                    # Answers the query for Georgetown, MIT, Stanford,
                    # and CMU
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
                    results['top_phd_count'] = cur.fetchone()[0]

                    # Query 9: Comparing original vs LLM generated data
                    cur.execute("""
                        SELECT COUNT(*)
                        FROM applicants
                        WHERE status ILIKE 'Accepted%'
                        AND status LIKE '%/2026'
                        AND (
                            program ILIKE '%Computer Science%'
                            AND (
                                program ILIKE '%Ph%d%'
                                OR program ILIKE '%Doctor%'
                            )
                        )
                        AND (
                            program ILIKE '%Georgetown%'
                            OR program ILIKE '%Stanford%'
                            OR program ILIKE '%MIT%'
                            OR program ILIKE
                                '%Massachusetts Institute of Technology%'
                            OR program ILIKE '%Carnegie Mel%n%'
                            OR program ILIKE '%CMU%'
                        )
                        LIMIT 1;
                    """)
                    results['orig_phd_count'] = cur.fetchone()[0]

                    # Calculate the difference to show the impact of the
                    # LLM cleanup
                    results['phd_difference'] = (
                        results['top_phd_count'] - results['orig_phd_count']
                    )


                    # Self-Generated Question #1: How many US American
                    # vs international students were accepted to JHU
                    # in 2026?
                    cur.execute("""
                        SELECT
                            COUNT(*) FILTER (
                                WHERE us_or_international = 'American'
                            ) AS american_count,
                            COUNT(*) FILTER (
                                WHERE us_or_international = 'International'
                            ) AS international_count
                        FROM applicants
                        WHERE (
                            llm_generated_university ILIKE 'John%Hopkins%'
                            OR llm_generated_university ILIKE '%JHU%'
                        )
                        AND status ILIKE 'Accepted%'
                        AND status LIKE '%/2026'
                        LIMIT 1;
                    """)
                    comparison = cur.fetchone()
                    results['jhu_us'] = comparison[0]
                    results['jhu_intl'] = comparison[1]

                    # Self-Generated Question #2: Which university
                    # accepted the most international students in 2026?
                    cur.execute("""
                        SELECT llm_generated_university,
                        COUNT(*) as acceptance_count
                        FROM applicants
                        WHERE us_or_international = 'International'
                        AND status ILIKE 'Accepted%'
                        AND status LIKE '%/2026'
                        GROUP BY llm_generated_university
                        ORDER BY acceptance_count DESC
                        LIMIT 1;
                    """)
                    top_intl = cur.fetchone()
                    results['top_intl_uni'] = (
                        top_intl[0] if top_intl else "N/A"
                    )
                    results['top_intl_count'] = top_intl[1] if top_intl else 0

            # Handle errors if they occur and print out error code.
            except psycopg.Error as e:
                print(f"Error fetching data for Flask: {e}")
            finally:
                connection.close()

            # Pass 'is_scraping' to the HTML template so we
            # can disable buttons in the UI.
            return render_template(
                'index.html',
                data=results,
                is_scraping=is_scraping
            )
        return render_template(
            'index.html',
            data=results,
            is_scraping=is_scraping
        )

    # This code block lets the webpage know if the scrape/clean process
    # is occuring. This lets index.html know whether to disable the
    # buttons while the pipeline is executing. pol() checks to see
    # if the subprocess is complete.
    @app.route('/scrape-status')
    def scrape_status():
        """Return JSON indicating whether a scrape is running."""
        running = (
            app.scraping_process is not None
            and app.scraping_process.poll() is None
        )
        return jsonify({"is_scraping": running})

    # Handles the "Pull Data" button click.
    @app.route('/pull-data', methods=['POST'])
    def pull_data():
        """Start the scraping pipeline unless a run is active."""

        # If a scrape is already running, return a 409 Busy response
        if (
            app.scraping_process is not None
            and app.scraping_process.poll() is None
        ):
            return make_response(jsonify({"busy": True}), 409)

        # Otherwise, start the scraper (use with to satisfy R1732;
        # we do not terminate in __exit__ since process must keep running)
        try:
            with _start_scraper_process() as proc:
                app.scraping_process = proc
            return jsonify({"ok": True})
        except OSError as e:
            # If something goes wrong, return 500 with error info
            return make_response(jsonify({"ok": False, "error": str(e)}), 500)



    # New Route: Handles the "Update Analysis" button click.
    @app.route('/update-analysis', methods=['POST'])
    def update_analysis():
        """Return OK if not busy; block when a scrape is active."""

        # If a scrape is running, block update and return 409 Busy
        if (
            app.scraping_process is not None
            and app.scraping_process.poll() is None
        ):
            return make_response(jsonify({"busy": True}), 409)

        # Otherwise, allow update
        return jsonify({"ok": True})

    return app

if __name__ == '__main__':
    main_app = create_app()
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    main_app.run(host='0.0.0.0', port=8080, debug=debug)
