"""
Convenience wrapper to run data/prep_anime.py over the large raw dataset and log summary.
"""
import subprocess
import sys

CMD = ["python", "data/prep_anime.py", "--upload"]

if __name__ == "__main__":
    print("Running music removal batch (stub)...")
    try:
        subprocess.check_call(CMD)
    except subprocess.CalledProcessError as e:
        print("Data prep failed", e)
        sys.exit(1)
    print("Batch run complete (stub)")
