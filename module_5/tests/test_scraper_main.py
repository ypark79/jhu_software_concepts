# Tests for Scraper.main (pipeline orchestrator)

import builtins
import io
import json
import sys
import types

import pytest

import Scraper.main as scraper_main


def _patch_scraper_main(monkeypatch, tmp_path):
    """Apply mocks for scraper_main pipeline."""
    raw_file = tmp_path / "raw_scraped_data.json"
    raw_file.write_text(json.dumps([]), encoding="utf-8")

    class FakePopen:
        def poll(self):
            return None

    class FakeResp:
        def read(self):
            return b"ok"

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_open(path, mode="r", *args, **kwargs):
        if "raw_scraped_data" in str(path):
            return io.StringIO("[]")
        raise FileNotFoundError(path)

    monkeypatch.setattr(scraper_main.subprocess, "Popen",
                        lambda *a, **k: FakePopen())
    monkeypatch.setattr(
        scraper_main.subprocess, "run",
        lambda *a, **k: type('R', (), {'returncode': 0})()
    )
    monkeypatch.setattr(scraper_main, "urlopen",
                        lambda *a, **k: FakeResp())
    monkeypatch.setattr(scraper_main.time, "sleep", lambda x: None)
    monkeypatch.setattr(
        scraper_main.os.path, "exists",
        lambda p: "raw_scraped_data" in str(p)
    )
    monkeypatch.setattr("builtins.open", fake_open)
    monkeypatch.setattr(scraper_main.clean, "main", lambda: None)
    monkeypatch.chdir(tmp_path)


@pytest.mark.analysis
def test_scraper_main_function(monkeypatch, tmp_path):
    """Run Scraper.main.main() with mocks to cover the pipeline."""
    _patch_scraper_main(monkeypatch, tmp_path)
    scraper_main.main()


@pytest.mark.analysis
def test_scraper_main_wait_for_llm_fails(monkeypatch, tmp_path):
    """Cover early return when wait_for_llm returns False."""
    monkeypatch.setattr(scraper_main, "wait_for_llm", lambda timeout_seconds=300: False)
    monkeypatch.setattr(
        scraper_main.subprocess, "Popen",
        lambda *a, **k: type('P', (), {'poll': lambda: None})()
    )
    monkeypatch.chdir(tmp_path)

    scraper_main.main()  # Returns early when wait_for_llm fails


@pytest.mark.analysis
def test_scraper_main_run_scrape_fails(monkeypatch, tmp_path):
    """Cover early return when run_scrape returns non-zero."""
    class FakeResp:
        def read(self):
            return b"ok"

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_run(*args, **kwargs):
        return type('R', (), {'returncode': 1})()

    monkeypatch.setattr(scraper_main, "urlopen", lambda *a, **k: FakeResp())
    monkeypatch.setattr(scraper_main.subprocess, "Popen",
                        lambda *a, **k: type('P', (), {'poll': lambda: None})())
    monkeypatch.setattr(scraper_main.subprocess, "run", fake_run)
    monkeypatch.setattr(scraper_main.time, "sleep", lambda x: None)
    monkeypatch.chdir(tmp_path)

    scraper_main.main()


@pytest.mark.analysis
def test_scraper_main_wait_for_file_fails(monkeypatch, tmp_path):
    """Cover early return when wait_for_file returns False."""
    class FakeResp:
        def read(self):
            return b"ok"

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(scraper_main, "urlopen", lambda *a, **k: FakeResp())
    monkeypatch.setattr(
        scraper_main, "wait_for_file",
        lambda path, timeout_seconds=300: False
    )
    monkeypatch.setattr(scraper_main.subprocess, "Popen",
                        lambda *a, **k: type('P', (), {'poll': lambda: None})())
    monkeypatch.setattr(
        scraper_main.subprocess, "run",
        lambda *a, **k: type('R', (), {'returncode': 0})()
    )
    monkeypatch.chdir(tmp_path)

    scraper_main.main()


@pytest.mark.analysis
def test_scraper_main_json_sanity_check_fails(monkeypatch, tmp_path):
    """Cover early return when json_sanity_check raises (invalid JSON)."""
    raw_file = tmp_path / "raw_scraped_data.json"
    raw_file.write_text("not valid json", encoding="utf-8")

    class FakeResp:
        def read(self):
            return b"ok"

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(scraper_main, "urlopen", lambda *a, **k: FakeResp())
    monkeypatch.setattr(
        scraper_main, "wait_for_file",
        lambda path, timeout_seconds=300: True
    )
    monkeypatch.setattr(scraper_main.subprocess, "Popen",
                        lambda *a, **k: type('P', (), {'poll': lambda: None})())
    monkeypatch.setattr(
        scraper_main.subprocess, "run",
        lambda *a, **k: type('R', (), {'returncode': 0})()
    )
    monkeypatch.setattr(scraper_main.os, "chdir", lambda p: None)
    monkeypatch.chdir(tmp_path)

    scraper_main.main()


