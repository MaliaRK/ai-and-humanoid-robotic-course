#!/usr/bin/env python3
"""
Verification script for Unity C# scripts.

This script checks that all Unity C# scripts follow C# coding standards and are syntactically correct.
"""

import os
import re
import sys
from pathlib import Path

def validate_csharp_syntax(file_path):
    """Basic validation of C# syntax."""
    issues = []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    # Check for proper opening and closing braces
    brace_count = 0
    in_multiline_comment = False

    for i, line in enumerate(lines, 1):
        stripped_line = line.strip()

        # Handle multiline comments
        if '/*' in line and '*/' not in line:
            in_multiline_comment = True
        elif '*/' in line:
            in_multiline_comment = False
            continue  # Skip the line with closing comment

        if in_multiline_comment:
            continue

        # Count braces outside of comments
        for char in line:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count < 0:
                    issues.append(f"Line {i}: Unmatched closing brace")

    if brace_count > 0:
        issues.append(f"File: {brace_count} unmatched opening braces")

    # Check for proper using statements at the top
    using_found = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('using ') and not stripped.startswith('//'):
            using_found = True
        elif stripped and not stripped.startswith('using ') and not stripped.startswith('//') and not stripped.startswith('/*') and not stripped.startswith('*'):
            if not using_found and not '{' in stripped and not stripped.startswith('namespace'):
                # This might be an issue if usings are expected at the top
                pass
            break

    # Check for Unity-specific patterns
    if 'MonoBehaviour' in content:
        # Check for common Unity patterns
        if not re.search(r'void\s+Start\s*\(\s*\)', content):
            # Start method is not required but is common
            pass

        if not re.search(r'void\s+Update\s*\(\s*\)', content):
            # Update method is not required but is common
            pass

    # Check for proper class declaration
    class_match = re.search(r'(public|private|protected)?\s+(static\s+)?(partial\s+)?class\s+(\w+)', content)
    if not class_match:
        issues.append("File: No class declaration found")

    # Check for Unity-specific class inheritance
    if 'using UnityEngine;' in content:
        # If using Unity, check for MonoBehaviour inheritance
        mono_behaviour_match = re.search(r'class\s+\w+\s*:\s*(MonoBehaviour|ScriptableObject|Component)', content)
        if not mono_behaviour_match:
            # Not all Unity scripts inherit from MonoBehaviour, so this is just a check
            pass

    if issues:
        return False, "\n".join(issues)
    else:
        return True, "Syntax appears valid"

def check_csharp_style(file_path):
    """Check for basic C# style compliance."""
    issues = []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    # Check for PascalCase for public methods and classes
    for i, line in enumerate(lines, 1):
        # Check for method declarations
        method_match = re.search(r'(public|private|protected)\s+(static\s+)?\w+\s+(\w+)\s*\(', line)
        if method_match:
            method_name = method_match.group(3)
            if not method_name[0].isupper():
                issues.append(f"Line {i}: Method '{method_name}' should use PascalCase")

        # Check for class declarations
        class_match = re.search(r'(public|private|protected)\s+class\s+(\w+)', line)
        if class_match:
            class_name = class_match.group(2)
            if not class_name[0].isupper():
                issues.append(f"Line {i}: Class '{class_name}' should use PascalCase")

    # Check for camelCase for private fields
    for i, line in enumerate(lines, 1):
        # Check for private field declarations
        field_match = re.search(r'private\s+\w+\s+(\w+)', line)
        if field_match:
            field_name = field_match.group(1)
            # Unity convention is often m_variableName or underscore_prefix
            if not field_name.startswith('m_') and not field_name.startswith('_') and field_name[0].isupper():
                issues.append(f"Line {i}: Private field '{field_name}' should use camelCase or Unity convention (m_/_)")

    if issues:
        return False, "\n".join(issues)
    else:
        return True, "Style appears to follow C# conventions"

def verify_unity_scripts(project_dir):
    """Verify all Unity C# scripts in the project directory."""
    csharp_files = []

    # Find all C# files
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file.endswith('.cs'):
                csharp_files.append(os.path.join(root, file))

    print(f"Found {len(csharp_files)} C# files to verify")

    results = {
        'valid': [],
        'invalid': []
    }

    for file_path in csharp_files:
        print(f"Checking {file_path}...")

        # Check syntax
        syntax_valid, syntax_msg = validate_csharp_syntax(file_path)
        if not syntax_valid:
            results['invalid'].append((file_path, f"Syntax error: {syntax_msg}"))
            continue

        # Check style
        style_valid, style_msg = check_csharp_style(file_path)
        if not style_valid:
            results['invalid'].append((file_path, f"Style error: {style_msg}"))
            continue

        results['valid'].append(file_path)

    return results

def main():
    project_dir = "/home/maliaraees/ai-and-humanoid-robotics-course/module2-digital-twin"

    print("Verifying Unity C# scripts...")
    print(f"Project directory: {project_dir}")

    # Verify all C# files
    results = verify_unity_scripts(project_dir)

    print(f"\nC# Scripts Verification Results:")
    print(f"Valid files: {len(results['valid'])}")
    print(f"Invalid files: {len(results['invalid'])}")

    if results['invalid']:
        print("\nInvalid C# files:")
        for file_path, error in results['invalid']:
            print(f"  - {file_path}: {error}")

    # Summary
    total_files = len(results['valid']) + len(results['invalid'])
    print(f"\nSummary: {len(results['valid'])}/{total_files} C# files are properly formatted.")

    if results['invalid']:
        print("Some C# files need to be fixed to comply with C# standards.")
        return 1
    else:
        print("All C# files are properly formatted!")
        return 0

if __name__ == "__main__":
    sys.exit(main())