Testing Guide
=============
This page explains pytest markers, selectors, and how fixtures/monkeypatch are used.

The tests are written with **pytest** and use **100% coverage** for
``module_4/src``.

How to run all tests
--------------------
From the repo root:

``PYTHONPATH=module_4/src pytest -c module_4/pytest.ini``

Markers used
------------
All tests are marked as required by the assignment:

- ``web``: Flask page and route tests
- ``buttons``: button routes and busy-state behavior
- ``analysis``: label and percentage formatting
- ``db``: database insert and query checks
- ``integration``: end-to-end flow

You can run the full suite with:

``pytest -m "web or buttons or analysis or db or integration"``

Test helpers and patterns
-------------------------
- **Flask test client**: sends GET/POST requests without a real browser
- **Monkeypatch**: replaces network calls, database calls, and subprocesses
- **Fake data**: makes tests fast and deterministic
- **BeautifulSoup + regex**: checks HTML labels and percent formatting

Busy-state policy
-----------------
If a scrape is running, the app should return:

- ``/pull-data`` → 409 with ``{"busy": True}``
- ``/update-analysis`` → 409 with ``{"busy": True}``

This keeps the UI safe and prevents duplicate work.

Selectors and fixtures
----------------------
Selectors:

- We use HTML elements and attributes (like button text or form actions)
  to find the correct UI elements in tests.

Fixtures:

- We use small fake datasets (rows) and helper functions so tests run fast
  and do not touch the real network or database.