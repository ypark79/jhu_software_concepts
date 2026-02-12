"""Orchestrate the scrape -> clean pipeline with a local LLM server."""

# os manages paths/files, subprocess enables running multiple scripts,
# sys ensures the use of the current Python interpreter, time used for
# wait periods, json used to validate output files of the scripts,
# and urllib used to reach and execute the LLM server.
import os
import sys
import time
import json
import subprocess
from urllib.request import urlopen

import clean

raw_file = "raw_scraped_data.json"
llm_dir = "llm_hosting"
llm_script = "app.py"
scrape_script = "scrape.py"
llm_health_url = "http://127.0.0.1:8000/"


# This function ensure the local LLM starts and stays running in the
# background.
def start_llm_server():
    """Start the local LLM server in the background."""
    # Optimize settings to reduce crashes or overwhelming CPU.
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "1"
    env["LLAMA_NUM_THREADS"] = "1"

    # subprocess.Popen runs app.py and allows code to continue.
    # Local LLM must stay running while scrape.py then clean.py run.
    # must stay running while scrape.py then clean.py are executed.
    return subprocess.Popen([sys.executable, llm_script], cwd=llm_dir,
                            env=env)


# Retries the LLM server until it is up and running.
def wait_for_llm(timeout_seconds=300):
    """Poll the LLM health endpoint until ready or timed out."""

    start = time.time()
    # Check the time per loop to determine how much time has elapsed.
    # Retries if opening the server fails.
    while time.time() - start < timeout_seconds:
        try:
            urlopen(llm_health_url, timeout=5)
            print("LLM server is ready.")
            return True
        except Exception:
            time.sleep(5)

    print("Timed out waiting for LLM server.")
    return False

# Once LLM is running, execute scrape.py.
def run_scrape():
    """Run scrape.py as a subprocess and return its exit code."""
    print("Running scrape.py")
    # Pauses main.py until scrape.py is complete.
    result = subprocess.run([sys.executable, scrape_script])
    return result.returncode


# Safety measure to ensure that the output of scrape.py
# exists before moving on.
def wait_for_file(path, timeout_seconds=300):
    """Wait for a file to exist within a timeout window."""
    print(f"Waiting for {path} to be created")
    start = time.time()

    while time.time() - start < timeout_seconds:
        if os.path.exists(path):
            print(f"Found {path}.")
            return True
        time.sleep(5)

    print(f"Timed out waiting for {path}.")
    return False

# Safety check to ensure that the output of script is a valid
# JSON file.
def json_sanity_check(path):
    """Basic JSON check: can we load it and is it a list?"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON root is not a list")

    return len(data)

# Ensures that all python files are executed in the proper order.
def main():
    """Run the full pipeline: start LLM, scrape, validate, clean."""
    # Make sure relative paths work no matter where user runs this from.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print("\n=== Pipeline Start ===\n")

    #Initiate app.py
    start_llm_server()

    # Waits for LLM server to be running.
    if not wait_for_llm():
        return

    # Execute scrape.py
    code = run_scrape()
    if code != 0:
        print(f"scrape.py failed with exit code {code}")
        return

    # Wait until raw JSON file exists.
    if not wait_for_file(raw_file):
        return

    # Validate the output file of scrape.py
    try:
        n = json_sanity_check(raw_file)
        print(f"raw_scraped_data.json loaded successfully ({n} rows).")
    except Exception as e:
        print(f"raw_scraped_data.json is not valid JSON: {e}")
        return

    # Run clean.py
    print("Running clean.py...")
    clean.main()

    print("Pipeline complete")
    print("Outputs generated:")
    print("llm_extend_applicant_data.json")
    print("applicant_data.json")


if __name__ == "__main__":
    main()