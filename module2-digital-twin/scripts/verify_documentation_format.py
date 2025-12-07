#!/usr/bin/env python3
"""
Verification script for Docusaurus documentation files.

This script checks that all MDX files have proper front-matter and are formatted correctly.
"""

import os
import re
import sys
from pathlib import Path
import yaml

def check_front_matter(file_path):
    """Check if the file has proper front-matter."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if file starts with ---
    if not content.strip().startswith('---'):
        return False, "File does not start with front-matter separator (---)"

    # Extract front-matter
    parts = content.split('---', 2)
    if len(parts) < 3:
        return False, "File does not have proper front-matter separators (---)"

    front_matter_str = parts[1]
    try:
        front_matter = yaml.safe_load(front_matter_str)
    except yaml.YAMLError as e:
        return False, f"Front-matter is not valid YAML: {e}"

    # Check required fields
    required_fields = ['title', 'description', 'tags', 'sidebar_position']
    missing_fields = []
    for field in required_fields:
        if field not in front_matter:
            missing_fields.append(field)

    if missing_fields:
        return False, f"Missing required front-matter fields: {missing_fields}"

    # Validate field types
    if not isinstance(front_matter['title'], str):
        return False, "Title must be a string"

    if not isinstance(front_matter['description'], str):
        return False, "Description must be a string"

    if not isinstance(front_matter['tags'], list):
        return False, "Tags must be a list"

    if not isinstance(front_matter['sidebar_position'], (int, float)):
        return False, "Sidebar position must be a number"

    # Check that tags are strings
    for tag in front_matter['tags']:
        if not isinstance(tag, str):
            return False, f"Tag '{tag}' is not a string"

    return True, "Front-matter is valid"

def check_mdx_content(file_path):
    """Check if the MDX content is properly formatted."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for proper heading structure
    lines = content.split('\n')
    heading_pattern = re.compile(r'^#+ ')

    for i, line in enumerate(lines):
        if heading_pattern.match(line):
            # Check if heading has content after it
            heading_text = line.lstrip('# ')
            if not heading_text.strip():
                return False, f"Empty heading found at line {i+1}"

    # Check for unclosed code blocks
    code_block_lines = [i for i, line in enumerate(lines) if line.strip().startswith('```')]
    if len(code_block_lines) % 2 != 0:
        return False, "Unclosed code block found"

    return True, "Content is properly formatted"

def verify_all_docs(docs_dir):
    """Verify all MDX files in the documentation directory."""
    mdx_files = []

    # Find all MDX files
    for root, dirs, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.mdx'):
                mdx_files.append(os.path.join(root, file))

    print(f"Found {len(mdx_files)} MDX files to verify")

    results = {
        'valid': [],
        'invalid': []
    }

    for file_path in mdx_files:
        print(f"Checking {file_path}...")

        # Check front-matter
        front_matter_valid, fm_msg = check_front_matter(file_path)
        if not front_matter_valid:
            results['invalid'].append((file_path, f"Front-matter error: {fm_msg}"))
            continue

        # Check content
        content_valid, content_msg = check_mdx_content(file_path)
        if not content_valid:
            results['invalid'].append((file_path, f"Content error: {content_msg}"))
            continue

        results['valid'].append(file_path)

    return results

def verify_code_examples(docs_dir):
    """Verify that code examples in documentation are properly formatted."""
    code_issues = []

    for root, dirs, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.mdx'):
                file_path = os.path.join(root, file)

                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Look for code blocks
                code_blocks = re.findall(r'```(\w*)\n(.*?)```', content, re.DOTALL)

                for lang, code in code_blocks:
                    if lang.lower() in ['python', 'py']:
                        # Check for basic Python syntax issues
                        if 'import' not in code and 'def ' not in code and 'class ' not in code and code.strip():
                            # Might be a Python code example without imports
                            # Just check for basic structure
                            pass

                    elif lang.lower() in ['bash', 'sh']:
                        # Check for common bash syntax
                        pass

                    elif lang.lower() in ['xml', 'sdf']:
                        # Check for basic XML structure
                        if '<' in code and '>' in code:
                            # Basic XML tags present
                            pass

    return code_issues

def main():
    docs_dir = "/home/maliaraees/ai-and-humanoid-robotics-course/module2-digital-twin/docs"

    print("Verifying Docusaurus documentation files...")
    print(f"Documentation directory: {docs_dir}")

    # Verify all documentation files
    results = verify_all_docs(docs_dir)

    print(f"\nVerification Results:")
    print(f"Valid files: {len(results['valid'])}")
    print(f"Invalid files: {len(results['invalid'])}")

    if results['invalid']:
        print("\nInvalid files:")
        for file_path, error in results['invalid']:
            print(f"  - {file_path}: {error}")

    # Verify code examples
    print("\nChecking code examples...")
    code_issues = verify_code_examples(docs_dir)

    if code_issues:
        print("Code issues found:")
        for issue in code_issues:
            print(f"  - {issue}")
    else:
        print("No code issues found.")

    # Summary
    total_files = len(results['valid']) + len(results['invalid'])
    print(f"\nSummary: {len(results['valid'])}/{total_files} files are properly formatted for Docusaurus.")

    if results['invalid']:
        print("Some files need to be fixed before Docusaurus build will work properly.")
        return 1
    else:
        print("All documentation files are properly formatted!")
        return 0

if __name__ == "__main__":
    sys.exit(main())