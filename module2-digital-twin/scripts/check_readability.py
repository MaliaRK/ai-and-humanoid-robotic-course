#!/usr/bin/env python3
"""
Readability checker for documentation files.

This script checks that all documentation files meet readability standards (Flesch-Kincaid Grade 8-10).
"""

import os
import re
import sys
from pathlib import Path

def count_syllables(word):
    """Count syllables in a word."""
    word = word.lower()
    vowels = "aeiouy"
    syllable_count = 0
    prev_was_vowel = False

    for i, char in enumerate(word):
        is_vowel = char in vowels

        # If it's a vowel and previous wasn't a vowel, increment syllable count
        if is_vowel and not prev_was_vowel:
            syllable_count += 1

        prev_was_vowel = is_vowel

    # Handle silent 'e' at the end
    if word.endswith('e') and syllable_count > 1:
        syllable_count -= 1

    # Every word has at least one syllable
    return max(1, syllable_count)

def calculate_flesch_kincaid_grade(text):
    """Calculate Flesch-Kincaid Grade Level for the text."""
    # Remove code blocks and other non-text elements
    clean_text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # Code blocks
    clean_text = re.sub(r'`[^`]*`', '', clean_text)  # Inline code
    clean_text = re.sub(r'<.*?>', '', clean_text)  # HTML/XML tags

    # Split into sentences (simple approach)
    sentences = re.split(r'[.!?]+', clean_text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Split into words
    words = re.findall(r'\b[a-zA-Z]+\b', clean_text)

    # Count syllables
    syllable_count = sum(count_syllables(word) for word in words)

    # Calculate metrics
    num_sentences = len(sentences)
    num_words = len(words)
    num_syllables = syllable_count

    # Avoid division by zero
    if num_sentences == 0 or num_words == 0:
        return 0

    # Flesch-Kincaid Grade Level formula
    # 0.39 * (total words / total sentences) + 11.8 * (total syllables / total words) - 15.59
    avg_words_per_sentence = num_words / num_sentences
    avg_syllables_per_word = num_syllables / num_words

    grade_level = 0.39 * avg_words_per_sentence + 11.8 * avg_syllables_per_word - 15.59

    return grade_level

def check_readability_of_file(file_path):
    """Check readability of a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        grade_level = calculate_flesch_kincaid_grade(content)

        # Check if within acceptable range (Grade 8-10)
        is_acceptable = 8 <= grade_level <= 10

        return is_acceptable, grade_level

    except Exception as e:
        return False, f"Error reading file: {e}"

def verify_readability(project_dir):
    """Verify readability of all documentation files."""
    doc_files = []

    # Find all documentation files
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file.endswith(('.md', '.mdx')):
                doc_files.append(os.path.join(root, file))

    print(f"Found {len(doc_files)} documentation files to check for readability")

    results = {
        'acceptable': [],
        'too_complex': [],
        'errors': []
    }

    for file_path in doc_files:
        print(f"Checking readability of {file_path}...")

        try:
            is_acceptable, grade_level = check_readability_of_file(file_path)

            if isinstance(grade_level, str):  # Error occurred
                results['errors'].append((file_path, grade_level))
            elif is_acceptable:
                results['acceptable'].append((file_path, grade_level))
            else:
                results['too_complex'].append((file_path, grade_level))

        except Exception as e:
            results['errors'].append((file_path, f"Error processing: {e}"))

    return results

def main():
    project_dir = "/home/maliaraees/ai-and-humanoid-robotics-course/module2-digital-twin"

    print("Checking readability of documentation files...")
    print(f"Project directory: {project_dir}")
    print("Target: Flesch-Kincaid Grade Level 8-10 (Grade 8-10 reading level)")

    # Verify readability
    results = verify_readability(project_dir)

    print(f"\nReadability Results:")
    print(f"Acceptable files (Grade 8-10): {len(results['acceptable'])}")
    print(f"Too complex files (outside Grade 8-10): {len(results['too_complex'])}")
    print(f"Files with errors: {len(results['errors'])}")

    if results['too_complex']:
        print("\nFiles that are too complex (outside Grade 8-10):")
        for file_path, grade_level in results['too_complex']:
            if grade_level > 10:
                level_desc = "too difficult (college level)"
            else:
                level_desc = "too simple"
            print(f"  - {file_path}: Grade {grade_level:.1f} ({level_desc})")

    if results['errors']:
        print("\nFiles with errors:")
        for file_path, error in results['errors']:
            print(f"  - {file_path}: {error}")

    # Summary
    total_files = len(results['acceptable']) + len(results['too_complex']) + len(results['errors'])
    print(f"\nSummary: {len(results['acceptable'])}/{total_files} files meet readability standards (Grade 8-10).")

    if results['too_complex']:
        print("Some documentation files have readability levels outside the target Grade 8-10 range.")
        print("Consider simplifying complex sentences or using more common vocabulary.")
        return 1
    else:
        print("All documentation files meet readability standards (Grade 8-10)!")
        return 0

if __name__ == "__main__":
    sys.exit(main())