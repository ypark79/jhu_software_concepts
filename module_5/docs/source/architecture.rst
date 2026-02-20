Architecture
============
This page explains the Web, ETL, and Database roles and how they connect.

This system has three main parts: Web, ETL, and Database.

Web (Flask)
-----------
- File: ``module_5/src/app.py``
- Provides the Analysis web page at ``/analysis``
- Provides button routes:
  - ``/pull-data`` (start scraping)
  - ``/update-analysis`` (refresh page when not busy)
  - ``/scrape-status`` (busy state check)

ETL (Scrape + Clean + Load)
---------------------------
- File: ``module_5/src/Scraper/main.py``
  - Orchestrates the pipeline
- File: ``module_5/src/Scraper/scrape.py``
  - Downloads and parses Grad Cafe HTML
- File: ``module_5/src/Scraper/clean.py``
  - Cleans raw rows and inserts into PostgreSQL
- File: ``module_5/src/load_data.py``
  - Loads cleaned JSON into PostgreSQL (used for batch loading)

Database (PostgreSQL)
---------------------
- The database stores cleaned applicant rows
- Queries run in:
  - ``module_5/src/query_data.py`` (console outputs)
  - ``module_5/src/app.py`` (analysis page)

Data flow (high level)
----------------------
1. User clicks ``Pull Data``
2. Scraper pulls raw data → Cleaner standardizes it
3. Clean data is stored in PostgreSQL
4. Analysis page runs SQL queries and displays results