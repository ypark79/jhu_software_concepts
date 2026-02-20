Name: Youngmin Park (ypark79)

Module Info: Module 5 Assignment: Software Assurance + Secure SQL (SQLi Defense) Assignment. Due on 23 FEB 2026 at 11:59 EST. 

SSH URL to GitHub Repo: git@github.com:ypark79/jhu_software_concepts.git
Link to Module 4 Folder in GitHub Repo: https://github.com/ypark79/jhu_software_concepts/tree/main/module_4
Link to Read the Docs HTML: https://jhu-software-concepts-ypark79.readthedocs.io/en/latest/


Module 5 Assignment Overall Approach – 

I copied the Module 4 Assignment files into my Module 5 folder and adjusted my code to successfully run out of the Module 5 folder. My overall approach to Module 5 assignment was to first get the environment and tests working and at 100% coverage (Step 0), then bring the source code up to Pylint’s standards so that I could achieve a 10/10 score (Step 1), and harden every SQL query against injection and enforce limits as prescribed in the assignment instructions (Step 2). In this step I identified every SQL query that used user input or variable components (e.g. table names), replaced f-string and concatenation with psycopg’s SQL composition (sql.SQL and sql.Identifier), added LIMIT 1 to every SELECT that did not have one, and enforced a maximum row limit for bulk inserts as per the instruction assignments. I ran Pylint again, created a configuration file (pylintrc) to outline project-specific standards, and fixed every remaining issue that Pylint reported; I ran Pylint at the conclusion of every step of this assignment. Of note, I only linted the python source code in the src folder as per the teacher’s instructions.  For Step 3, I removed the last hard-coded credential (PGUSER default in clean.py), added .env.example with the environmental variables with example values, created .env  with real environmental variable values (ensured it was put in .gitignore), and created a least-privilege DB user with only the permissions the app needs to run successfully. For Step 4, I installed pydeps and Graphviz, ran pydeps to generate the dependency graph, and saved it as dependency.svg for submission. For Step 5, I ensured the requirements.txt contained only the required runtime and tool dependencies, added setup.py so the project is installable with pip install -e, and added an “Install” section to the README, which explains how to install my program using both pip and uv so anyone can reproduce the environment. For Step 6, I installed and authenticated the Snyk CLI, ran snyk test, and documented the one dependency vulnerability (diskcache via llama-cpp-python) with an explanation of why I kept the vulnerability. For extra credit, I ran snyk code test, fixed the four reported issues (path traversal and debug mode issues), and ran the test again for a clean result. For Step 7, I updated my GitHub Actions workflow (located in the root directory at .github/workflows/tests.yml) that runs on every push and pull request to GitHub. The workflow enforces shift-left security by running five actions for Module 5: Pylint (fail if score below 10), pytest with 100% coverage, generation of dependency.svg via pydeps, Snyk test (using SNYK_TOKEN in my repo secrets), and the same pytest suite so that tests and coverage are required to pass. These steps will be explained in more detail in this README. 


Module 5 Directory Structure Overview - 

I organized the module_5 folder so that source code, tests, documentation, and configuration are organized and easy to find. 

-module_5 folder: 
- src folder (all application source code). 
	-app.py (Flask application): routes for /, /analysis, /scrape-status, /pull-data, and /update-analysis.

	-db_connection.py: Python file that opens a connection to PostgreSQL using environment variables.

	-load_data.py: Loads applicant data from JSON into the PostgreSQL database (term inference, date parsing, inserts).
    		
	-query_data.py: Runs the analysis queries used by the Flask app and provides a sample-applicant helper for tests.

- Scraper Folder: Scraping and cleaning pipeline and local LLM (llm_hosting). 
      	-scrape.py: Fetches and parses Grad Cafe pages, saves raw JSON.

	-clean.py: Cleans and normalizes rows, optional LLM step, appends to master JSON and inserts into PostgreSQL.

	-main.py: Orchestrates scrape then clean; used when the user clicks “Pull Data.”

-llm_hosting folder: Holds local LLM for cleaning university and program data. 

-tests folder:  pytest suite.

- docs folder: Sphinx documentation.
    	-source folder:  RST source and conf.py (Sphinx config).
    	-build folder: Generated HTML 

