Name: Youngmin Park (ypark79)

Module Info: Module 4 Assignment: Testing and Documentation Experiment Assignment. Due on 15 FEB 2026 at 11:59 EST. 

SSH URL to GitHub Repo: git@github.com:ypark79/jhu_software_concepts.git
Link to Module 4 Folder in GitHub Repo: https://github.com/ypark79/jhu_software_concepts/tree/main/module_4
Link to Read the Docs HTML: https://jhu-software-concepts-ypark79.readthedocs.io/en/latest/
To Run Full Pytest Suite, enter in terminal: PYTHONPATH=module_4/src pytest -c module_4/pytest.ini


Overview:

The Module 4 assignment consists of a full pytest suite that has 100% test coverage over all the source code for my Gradcafe analytics application. As a recap, my analytics application takes raw Gradcafe application results, cleans them into a consistent format, stores the data in a PostgreSQL, and displays meaningful summary statistics in a Flask web page. The Pytest suite was designed around the two primary components of my web application: Web (Flask) and Data. In order to meet 100% coverage for the source code, I was required to extend the Pytest suite beyond the prescribed unit tests outlined in the Module 4 assignment. The Pytest suite provides comprehensive, automated verification of the Gradcafe analytics system across the web user User Interface (UI), data pipeline, and database layer. It tests Flask route availability and page rendering, validates button behavior with busy-state gating, confirms analysis output formatting (labels and two‑decimal percentages), and verifies database inserts and idempotency using a dedicated test database. End‑to‑end tests cover the full flow (pull - update - render) with simulated/fake scrapers to keep tests fast and deterministic. Additionally, I utilized fake data sets (formatted in accordance with what my code and the PostgreSQL database expected) to run the simulated/fake scrapers to stay within accordance to the assignment instructions that all tests shall not require internet and long running scrapes. Also, I utilized Monkeypatch to replace network and database calls. All tests are marked by category for the pytest.ini and run under 100% coverage to ensure every code path in module_4/src is exercised and stable.

When building my Pytest suite, I started with the Flask web layer, making sure the /analysis page loads, the buttons are present, and the page text includes the expected labels. Then I tested the button endpoints directly to confirm they return the right status codes (200 when idle, 409 when busy). This tells me the UI behavior is reliable even when a scrape is running.

Next, I focused on formatting and correctness of the analysis output. I wrote tests that scan the rendered HTML and verify every answer label is present and every percentage is formatted to two decimals. That ensures the results are consistent and readable, which is a key requirement.

After that, I moved into the database layer. I used a separate test database so I wouldn’t touch my real data. I tested inserts after a pull, checked for required fields, and verified idempotency so duplicate pulls don’t create duplicate rows. I also added a helper query function and tested that it returns a dictionary with the exact keys my analysis page needs.
Finally, I wrote end‑to‑end tests that simulate the full workflow: pull - update - render. These tests inject fake scraper data, confirm the database updates, and then verify the analysis page reflects the updated results. This ties everything together and proves the system works as a whole.

To guarantee 100% coverage, I used “pytest-cov with --cov=module_4/src and --cov-fail-under=100”. This forces every line in the source code to be executed by tests. If any line isn’t tested, the run fails. Because the full suite passes with coverage enforcement, I know that every path in the codebase is exercised and verified. This demonstrates that the application is stable, testable, and ready for future changes. Please reference the comments within the tests in the Pytest suite for the further explanation of what code was used to accomplish this. 

After attaining 100% coverage, I created Sphinx documentation to explain the entire web application for future developers. I documented using Sphinx by generating a docs scaffold, adding clear module and function docstrings across the Flask, database, and scraper/cleaner code, and writing structured .rst pages for overview/setup, architecture, testing, and API reference. Autodoc and Napoleon were enabled to pull docstrings into the API page automatically. I configured Read the Docs with a .readthedocs.yaml file and a minimal requirements.txt for Sphinx dependencies, built the HTML locally to verify output, and published the docs to Read the Docs. The link to my Read the Docs HTML is here: https://jhu-software-concepts-ypark79.readthedocs.io/en/latest/ . 

