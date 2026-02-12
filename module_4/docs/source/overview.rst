Overview and Setup
==================
This page explains how to set up the project, required environment variables,
and how to run the app and tests.

This project is a Grad Cafe analytics system. It scrapes Grad Cafe results,
cleans the data, stores it in PostgreSQL, and displays analysis on a Flask web
page.

What the app does
-----------------
- Pulls new Grad Cafe results (scrape)
- Cleans and standardizes raw text (clean)
- Loads cleaned rows into PostgreSQL (load)
- Runs summary queries and shows results on the Analysis page (web)

Project structure
-----------------
- ``module_4/src``: application code
- ``module_4/tests``: pytest test suite
- ``module_4/docs``: Sphinx documentation

Setup (local)
-------------
1. Create and activate a virtual environment:

   ``python -m venv module_4/.venv``

   ``source module_4/.venv/bin/activate``

2. Install dependencies:

   ``pip install flask psycopg beautifulsoup4 pytest pytest-cov``

3. Start PostgreSQL locally and create a database (example):

   - Database name: ``module_4_db_test``

Environment variables
---------------------
These are used to connect to PostgreSQL:

- ``PGHOST`` (example: ``localhost``)
- ``PGPORT`` (example: ``5432``)
- ``PGUSER`` (example: your local DB username)
- ``PGPASSWORD`` (example: your local DB password)
- ``PGDATABASE`` (example: ``module_4_db_test``)

Run the app
-----------
From the repo root:

``PYTHONPATH=module_4/src python module_4/src/app.py``

Then open:

``http://127.0.0.1:8080/analysis``

Run the tests
-------------
From the repo root:

``PYTHONPATH=module_4/src pytest -c module_4/pytest.ini``