-.pylintrc: Pylint configuration 

-.env.example: Template for DB connection environmental variables (Step 3). I also made a real .env (added to gitignore) with my real environmental variables with real values. 

-pytest.ini: Pytest markers

-requirements.txt:  Python dependencies for the project.

-setup.py:  Makes the project installable (Step 5).

-.gitignore: Ignores .venv, .pytest_cache, .pylint_cache, .env, bytecode, and 	large/generated files as dictated by me. 

-sql folder: SQL scripts for database setup (Step 3 least-privilege user).

-dependency.svg: Python dependency graph (Step 4).

-snyk-analysis.png: Screenshot of Snyk dependency scan results (Step 6).

-Screenshot PDF

-readme.txt


Requirements to Run the Module 5 Program - 

- Python 3.10+ (I used 3.13)
- PostgreSQL (for the app and for the test database.)
- A virtual environment and the packages listed in requirements.txt required for runtime. 


Fresh Install Instructions (Step 5C) - 

To create a new environment and run the project from scratch, use one of these methods:

Option 1: pip (Enter the following in your terminal)

cd module_5
python -m venv .venv
source .venv/bin/activate   # Mac/Linux; on Windows: .venv\Scripts\activate
pip install -r requirements.txt


Option 2: uv  

First install uv by entering curl -LsSf https://astral.sh/uv/install.sh | sh (Mac/Linux) or pip install uv in your terminal. Then enter the following:

cd module_5
uv venv
source .venv/bin/activate   # Mac/Linux; on Windows: .venv\Scripts\activate
uv pip sync requirements.txt


Installing the Whole Project as a Package (Step 5B) – 

After installing requirements, run pip install -e . from the module_5 folder. 

Pip:  pip install -e . 

Uv:  uv pip install -e . 

setup.py describes my project layout and dependencies so that pip install -e . knows what to install. The package is named gradcafe-analytics in setup.py. After installing, continue with the Setup steps below (PostgreSQL, environment variables, etc.).


Once the installations and set up are complete, initiate the Flask app by typing in the following in the module_5 venv directory in your terminal: 

Python -m app

Then open the URL in a browser, click the Pull Data button, allow the scrape/clean process to run, and then click the Update Analysis button to view the new analysis. The buttons will not be active while the scrape/clean process is ongoing – they will automatically become usable once the scrape/clean process is complete. 


Setup Instructions - 

1. Set up PostgreSQL: Create a database for the application. I used my real PostgreSQL database from Module_3 for real data and created a separate test database (module_5_db_test) to run my Pytest suite without touching my real data.

2. Set environment variables for PostgreSQL:
   - PGHOST (e.g. localhost),
   - PGPORT (e.g. 5432),
   - PGUSER (your PostgreSQL username),
   - PGPASSWORD (your password),
   - PGDATABASE (your main DB name when running the app).

My Pytest suite tests use PGDATABASE=module_5_db_test (and the same host/port/user/password) so that the test suite runs against the test database. On my Mac, the default PostgreSQL role was not “postgres,” so I had to ensure **PGUSER** was set to my system username for the tests to connect.


Running the Pytest Suite - 

All tests must be run from inside the module_5 directory so that imports and paths are correct. With the virtual environment activated and current directory set to module_5, type the following in your terminal:

PYTHONPATH=src pytest

Pytest will use pytest.ini in the module_5 folder, which sets --cov=src, --cov-report=term-missing, and --cov-fail-under=100 so the full test run also enforces 100% code coverage over all source code in the src folder. Tests that require PostgreSQL (test_db_insert.py, test_integration_end_to_end.py) can be excluded with --ignore=tests/test_db_insert.py --ignore=tests/test_integration_end_to_end.py if you do not have a test database configured at the time of testing.


How I Ran Pylint (Step 1)

I only linted the python code in the src folder, not the tests as per the instructors guidance. 
To run Pylint, I used the following in the terminal from my module_5 virtual environment. 

PYLINT_HOME=.pylint_cache PYTHONPATH=src pylint src

I also used the following to ensure I scored a 10/10:

PYLINT_HOME=.pylint_cache PYTHONPATH=src pylint src --fail-under=10