I then created a CI pipeline in github/workflows/tests.yml that runs the full Pytest suite on every push. The workflow provisions a PostgreSQL service, sets the required environment variables, installs the items outlined in a requirements.txt, and executes the test command with coverage enforcement. This provides automated verification that the Flask app, pipeline, and database logic remain stable in a clean, reproducible environment. The successful run was captured as ypark79_actions_success.png for submission.


Module 4 Directory/File Structure: 

The Module 4 project is organized so that the source code, tests, and documentation are separated and easy to maintain and navigate. Module_4 contains a src folder, tests folder, and docs folder. All application code lives in module_4/src folder. Within the src folder lives app.py (Flask routes and analysis page), db_connection.py (database connection helper), load_data.py (loads JSON rows into PostgreSQL), query_data.py (query helper), and a subfolder named “Scraper.” Within the Scraper folder is the scraping and cleaning pipeline (code generated in Module 2). All pytest tests live in module_4/tests folder. The Sphinx documentation source files live in module_4/docs folder. Also within the module_4 folder is the coverage_summary.txt (test coverage output), requriements.txt (Python dependencies), ypark79_actions_success.png (proof showing successful github actions, and this readme.txt. Of note, the workflow file for the github actions lives in .github/workflows/test.yml. Ultimately, this file structure within the module_4 folder makes it easy to import code from the src folder into the tests, keep tests separate from production code, and run the pytest suite with full coverage on only the src folder. 


Setup:

1. Create a virtual environment by entering “python -m venv module_4/.venv” in your terminal. 
2. Active the venv by entering “source module_4/.venv/bin/activate
3. Then install Python dependencies by entering “pip install -r module_4/requirements.txt”
4. Set up a PostgreSQL database on your local machine. For the purposes of this assignment, I created a separate test database on my local machine to avoid touching the PostgreSQL database I created and appended new data to during Module 3. 


Environmental Variables: 

My module 4 project connects to PostgreSQL utilizing environment variables. The required variables are as follows: 
- PGHOST = localhost
- PGPORT = 5432
- PGUSER = your_username
- PGPASSWORD = your_password
- PGDATABASE = module_4_db_test


Running the Pytest Suite: 

The entirety of my Pytest Suite can be ran by entering the following in the repo root terminal: “PYTHONPATH=module_4/src pytest -c module_4/pytest.ini.”


Pytest Marker Breakdown: 

As per the Module 4 instructions, the following markers were utilized to categories the tests within the Pytest suite: 
- web: tests page load and HTML checks. 
- buttons: button routes and busy state behavior
- analysis: labeling and percentage formatting. 
- db: database inserts and queries
- integration: full end to end flow. 

All the tests in the Pytest suite are marked with these markers as per the assignment instructions; there are no tests that are unmarked. The 100% coverage report can be found in the module_4 folder in a txt file titled “coverage_summary.txt. 


Key Design Highlights: 

When I refactored the project for Module 4, my main goal was to make the system testable, reliable, and easy to explain. I introduced a Flask create_app() factory so tests could run the app without side effects, and I added explicit routes for /analysis, /pull-data, and /update-analysis so the User Interface behavior could be tested directly. The busy‑state logic for the buttons was designed to be observable and deterministic (no sleep()), which made it possible to validate “busy” vs “idle” behavior with unit tests.

On the data side, I chose to keep the database schema consistent with Module 3 and enforce idempotency through a unique result_id. That way, repeated pulls never created duplicate rows. I also used a dedicated test database and environment variables in the tests so the suite could run safely without touching real data. This separation made it easy to test inserts, queries, and edge cases without risking the production dataset.
For output validation, I standardized analysis formatting at the template level and then enforced it in tests (labels and two‑decimal percentages). This ensures the web User Interface stays consistent even as the underlying queries evolve. Finally, I documented the full system with Sphinx and configured a minimal GitHub Actions workflow so the entire pipeline—web app, Extract Transform Load (ETL), and database logic—could be verified automatically in CI. These design choices were all made to keep the system stable, testable, and easy for someone else to run.

Reoccurring techniques within my Pytest suite include fake data rows to avoid real scraping or API calls, Monkey patch to replace network/database calls and subprocesses, Flask test client to send requests without opening a real browser, REGEX and BeautifulSoup to check HTML formatting and labels, test database environment variables to avoid touching my real data, and busy-state simulations to check for code 409 outputs. 



Pytest Suite Breakdown (please reference the comments in the test files). 


Test_flask_page.py (Flask page and routes): This test series checks that the Flask app exists, required routes are registered, the Analysis page loads, and the HTML contains the correct buttons and labels. The purpose of each of the tests are: 

Test_app_has_required-routes(): validates Flask routes exist (/analysis, /pull-data, /update-analysis). 

Test_get_analysis_page(): ensures the page returns 200 and contains buttons/labels. 

Test_scrape_status_route_idle: /scrape-status returns (is_scraping” : False) aka not running. 

Test_pull_data_exception_returns_500: confirms failure path returns 500. 

Test_analysis_handles_db_error: verifies the page still renderes if the database query fails. 

Test_app_main_block: covers the __main__block safely. 



Test_buttons.py (Button behavior and busy state): This test series test that the buttons return 200 when idle, return 409 when busy, and that loaders are called (ro not called) correctly. 

Test_pull_data_returns_ok_and_calls_loader(): ensures /pull-data returns 200 and calls loader. 

Test_update_analysis_returns_ok_when_not_busy(): ensures /update-analysis returns 200 when idle. 

Test_busy_udpate_analysis(): ensures /update-analysis returns 409 when busy. 

Test_busy_for_pull_data(): ensures /pull-data returns 409 when busy and doesn’t run the loader. 



Test_analysis_format.py (Labels and percentage formatting): This test series checks that all answers are labeled and all percentages have exactly two decimals. 

Test_analysis_has answers_labels_and_two_decimal_percents: checks lebals and percent formatting. 



Test_db_insert.py (Database inserts, idempotency, and key structure): This sries uses a test database to verify inserts happen, duplicates are prevented, and query returns expected keys. 

Test_insert_on_pull_and_idempotency(): inserts fake rows and checks duplicates are not created. 

Test_query_returns_expected_keys(): verifies query dictionary includes all required fields. 



Test_integration_end_to_end.py (Full pipeline test): runs the full flow (update – render-second pull with no duplicates). 

Test_end _to_end_pull_update_render(): complete end to end validation including the HTML formatting. 



Test_load_data.py (load_data hlpers and main): This series of tests test the helper functions used for term parsing, date parsing, float conversation, and main database behavior using fake connections. Of note, although I corrected my scrape.py code from module 2, I kept all the functions that can infer “term” data in the case that a student application that’s scraped in the future does not provide data in the “term” field. Keeping the functions that infer the term adds redundancies to maximize data collection on the terms. 

Test_infer_term_from_status_date(): term inferred from the status date. 

Test_infer_term_from_date_added(): term inferred from date added

Test_parse_date_valid(): / test_parse_date_invalid(): date parsing successful. 

Test_try_float(): float conversation behavior. 

Test_main_success(): main inserts data with fake database and fake file. 

Test_main_connection_file(): main exits safely in the case the database connection fails. 

Test_infer_term_from_status_year(): alternate date-based inference. (used to infer the term)

Term_infer_term_fallback_months(): month-based fallback (used to infer the term)

Term_infer_term_invalid_date(): invalid date returns None. 

Test_load_data_main_rollback(): tests rollback on database error. 

Test_load_data_main_block(): tests the main block runs safely. 



Test_query_data.py (query_data logic and helper function for the dictionary test): These series of tests simulates query results without a real database and tests the helper dictionary logic. 

Test_main_success(): fake cursor returns expected query results. 

Test_main_connection_fail(): safe exist when connection fails

Test_get_sample_applicant_dict(): tests the dictionary helper that returns correct data fields. 

Test_query_data_acceptance_none_and_top_intl_none(): tests the branch that accounts for N/A. 

Test_query_data_comparison_branches(): tests both comparison paths. 

Test_get_sample_applicant_dict_connection_none(): None when connection fails. 

Test_get_sample_applicant_dict_row_none(): None when there is no row. 

Test_query_data_main_blocl(): tests safe main execution. 



Test_scrape.py (Scraping helpers and scrape flow): These series of tests use HTML fixtures to test parsing, error handling, and the __main__ loop without real network calls. 

Test_extract-result_id(): URL – result_id parsing. 

Test_parse_date_added(): parse valid/invalid dates. 

Test_extract_term_from_text(): term detection in text. 

Test_infer_term_from_row(): term inferred from combined fields. 

Test_extract_term_from_detail_row(): extracts term from detail row. (This was the code that was corrected to ensure my scrape.py properly extracts the term from the student application). 

Test_extract_tr_rows_from_html(): only <tr> rows with data. 

Test_row_dct_from_tr_parses_fields(): parses row dictionary correctly. 

Test_scrape_data_happy_path(): normal scrape flow with fixtures. 

Tess_scrape_data_data_stops_on_existing_id(): stops on existing IDs. 

Test_scrape_data_skips_rows_without_link(): skip rows missing a link. 

Test_scrape_data_detail_fetch_error_sets_none(): detail page failure handled. 

Test_make_request_headers(): headers are set correctly. 

Test_download_html_success(): decode HTML success. 

Test_download_html_http_error_retires: retry on 5xx code. 

Test_download_html_http_error_non_retry(): fail on non-500 code. 

Test_download_html_urlerror(): retry URLError. 

Test_extract_term_from_detail_row_autumn(): normalize “Autumn” as “Fall.” 

Test_scrape_data_empty_page(): empty page returns empty. 

Test_scrape_data_missing_result_id(): skips non-numeric IDs. 

Test_scrape_data_detail_row_no_term(): no term in detail row. 

Test_scrape_save_and_load(): save/load roundtrip. 

Test_scrape_load_bad_json(): bad JSON returns an empty list []

Test_scrape_main_block(): main safe execution. 

Test_scrape_main_loop_paths(): empty page path in main. 

Test_scrape_main_loop_stop_now(): stop when already known. 

Test_scrape_main_loop_error_path(): error handling in loop. 

Test_scrape_main_loop_non_empty_then_empty(): success then exist. 

Test_scrape_main_loop_error_path(): alternate error branch. 



Test_clean.py (cleaning logic, LLM, and Database Inserts): This test series covers cleaning helpers, extraction logic, LLM integration (simulated), database insertion behavior, and main safety paths. 

Test_chunked_splits_list(): splits list into chunks. 

Test_clean_whitespace(): whitespace normalization. 

Test_clean_program_cell(): strips extract text in “program”

Test_clean_program_cell_none(): handles None. 

Test_normalize_zero_none(): None handling. 

Test_normalize_zero(): “0” values are interpreted as None. 

Test_Text_extractors_from_sample_text(): extracts  decisions, GPA, GRE, etc. 

Test_extract_term_year_autumn_normalized(): Normalizes “Autumn” to “Fall”

Test_text_extractors_none_inputs(): None inputs return None. 

Rest_text_extractors_no_match(): no matches is interpreted as None. 

Test_load_data_file_not_found(): missing file is returned as an empty list []

Test_save_and_load_data_roundtrip(): save/load “ok”. 

Test_load_data_bad_json_returns_empty(): bad JSON returns an empty list []

Test_llm_post_rows_success(): LLM success path. 

Test_llm_post_rows_missing_rows_raises(): missing rows returns an error. 

Test_llm_post_rows_all_retries_fail(): retry loop failure. 

Test_clean_data_basic(): end to end clean with LLM simulation. 

Test_clean_data_missign_decision_and_term_fallback(): term fallback to extract term. 

Test_parse_date_and_to_float_invalid(): invalid parasing returns None. 

Test_append_rows_to_master(): deduplication and appends new data. 

Test_append_rows_to_master_skips_none_id(): skip missing IDs. 

Test_insert_rows_into_postgres_empty_returns_zero(): no rows returns 0. 

Teset_insert_rows_into_postgres_fake_connection(): insert with fake database. 

Test_insert_rows_into_postgres_skips_missing_id(): skips missing ID. 

Test_clean_data_decision_only(): decision without a provided date. 

Test_clean_data_rejected_branch: rejected branch. 

Test_clean_data_combined_program_branches(): program/university combinations. 

Test_parse_date_empty_and_to_float_none(): empty inputs. 

Test_clean_main(): main runs with simulated/mocked helpers. 

Test_clean_main_block(): tests main safe. 



Test_db_connection.py (Database connection failure): this test confirms get_conect() returns None if the database connect fall fails. 

Test_get_connection_failure(): connection error handled. 



Known Bugs – 

The Pytest suite, Github Actions, and Read the Docs run with no issues. 


Citations – 
ChatGPT and GPT 5.2 CODEX assisted with the learning and coding of this project. 
