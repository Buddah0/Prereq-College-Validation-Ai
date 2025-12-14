import os
import sys
from pathlib import Path

# Ensure we can import from scripts
# Since main.py is in the root, scripts is a submodule
from scripts.analyze import analyze_course_graph

if __name__ == "__main__":
    # Use sample output by default
    sample_path = "samples/sample-output.json"
    if os.path.exists(sample_path):
        analyze_course_graph(sample_path)
    else:
        print("Sample data not found at samples/sample-output.json")