Upon a successful Pylint run, I saw 10/10 with no errors or warnings.

Of note, no Pylint checks were disabled and no python files in the source code were ignored. The .pylintrc file contains only configuration requirements (max-line-length, good-names, generated-members, design limits, min-similarity-lines). There is no disable= list and no ignore= directive. Every issue reported by Pylint was fixed in the code itself in all iterations. 


In Depth Approach Breakdown by Step – 

Step 0: Making Sure the Flask App and All Tests Work

I started with a copy of my Module 4 project. Module 4 already had a Flask app, a full pytest suite with 100% coverage, and Sphinx docs. For Module 5, I needed to adjust paths, dependencies, and environment so that everything runs from the module_5 folder. I also had to fix environment-specific issues (like the PostgreSQL role name on my Mac) so that the test database could be used successfully.

Dependencies (requirements.txt) - 
I updated requirements.txt for module_5 by removing packages that were not needed for this assignment and made sure pytest and pytest-cov were included so that the test suite and coverage enforcement run correctly. I updated requirements.txt later in the assignment when generating the dependency.svg file.

Flask app: root route and docstring - 
In order to make the app easier to open in a browser, I added a root route / that redirects to /analysis, so that visiting http://127.0.0.1:8080 takes the user straight to the analysis page. I also updated the module docstring at the top of **app.py** to describe the routes (/, /analysis, /scrape-status, /pull-data, /update-analysis).

Running Pytest: Then I ran the Pytest suite. Initially, ran it from the repo directory root and pointed to the module-5 tests. I received an error (import file mismatch). In order to fix this, I ran the following  in the terminal to successfully run the Pytest

cd module_5
source .venv/bin/activate
PYTHONPATH=src pytest

Pytest configuration (pytest.ini)
I updated pytest.ini so that it matches the module_5 layout. I changed the coverage option from --cov=module_4/src to --cov=src so that coverage is measured only over the src folder under module_5.  

Database role and test database 
On my machine, the default PostgreSQL superuser is not named “postgres,” so several tests failed with “role postgres does not exist.” I fixed this by changing the test setup to use getpass.getuser() as the default PGUSER when PGUSER is not set, and an empty default for PGPASSWORD. The tests are configured to use a test database name module_5_db_test. I created that database on my local PostgreSQL database. After that, the database tests could connect and all tests passed.



Step 1: Pylint 

I ran Pylint on all Python code inside my src folder and fixed all issues. No Pylint checks were disabled or ignored; all Pylint issues were fixed by changing the code itself. My .pylintrc only contains configurations  (max-line-length=80, good-names, generated-members, design limits, min-similarity-lines). In order to run Pylint over my code, I used the following in my terminal: 

PYLINT_HOME=.pylint_cache PYTHONPATH=src pylint src


Step 2: SQL Injection Defenses 


I found two places where SQL was built unsafely and fixed both. I also added LIMIT to every SELECT and enforced a maximum row limit for bulk inserts.

1. query_data.py : get_sample_applicant_dict. The function takes a table_name argument and was using an f-string to put it into the query: FROM {table_name}. I replaced that with psycopg’s sql.SQL() and sql.Identifier(table_name) so the table name is safely quoted. The query already had LIMIT 1.

2. Scraper/clean.py:  insert_rows_into_postgres. The function takes a table_name argument and was using an f-string for INSERT INTO {table_name} and for the ON CONFLICT clause. I replaced that with sql.SQL() and sql.Identifier(table_name) so the table name is never concatenated into the SQL string. I also added a constant MAX_INSERT_ROWS = 10000 and capped the number of rows inserted per call with rows = rows[:MAX_INSERT_ROWS], so a caller cannot pass an unbounded list.

3. app.py and query_data.py. The assignment instructions said every query must have an inherent LIMIT. All of the analysis queries are aggregates (COUNT, AVG, ROUND) that return one row. I added LIMIT 1 to each SELECT that did not already have one. The “top university”–style query already had ORDER BY ... LIMIT 1.

