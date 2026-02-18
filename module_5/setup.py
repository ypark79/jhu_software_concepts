"""Setup script for Grad Cafe Analytics (module_5)."""
from setuptools import find_packages, setup

setup(
    name="gradcafe-analytics",
    version="1.0.0",
    description="Grad Cafe Analytics — scrape, clean, and analyze application results",
    author="Youngmin Park",
    python_requires=">=3.10",
    # Tells setuptools: "The root of my package code lives in the 'src' folder."
    # Empty string "" means "from the project root," so "src" is the package root.
    package_dir={"": "src"},
    # Automatically finds all packages (folders with __init__.py) inside src/,
    # e.g. Scraper, Scraper.llm_hosting.
    packages=find_packages("src"),
    # Standalone .py files at the top level of src/ that are not inside a package.
    # These become importable as "import app", "import db_connection", etc.
    py_modules=["app", "db_connection", "load_data", "query_data"],
    # Dependencies pip will install when user runs "pip install -e ."
    install_requires=[
        "Flask>=3.0",
        "psycopg[binary]>=3.0",
        "beautifulsoup4>=4.12",
        "requests>=2.28",
        "PyYAML>=6.0",
    ],
)
