"""Entry point for pydeps to trace module dependencies."""
from Scraper import clean, scrape, main as scraper_main
import app
import db_connection
import load_data
import query_data

# Satisfies Pylint: names are used here; pydeps reads imports for graph
_DEPS = (clean, scrape, scraper_main, app, db_connection, load_data, query_data)
