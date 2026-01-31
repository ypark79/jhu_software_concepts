import sys
import os
import time
import json
import subprocess
from urllib.request import urlopen

import clean  # your clean.py

# ---------------- CONFIG ----------------

RAW_FILE = "raw_scraped_data.json"

LLM_DIR = "llm_hosting"     # folder containing app.py + model files
LLM_SCRIPT = "app.py"

SCRAPE_SCRIPT = "scrape.py"

LLM_HEALTH_URL = "http://127.0.0.1:8000/"

# ---------------- UTILITIES ----------------

def wait_for_llm(timeout_seconds: int = 300) -> bool:
    """
    Wait until the local LLM server is reachable.
    """
    print("Checking that app.py (LLM server) is running...")
    start = time.time()

    while time.time() - start < timeout_seconds:
        try:
            resp = urlopen(LLM_HEALTH_URL, timeout=5)
            body = resp.read().decode("utf-8", errors="replace")

            # If Flask is up, we assume server is ready
            print("✅ LLM server is reachable.")
            return True

        except Exception:
            print("LLM not ready yet... waiting 5 seconds")
            time.sleep(5)

    print("❌ Timed out waiting for the LLM server.")
    return False


def start_llm_server():
    """
    Starts app.py as a background process from llm_hosting folder.
    """
    print("\nStarting local LLM (app.py)...\n")

    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "1"
    env["LLAMA_NUM_THREADS"] = "1"

    proc = subprocess.Popen(
        [sys.executable, LLM_SCRIPT],
        cwd=LLM_DIR,     # IMPORTANT: run from inside llm_hosting
        env=env
    )

    return proc


def run_scrape() -> int:
    """
    Run scrape.py as a blocking subprocess.
    """
    print("\nStarting scrape.py...\n")
    proc = subprocess.run([sys.executable, SCRAPE_SCRIPT])
    return proc.returncode


def wait_for_file_stable(path: str, check_every_seconds: int = 10, stable_checks: int = 2) -> None:
    """
    Wait until a file exists and stops changing size.
    """
    while not os.path.exists(path):
        print(f"{path} not found yet... waiting {check_every_seconds}s")
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

    print(f"✅ {path} is stable.")


def quick_json_sanity_check(path: str) -> int:
    """
    Loads JSON and returns number of entries.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON root is not a list")

    return len(data)

# ---------------- MAIN PIPELINE ----------------

def main():
    # Ensure working directory is module_2
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print("\n=== AUTOMATED PIPELINE START ===\n")

    # 1) Start LLM server
    llm_proc = start_llm_server()

    # 2) Wait for LLM to be reachable
    if not wait_for_llm(timeout_seconds=300):
        print("❌ LLM failed to start. Exiting pipeline.")
        return

    # 3) Always run scrape.py (no assumptions about files existing)
    scrape_exit = run_scrape()
    if scrape_exit != 0:
        print(f"\n❌ scrape.py exited with code {scrape_exit}. Pipeline stopping.")
        return

    # 4) Wait for raw scraped file to exist and stabilize
    wait_for_file_stable(RAW_FILE, check_every_seconds=10, stable_checks=2)

    # 5) Sanity check JSON
    try:
        n = quick_json_sanity_check(RAW_FILE)
        print(f"✅ raw_scraped_data.json valid. Entries: {n}")
    except Exception as e:
        print(f"❌ JSON sanity check failed: {e}")
        return

    # 6) Run clean.py
    print("\nStarting clean.py...\n")
    clean.main()

    print("\n✅ PIPELINE COMPLETE")
    print("Outputs generated:")
    print(" - llm_extend_applicant_data.json")
    print(" - applicant_data.json")
    print("\nReady for submission.")

if __name__ == "__main__":
    main()