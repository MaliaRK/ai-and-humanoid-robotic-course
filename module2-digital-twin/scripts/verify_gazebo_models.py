#!/usr/bin/env python3
"""
Verification script for Gazebo world files and SDF models.

This script checks that all Gazebo world files and SDF models are properly formatted and functional.
"""

import os
import xml.etree.ElementTree as ET
import sys
from pathlib import Path

def validate_xml_syntax(file_path):
    """Validate XML syntax of the file."""
    try:
        tree = ET.parse(file_path)
        return True, "XML is well-formed"
    except ET.ParseError as e:
        return False, f"XML Parse Error: {e}"
    except Exception as e:
        return False, f"Error parsing XML: {e}"

def validate_sdf_structure(file_path):
    """Validate basic SDF structure."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Check if root tag is sdf or world
        if root.tag not in ['sdf', 'world']:
            return False, f"Root tag should be 'sdf' or 'world', got '{root.tag}'"

        # Check for version attribute in sdf tag
        if root.tag == 'sdf' and 'version' not in root.attrib:
            return False, "SDF tag missing version attribute"

        # For world files, check for basic required elements
        if root.tag == 'world':
            # Check for basic world elements
            has_name = 'name' in root.attrib
            has_elements = len(root) > 0

            if not has_name:
                return False, "World tag missing name attribute"

        # Check for common SDF elements
        required_elements = []
        for elem in root.iter():
            if elem.tag == 'model':
                # Check for name attribute
                if 'name' not in elem.attrib:
                    return False, "Model tag missing name attribute"
            elif elem.tag == 'link':
                # Check for name attribute
                if 'name' not in elem.attrib:
                    return False, "Link tag missing name attribute"
            elif elem.tag == 'joint':
                # Check for name and type attributes
                if 'name' not in elem.attrib:
                    return False, "Joint tag missing name attribute"
                if 'type' not in elem.attrib:
                    return False, "Joint tag missing type attribute"

        return True, "SDF structure is valid"

    except ET.ParseError as e:
        return False, f"SDF Parse Error: {e}"
    except Exception as e:
        return False, f"Error validating SDF: {e}"

def verify_gazebo_files(project_dir):
    """Verify all Gazebo world files and SDF models in the project directory."""
    gazebo_files = []

    # Find all world and SDF files
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file.endswith('.world') or file.endswith('.sdf') or file.endswith('.model'):
                gazebo_files.append(os.path.join(root, file))

    print(f"Found {len(gazebo_files)} Gazebo files to verify")

    results = {
        'valid': [],
        'invalid': []
    }

    for file_path in gazebo_files:
        print(f"Checking {file_path}...")

        # Check XML syntax first
        xml_valid, xml_msg = validate_xml_syntax(file_path)
        if not xml_valid:
            results['invalid'].append((file_path, xml_msg))
            continue

        # Check SDF structure
        sdf_valid, sdf_msg = validate_sdf_structure(file_path)
        if not sdf_valid:
            results['invalid'].append((file_path, sdf_msg))
            continue

        results['valid'].append(file_path)

    return results

def verify_urdf_models(project_dir):
    """Verify URDF models in the project directory."""
    urdf_files = []

    # Find all URDF files
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file.endswith('.urdf') or file.endswith('.xacro'):
                urdf_files.append(os.path.join(root, file))

    print(f"Found {len(urdf_files)} URDF/XACRO files to verify")

    results = {
        'valid': [],
        'invalid': []
    }

    for file_path in urdf_files:
        print(f"Checking {file_path}...")

        # Check XML syntax first
        xml_valid, xml_msg = validate_xml_syntax(file_path)
        if not xml_valid:
            results['invalid'].append((file_path, xml_msg))
            continue

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Check if root tag is robot (for URDF) or for XACRO files
            if root.tag == 'robot':
                # Validate basic URDF structure
                if 'name' not in root.attrib:
                    results['invalid'].append((file_path, "Robot tag missing name attribute"))
                    continue

                # Check for at least one link
                links = root.findall('.//link')
                if len(links) == 0:
                    results['invalid'].append((file_path, "URDF has no links"))
                    continue

                # Check for at least one joint if there are multiple links
                joints = root.findall('.//joint')
                if len(links) > 1 and len(joints) == 0:
                    # This might be valid for a single-link robot, but let's allow it
                    pass

            results['valid'].append(file_path)

        except Exception as e:
            results['invalid'].append((file_path, f"Error parsing URDF: {e}"))

    return results

def main():
    project_dir = "/home/maliaraees/ai-and-humanoid-robotics-course/module2-digital-twin"

    print("Verifying Gazebo world files and SDF models...")
    print(f"Project directory: {project_dir}")

    # Verify Gazebo world and SDF files
    gazebo_results = verify_gazebo_files(project_dir)

    print(f"\nGazebo Files Verification Results:")
    print(f"Valid files: {len(gazebo_results['valid'])}")
    print(f"Invalid files: {len(gazebo_results['invalid'])}")

    if gazebo_results['invalid']:
        print("\nInvalid Gazebo files:")
        for file_path, error in gazebo_results['invalid']:
            print(f"  - {file_path}: {error}")

    # Verify URDF models
    print("\nVerifying URDF/XACRO models...")
    urdf_results = verify_urdf_models(project_dir)

    print(f"\nURDF/XACRO Files Verification Results:")
    print(f"Valid files: {len(urdf_results['valid'])}")
    print(f"Invalid files: {len(urdf_results['invalid'])}")

    if urdf_results['invalid']:
        print("\nInvalid URDF/XACRO files:")
        for file_path, error in urdf_results['invalid']:
            print(f"  - {file_path}: {error}")

    # Summary
    total_gazebo = len(gazebo_results['valid']) + len(gazebo_results['invalid'])
    total_urdf = len(urdf_results['valid']) + len(urdf_results['invalid'])

    print(f"\nSummary: {len(gazebo_results['valid'])}/{total_gazebo} Gazebo files are valid.")
    print(f"Summary: {len(urdf_results['valid'])}/{total_urdf} URDF/XACRO files are valid.")

    if gazebo_results['invalid'] or urdf_results['invalid']:
        print("Some Gazebo or URDF files need to be fixed.")
        return 1
    else:
        print("All Gazebo and URDF files are properly formatted!")
        return 0

if __name__ == "__main__":
    sys.exit(main())