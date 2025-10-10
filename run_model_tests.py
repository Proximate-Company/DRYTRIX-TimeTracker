#!/usr/bin/env python
"""Simple test runner to check model tests."""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "-m", "unit and models", "-v", "--tb=short"],
    capture_output=True,
    text=True
)

with open("test_results_model.txt", "w", encoding="utf-8") as f:
    f.write(result.stdout)
    f.write("\n")
    f.write(result.stderr)
    f.write(f"\n\nExit code: {result.returncode}\n")

print("Test results written to test_results_model.txt")
print(f"Exit code: {result.returncode}")

