# Test buttons and busy state behavior.
import os
import sys
import pytest
from app import create_app
import app


# Create a fake process object to simulate if the
# code is running or finished.
class DummyProcess:
    def __init__(self, running: bool):
        # If running=True, poll() should return None (still running)
        self._running = running

    def poll(self):
        # None means "still running" in subprocess
        return None if self._running else 0


@pytest.mark.buttons
# This function will test if the "Pull Data" button is avaiable to click
# when the process is not running.
def test_pull_data_returns_ok_and_calls_loader(monkeypatch):
    app = create_app()
    # Create a fake browser to send POST requests.
    client = app.test_client()

    # Determine if the fake loader was called by tracking the value.
    # A false value means that the loader was not called.
    called = {"value": False}

    # Fake subprocess.Popen without running the real scraper.
    # DummyProcess(running=False) means that the process is not running.
    # called['value'] = True means that the loader was called. Therefore
    # if the loader was called, the process should not be running.
    def fake_popen(*args, **kwargs):
        called["value"] = True
        return DummyProcess(running=False)

    # Monkeypatch simulates a user running the scraper without
    # actually running the scraper. Simulates the subprocess.Popen.
    monkeypatch.setattr("app.subprocess.Popen", fake_popen)

    # Ensure the process is not running.
    app.scraping_process = None

    # Send POST request to pull-data
    response = client.post("/pull-data")

    # Confirms that the POST to the /pull-data route was successful
    # and the code returned the expected JSON output.
    assert response.status_code == 200
    assert response.get_json() == {"ok": True}

    # Confirm our fake loader was called
    assert called["value"] is True


@pytest.mark.buttons
# This function will test if the "Update Analysis" button
# is available to click when the process is not running.
def test_update_analysis_returns_ok_when_not_busy():
    app = create_app()
    client = app.test_client()

    # Simulates that the process is not running.
    app.scraping_process = None

    response = client.post("/update-analysis")

    # Route redirects to analysis page when not busy (no JSON response).
    assert response.status_code == 302
    assert response.headers.get("Location", "").endswith("/analysis")


@pytest.mark.buttons
# This test will check if the "Update Analysis" button
# is disabled when the process is running.
def test_busy_update_analysis():
    app = create_app()
    client = app.test_client()

    # Simulates that the process is running.
    app.scraping_process = DummyProcess(running=True)  # busy

    response = client.post("/update-analysis")

    # Should return 409 and JSON {"busy": True} to
    # show no analysis was updated while running.
    assert response.status_code == 409
    assert response.get_json() == {"busy": True}


@pytest.mark.buttons
# This test will check if the "Pull Data" button is disabled when the
# process is running.
def test_busy_for_pull_data(monkeypatch):
    app = create_app()
    client = app.test_client()

    # Loader is not called when process is running.
    def fake_popen(*args, **kwargs):
        raise AssertionError("Loader should not run when busy")

    # Replace the real subprocess.Popen inside app.py with a fake
    # subprocess.Popen.
    monkeypatch.setattr("app.subprocess.Popen", fake_popen)

    # Simulates that the process is running.
    app.scraping_process = DummyProcess(running=True)

    response = client.post("/pull-data")

    # Should return 409 and JSON {"busy": True} to
    # show no data was pulled while running.
    assert response.status_code == 409
    assert response.get_json() == {"busy": True}


@pytest.mark.buttons
def test_module5_python_returns_venv_when_found(monkeypatch):
    """When .venv exists, _module5_python returns its python path (covers line 37 on CI)."""
    src_dir = os.path.dirname(os.path.abspath(app.__file__))
    module5_root = os.path.dirname(src_dir)
    subdir = 'Scripts' if os.name == 'nt' else 'bin'
    exe = 'python.exe' if os.name == 'nt' else 'python'
    expected = os.path.join(module5_root, '.venv', subdir, exe)
    monkeypatch.setattr("app.os.path.isfile", lambda p: p == expected)
    assert app._module5_python() == expected


@pytest.mark.buttons
def test_module5_python_fallback_when_no_venv(monkeypatch):
    """When no .venv/.venv.test exists, _module5_python returns sys.executable."""
    monkeypatch.setattr("app.os.path.isfile", lambda _: False)
    assert app._module5_python() == sys.executable