@pytest.mark.analysis
def test_scraper_main_json_not_list(monkeypatch, tmp_path):
    """Cover json_sanity_check when JSON root is not a list."""
    raw_file = tmp_path / "raw_scraped_data.json"
    raw_file.write_text('{"key": "value"}', encoding="utf-8")

    class FakeResp:
        def read(self):
            return b"ok"

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(scraper_main, "urlopen", lambda *a, **k: FakeResp())
    monkeypatch.setattr(
        scraper_main, "wait_for_file",
        lambda path, timeout_seconds=300: True
    )
    monkeypatch.setattr(scraper_main.subprocess, "Popen",
                        lambda *a, **k: type('P', (), {'poll': lambda: None})())
    monkeypatch.setattr(
        scraper_main.subprocess, "run",
        lambda *a, **k: type('R', (), {'returncode': 0})()
    )
    monkeypatch.setattr(scraper_main.os, "chdir", lambda p: None)
    monkeypatch.chdir(tmp_path)

    scraper_main.main()


@pytest.mark.analysis
def test_scraper_main_helpers(tmp_path):
    """Cover helper functions: json_sanity_check, wait_for_llm, wait_for_file."""
    valid = tmp_path / "valid.json"
    valid.write_text("[]", encoding="utf-8")
    assert scraper_main.json_sanity_check(str(valid)) == 0

    with pytest.raises(ValueError, match="not a list"):
        bad = tmp_path / "bad.json"
        bad.write_text('{}', encoding="utf-8")
        scraper_main.json_sanity_check(str(bad))


@pytest.mark.analysis
def test_wait_for_llm_timeout(monkeypatch):
    """Cover wait_for_llm timeout path."""
    def fake_urlopen_raise(*a, **k):
        raise OSError("refused")
    monkeypatch.setattr(scraper_main, "urlopen", fake_urlopen_raise)
    monkeypatch.setattr(scraper_main.time, "time",
                        lambda: 0)  # start; then sleep
    called = {"n": 0}
    def fake_sleep(x):
        called["n"] += 1
        if called["n"] > 0:
            # After first sleep, make time exceed timeout
            monkeypatch.setattr(
                scraper_main.time, "time",
                lambda: 301
            )
    monkeypatch.setattr(scraper_main.time, "sleep", fake_sleep)
    assert scraper_main.wait_for_llm(timeout_seconds=300) is False


@pytest.mark.analysis
def test_wait_for_file_timeout(monkeypatch, tmp_path):
    """Cover wait_for_file timeout path (loop and return False)."""
    monkeypatch.setattr(scraper_main.os.path, "exists", lambda p: False)
    t = [1000.0]  # mutable so fake_time can update
    def fake_time():
        return t[0]
    def fake_sleep(x):
        t[0] = 1010.0  # exceed timeout
    monkeypatch.setattr(scraper_main.time, "time", fake_time)
    monkeypatch.setattr(scraper_main.time, "sleep", fake_sleep)
    monkeypatch.chdir(tmp_path)
    assert scraper_main.wait_for_file(
        "nonexistent.json", timeout_seconds=5
    ) is False


@pytest.mark.analysis
def test_main_import_error_fallback(monkeypatch):
    """Cover ImportError fallback (lines 16-17) when 'from . import clean' fails."""
    real_import = builtins.__import__
    fake_clean = types.ModuleType("clean")
    fake_clean.main = lambda: None

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        # Simulate relative import failure for .clean
        if level >= 1 and fromlist and "clean" in fromlist:
            raise ImportError("attempted relative import with no known parent package")
        if name == "clean":
            return fake_clean
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    for mod in list(sys.modules.keys()):
        if mod == "Scraper.main" or mod == "Scraper":
            del sys.modules[mod]
    try:
        import Scraper.main as mod
        assert mod.clean is fake_clean
        mod.clean.main()  # no-op
    finally:
        # Restore modules for subsequent tests
        import importlib
        if "Scraper.main" not in sys.modules:
            importlib.import_module("Scraper.main")