After these changes, every SQL query that uses variable components (table names) is built with psycopg’s SQL composition. User and caller values are never pasted into SQL strings; they go through parameter binding or sql.Identifier. Every SELECT has an inherent LIMIT (either LIMIT 1 or the existing LIMIT 1 on the top-university query), and the bulk insert enforces a maximum of 10,000 rows per call. I re-ran pytest and Pylint; both pass with 100% coverage and 10.00/10.


Step 3: Database Hardening 

1. No hard-coded DB credentials in code: I found every place that establishes a database connection: db_connection.py, Scraper/clean.py, and the test files. db_connection.py already read PGHOST, PGPORT, PGDATABASE, PGUSER, and PGPASSWORD from environment variables with no hard-coded credentials. Scraper/clean.py had one violation: it used os.getenv("PGUSER", "youngminpark"), which hard-coded a username. I fixed this by changing it to `os.getenv("PGUSER") or getpass.getuser(). No usernames or passwords are hard-coded anywhere now.

2. App reads DB connection values from environment variables: The app uses the standard PostgreSQL environment variables: PGHOST, PGPORT, PGDATABASE, PGUSER, and PGPASSWORD. These are read in db_connection.py (used by app.py, query_data.py, load_data.py) and in Scraper/clean.py (for insert_rows_into_postgres). The assignment gave DB_HOST, DB_PORT, etc. as examples; using PGHOST, PGPORT, etc. satisfies the requirement that values come from environment variables.

3. .env.example containing variable names with placeholder values.

I created .env.example in the module_5 folder with:

PGHOST=localhost
PGPORT=5432
PGDATABASE=your_database_name
PGUSER=your_db_username
PGPASSWORD=your_db_password


4. Least-privilege DB user

I created sql/least_privilege_user.sql with the SQL needed to create a role gradcafe_app that is not a superuser and has no DROP, ALTER, or owner-level permissions. The role has only:

- CONNECT on the database
- USAGE on the public schema
- SELECT, INSERT, UPDATE, TRUNCATE on the applicants table

I granted these because:

- SELECT — app.py and query_data.py read analysis data from the applicants table
- INSERT — load_data.py and clean.py insert rows
- UPDATE — clean.py uses ON CONFLICT DO UPDATE 
- TRUNCATE — load_data.py truncates the table before loading JSON

 My app is not read-only; it writes data (load_data, scrape-and-clean pipeline). So the DB user needs INSERT, UPDATE, and TRUNCATE, but I did not grant DROP, ALTER, CREATE, or superuser privileges. 


Instructions on how to run the least-privilege SQL script 

1. Replace placeholders in the SQL file. Open sql/least_privilege_user.sql and replace:
   - YOUR_DATABASE_NAME with your actual database name 
   - CHANGE_ME with your own password for the gradcafe_app role.

2. Run the script as a PostgreSQL superuser. From the module_5*directory, run:
   
psql -d module_3 -f sql/least_privilege_user.sql

Replace module_3 with your database name. If you need to specify host, port, or user, use: psql -h localhost -p 5432 -U postgres -d module_3 -f sql/least_privilege_user.sql

3. Ensure the applicants table exists because the script grants privileges on the applicants table. If the table does not exist yet, create it first (e.g. by running load_data.py or by creating the schema with a superuser).

4. Use the new user in the app. To run the Flask app with the least-privilege user, set these in your .env file:

PGUSER=gradcafe_app
PGPASSWORD=your_password_here
PGDATABASE=module_3
Use the same password from step 1

After these changes, the codebase had no hard-coded DB credentials, all connection values come from environment variables, .env.example documented the required variables, .env is in .gitignore, and a least-privilege SQL script is provided for creating the app’s DB user. Pytest and Pylint also passed with 100% coverage and 10.00/10 at this point in the assignment. 



Step 4: Python Dependency Graph 

I installed pydeps via pip and Graphviz and ensured the dot command was available. I also ensured pydeps is now listed in requirements.txt along with pylint and all runtime dependencies. I ran pydeps from the module_5 directory with PYTHONPATH set so that app.py’s imports resolve. The command I used was:

cd module_5
source .venv/bin/activate
PYTHONPATH=src pydeps src/app.py --noshow -T svg -o dependency.svg


The dependency graph shows app.py as the entry point. The app depends on Flask for the web layer and on db_connection to connect to PostgreSQL. db_connection uses psycopg to execute SQL and manage the database connection; the app uses db_connection to run the analysis queries and load data. The graph also includes Flask’s internal modules (e.g., flask.app, flask.templating, flask.helpers) because pydeps traces all imports.



Step 5: Reproducible Environment + Packaging 

5A: requirements.txt: requirements.txt now includes everything needed at runtime (Flask, psycopg, beautifulsoup4, requests, etc.) plus the tools pylint and pydeps. A brand new environment can run the project from scratch by installing from this file. The Flask web app and analysis page still run after installation.

5B: setup.py: I added setup.py*in the module_5 folder. 

Why packaging matters: It makes the project installable (pip install -e .), so imports behave consistently across local runs, tests, and CI. Editable installs reduces issues when code is ran on different machines due to file/directory path differences. Tools like uv can also extract requirements from setup.py when syncing environments. The setup.py dictates the package layout (src/, packages, py_modules, etc.), Python version (3.10+), and install requirements for the core runtime dependencies.


5C: Fresh Install Instructions

As mentioned above, see below for fresh install  and set up instructions: 

Fresh Install Instructions (Step 5C) - 

To create a new environment and run the project from scratch, use one of these methods:

Option 1: pip (Enter the following in your terminal)

cd module_5
python -m venv .venv
source .venv/bin/activate   # Mac/Linux; on Windows: .venv\Scripts\activate
pip install -r requirements.txt


Option 2: uv  

First install uv by entering curl -LsSf https://astral.sh/uv/install.sh | sh (Mac/Linux) or pip install uv in your terminal. Then enter the following:

cd module_5
uv venv
source .venv/bin/activate   # Mac/Linux; on Windows: .venv\Scripts\activate
uv pip sync requirements.txt


Installing the Whole Project as a Package (Step 5B) – 

After installing requirements, run pip install -e . from the module_5 folder. 

Pip:  pip install -e . 

Uv:  uv pip install -e . 

setup.py describes my project layout and dependencies so that pip install -e . knows what to install. The package is named gradcafe-analytics in setup.py. After installing, continue with the Setup steps below (PostgreSQL, environment variables, etc.).


Once the installations and set up are complete, initiate the Flask app by typing in the following in the module_5 venv directory in your terminal: 

Python -m app

Then open the URL in a browser, click the Pull Data button, allow the scrape/clean process to run, and then click the Update Analysis button to view the new analysis. The buttons will not be active while the scrape/clean process is ongoing – they will automatically become usable once the scrape/clean process is complete. 


Setup Instructions - 

1. Set up PostgreSQL: Create a database for the application. I used my real PostgreSQL database from Module_3 for real data and created a separate test database (module_5_db_test) to run my Pytest suite without touching my real data.

2. Set environment variables for PostgreSQL:
   - PGHOST (e.g. localhost),
   - PGPORT (e.g. 5432),
   - PGUSER (your PostgreSQL username),
   - PGPASSWORD (your password),
   - PGDATABASE (your main DB name when running the app).

My Pytest suite tests use **PGDATABASE=module_5_db_test** (and the same host/port/user/password) so that the test suite runs against the test database. On my Mac, the default PostgreSQL role was not “postgres,” so I had to ensure **PGUSER** was set to my system username for the tests to connect.



Step 6: Snyk Dependency Scan  + Extra Credit

Step 6 required running a dependency scan with Snyk to check for known vulnerabilities in the packages the project uses. I installed the Snyk CLI via Homebrew) authenticated with my Snyk account, and ran snyk test from the module_5 directory. Snyk scanned requirements.txt and setup.py and compared the declared dependencies against Snyk’s vulnerability database.

Snyk test produced one vulnerability that I chose to accept:  Deserialization of Untrusted Data (High Severity) in diskcache@5.6.3. After using an LLM to research what this issue is, it originates from llama-cpp-python, which depends on diskcache. This package is required to run the instructor-provided local LLM that cleans university and program data. 

I chose to keep llama-cpp-python in the project because it is required for the “Pull Data” feature. When a user clicks “Pull Data,” the app runs the scrape-and-clean pipeline, which starts a local LLM server (in src/Scraper/llm_hosting/). That server uses **llama-cpp-python** to standardize program and university names in the scraped data. Without this package, the Pull Data flow would fail and users could not refresh the analysis data from Grad Cafe. Since Snyk reports no fix for the diskcache vulnerability, and because the LLM runs only in a controlled local environment, I documented the vulnerability and kept the package. 


Extra Credit: Snyk Code (SAST)
I ran snyk code test from the module_5 directory. The first run reported 4 open issues, all medium severity:

1. Path Traversal (3 findings) in src/Scraper/llm_hosting/app.py (lines 365, 377, 385). Snyk flagged that command-line arguments (file paths for the --file and output options) were passed into open() and json.dump() without sanitization.

2. Debug Mode Enabled in src/app.py (line 369). The main Flask app was started with debug=True, which can expose sensitive information if the app is reachable by untrusted parties.

I addressed all four findings: I added a path-validation helper in the LLM hosting app so that file paths must stay under the current working directory (preventing path traversal), and I changed the main app so that debug mode is off by default and can be enabled only via the FLASK_DEBUG environment variable. After these fixes, I re-ran snyk code test and the scan completed with no open issues. 



Step 7: CI Enforcement with GitHub Actions

Step 7 required adding a GitHub Actions workflow that runs on every push and pull request and enforces “shift-left security” with five separate actions for module_5.

I updated the existing workflow at .github/workflows/tests.yml (in the repository root, following the same pathway as Module 4 as per the assignment instructions). The test-module-5 job now runs these steps in order:

1. Run Pylint: From the module_5 directory, the workflow runs `PYLINT_HOME=.pylint_cache PYTHONPATH=src pylint src --fail-under=10`. If the Pylint score drops below 10/10, the job fails.

2. Run tests (pytest): The same pytest command used locally runs in CI with the module_5 test database. The pytest.ini in module_5 already sets --cov-fail-under=100, so the job fails if coverage drops below 100%.

3. Generate dependency.svg: The workflow installs Graphviz, then runs PYTHONPATH=src pydeps src/app.py --noshow -T svg -o dependency.svg from module_5 and checks that the file exists. If pydeps fails or the file is missing, the job fails.

4. Run Snyk test: The workflow sets up Node (for the Snyk CLI), installs Snyk globally with npm, and runs snyk test from module_5. Authentication uses the SNYK_TOKEN repository secret (a Snyk Personal Access Token or API key added under GitHub Settings → Secrets and variables → Actions). The step is configured with continue-on-error: true because of the vulnerability that snyk test found in Step 6: I kept llama-cpp-python for the Pull Data feature even though it brings in the vulnerable diskcache dependency and no patch is available, so Snyk will report that finding and exit with code 1 on every run. With continue-on-error: true, the workflow still passes and the scan output appears in the Actions log; the tradeoff is documented here and in Step 6. 

5. Pytest again”: The final step runs PYTHONPATH=src pytest again. Together with step 2, this satisfies the requirement that the workflow run pytest and fail if the coverage is below 100%


Running Scrape/Clean Pipeline and Readthedocs Out of Module_5 Project Folder: Last thing I did in this assignment is update my scrape/clean pipeline code to properly run out of the module_5 .venv. Also, I updated my Sphinx and readthedocs yaml file to run out of the module_5 folder. The installation requirements in my overview.rst and all references to the module_5 folder in readthedocs were updated to reflect module_5. I ran the app.py, the full scrape/clean pipeline using the buttons on the Flask webpage, confirmed the Update Analysis button works and displays new analysis, and ensured the readthedocs builds successfully with updated data from module_5. The whole project passes Pylint with a 10/10 and my Pytest suite with 100% coverage. 




Known Bugs – 

Snyk test identified 1 vulnerability (Deserialization of Untrusted Data (High Severity) in diskcache@5.6.3) that I chose to accept since the local LLM that cleans university and program data requires this package. To acknowledge that I accepted this vulnerability, I ensured that my GitHub CI workflow acknowledges the vulnerability. I assess that this vulnerability is acceptable due to the fact that the local LLM operates in a local environment and is not at risk to public threats. 


Citations – 
ChatGPT and GPT 5.2 CODEX assisted with the learning and coding of this project. 
