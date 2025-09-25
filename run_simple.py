"""
Run the simplified version
"""
import subprocess
import sys

if __name__ == "__main__":
    subprocess.run([sys.executable, "-m", "uvicorn", "src.main_simple:app", "--reload", "--host", "0.0.0.0", "--port", "8000"])
