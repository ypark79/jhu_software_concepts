import sys
import os
import time
import json
import subprocess
from urllib.request import urlopen

import clean  # uses your clean.py

RAW_FILE = "applicant_data.json"
LLM_HEALTH_URL = "http://127.0.0.1:8000/"


def wait_for_llm(timeout_seconds: int = 300) -> bool:
    """
    Wait until the local LLM server is reachable.
    Returns True if reachable, False if timeout.
    """
    print("Checking that app.py (LLM server) is running...")
    start = time.time()

    while time.time() - start < timeout_seconds:
        try:
            resp = urlopen(LLM_HEALTH_URL, timeout=5)
            body = resp.read().decode("utf-8", errors="replace")
            if "ok" in body.lower():
                print("✅ LLM server is reachable.")
                return True
        except Exception:
            pass

        print("LLM not ready yet... waiting 5 seconds")
        time.sleep(5)

    print("❌ Timed out waiting for the LLM server. Start app.py first.")
    return False


def run_scrape() -> int:
    """
    Run scrape.py as a subprocess using the current Python interpreter.
    Returns the exit code.
    """
    print("\nStarting scrape.py...\n")
    proc = subprocess.run([sys.executable, "scrape.py"])
    return proc.returncode


def wait_for_file_stable(path: str, check_every_seconds: int = 10, stable_checks: int = 2) -> None:
    """
    Wait until a file exists and stops changing size.
    stable_checks=2 means "same size twice in a row".
    """
    while not os.path.exists(path):
        print(f"{path} not found yet... waiting {check_every_seconds} seconds")
        time.sleep(check_every_seconds)

    print(f"Found {path}. Waiting for it to stop changing...")

    last_size = -1
    same_count = 0

    while True:
        size = os.path.getsize(path)
        if size == last_size:
            same_count += 1
        else:
            same_count = 0

        if same_count >= stable_checks:
            break

        last_size = size
        time.sleep(check_every_seconds)

    print(f"✅ {path} looks stable.")


def quick_json_sanity_check(path: str) -> int:
    """
    Loads the JSON and returns number of entries.
    If invalid JSON, raises an exception.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"{path} does not contain a JSON list.")

    return len(data)


def main():
    # --- Make sure we run from the folder that contains main.py ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # ----
    # --- Optional safety: remove old output so you don't clean stale data ---
    # Comment these two lines out if you prefer to resume from existing files.
    if os.path.exists(RAW_FILE):
        os.remove(RAW_FILE)
        print(f"Deleted old {RAW_FILE} so this run starts fresh.")

    # 1) Run scrape.py (this blocks until scrape.py finishes)
    scrape_exit = run_scrape()
    if scrape_exit != 0:
        print(f"\n❌ scrape.py exited with code {scrape_exit}. Not running clean.py.")
        return

    # 2) Ensure applicant_data.json exists and is stable
    wait_for_file_stable(RAW_FILE, check_every_seconds=10, stable_checks=2)

    # 3) Sanity check the JSON file
    try:
        n = quick_json_sanity_check(RAW_FILE)
        print(f"✅ applicant_data.json is valid JSON. Entries: {n}")
    except Exception as e:
        print(f"❌ applicant_data.json sanity check failed: {e}")
        return

    # 4) Confirm LLM server is up before starting clean
    if not wait_for_llm(timeout_seconds=300):
        return

    # 5) Run clean.py
    print("\nStarting clean.py...\n")
    clean.main()
    print("\n✅ clean.py finished. Pipeline complete.")


if __name__ == "__main__":
    main()