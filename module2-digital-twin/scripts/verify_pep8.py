#!/usr/bin/env python3
"""
Verification script for PEP8 compliance in Python files.

This script checks that all Python files follow PEP8 standards.
"""

import os
import subprocess
import sys
from pathlib import Path

def check_pep8_compliance(file_path):
    """Check if a Python file is PEP8 compliant."""
    try:
        # Use pycodestyle (formerly pep8) to check PEP8 compliance
        result = subprocess.run(
            ['pycodestyle', '--max-line-length=100', file_path],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return True, "PEP8 compliant"
        else:
            return False, result.stdout.strip()
    except FileNotFoundError:
        # If pycodestyle is not installed, use a basic check
        return basic_pep8_check(file_path)

def basic_pep8_check(file_path):
    """Basic PEP8 checks without pycodestyle."""
    issues = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines, 1):
        stripped = line.rstrip()  # Remove trailing whitespace

        # Check line length (PEP8 recommends max 79 characters, using 100 for practicality)
        if len(stripped) > 100:
            issues.append(f"Line {i}: Line too long ({len(stripped)} > 100 characters)")

        # Check for trailing whitespace
        if line != stripped + '\n':
            issues.append(f"Line {i}: Trailing whitespace")

        # Check for tabs vs spaces
        if '\t' in line:
            issues.append(f"Line {i}: Contains tab character, use spaces instead")

    if issues:
        return False, "\n".join(issues)
    else:
        return True, "Passes basic PEP8 checks"

def verify_python_files(project_dir):
    """Verify all Python files in the project directory."""
    python_files = []

    # Find all Python files
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    print(f"Found {len(python_files)} Python files to verify")

    results = {
        'compliant': [],
        'non_compliant': []
    }

    for file_path in python_files:
        print(f"Checking {file_path}...")
        is_compliant, message = check_pep8_compliance(file_path)

        if is_compliant:
            results['compliant'].append(file_path)
        else:
            results['non_compliant'].append((file_path, message))

    return results

def main():
    project_dir = "/home/maliaraees/ai-and-humanoid-robotics-course/module2-digital-twin"

    print("Verifying PEP8 compliance in Python files...")
    print(f"Project directory: {project_dir}")

    # Verify all Python files
    results = verify_python_files(project_dir)

    print(f"\nPEP8 Compliance Results:")
    print(f"Compliant files: {len(results['compliant'])}")
    print(f"Non-compliant files: {len(results['non_compliant'])}")

    if results['non_compliant']:
        print("\nNon-compliant files:")
        for file_path, error in results['non_compliant']:
            print(f"  - {file_path}:")
            for line in error.split('\n'):
                if line.strip():
                    print(f"      {line}")

    # Summary
    total_files = len(results['compliant']) + len(results['non_compliant'])
    print(f"\nSummary: {len(results['compliant'])}/{total_files} Python files are PEP8 compliant.")

    if results['non_compliant']:
        print("Some Python files need to be fixed to comply with PEP8 standards.")
        return 1
    else:
        print("All Python files are PEP8 compliant!")
        return 0

if __name__ == "__main__":
    sys.exit(main())