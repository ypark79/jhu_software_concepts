import time
import os
import clean   # imports your clean.py

RAW_FILE = "applicant_data.json"

def main():
    print("Waiting for scrape.py to finish...")

    # Wait for file to appear
    while not os.path.exists(RAW_FILE):
        print("applicant_data.json not found yet... waiting 10 seconds")
        time.sleep(10)

    # Wait for file to stop growing (means scrape.py finished writing)
    print("File detected. Waiting for scrape to complete writing...")
    last_size = -1
    while True:
        current_size = os.path.getsize(RAW_FILE)
        if current_size == last_size:
            break
        last_size = current_size
        time.sleep(10)

    print("scrape.py finished.")
    print("Starting clean.py...\n")

    # Run clean.py
    clean.main()

    print("\n✅ clean.py finished. Pipeline complete.")

if __name__ == "__main__":
    main()