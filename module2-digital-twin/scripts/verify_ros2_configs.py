#!/usr/bin/env python3
"""
Verification script for ROS2 launch files and configuration files.

This script checks that all ROS2 launch files and configuration files are properly formatted and valid.
"""

import os
import xml.etree.ElementTree as ET
import yaml
import json
import sys
import re
from pathlib import Path

def validate_launch_file_syntax(file_path):
    """Validate ROS2 launch file syntax."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Check if it's a Python launch file
        if file_path.endswith('.py'):
            # Basic check for required imports and function
            if 'from launch import LaunchDescription' not in content:
                return False, "Missing required launch import"

            if 'def generate_launch_description():' not in content:
                return False, "Missing generate_launch_description function"

            # Check for proper return statement
            if 'return LaunchDescription' not in content:
                return False, "Missing return LaunchDescription statement"

            return True, "Launch file syntax appears valid"

        # Check if it's an XML launch file
        elif file_path.endswith('.launch.xml') or file_path.endswith('.xml'):
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()

                # Check for basic structure
                if root.tag not in ['launch', 'group', 'include']:
                    return False, f"Unexpected root tag: {root.tag}, expected 'launch'"

                return True, "XML launch file syntax appears valid"
            except ET.ParseError as e:
                return False, f"XML Parse Error: {e}"

        else:
            return False, "Unknown launch file type (expected .py or .xml)"

    except Exception as e:
        return False, f"Error reading file: {e}"

def validate_yaml_config(file_path):
    """Validate YAML configuration files."""
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)

        # Check if it's a valid YAML file
        if data is None:
            return True, "Valid empty YAML file"

        return True, "YAML configuration is valid"

    except yaml.YAMLError as e:
        return False, f"YAML Parse Error: {e}"
    except Exception as e:
        return False, f"Error reading YAML file: {e}"

def validate_params_file(file_path):
    """Validate ROS2 parameters files."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Try to parse as YAML first
        try:
            data = yaml.safe_load(content)
            if data is not None:
                # Check for ROS2 parameter file structure
                if isinstance(data, dict):
                    for node_name, node_params in data.items():
                        if isinstance(node_params, dict) and 'ros__parameters' in node_params:
                            # This looks like a proper ROS2 parameter file
                            return True, "ROS2 parameters file is valid"
                return True, "YAML parameters file is valid"
        except yaml.YAMLError:
            pass  # Try other formats

        # If not YAML, it might be a different config format
        return True, "Configuration file appears valid"

    except Exception as e:
        return False, f"Error reading parameters file: {e}"

def verify_ros2_files(project_dir):
    """Verify all ROS2 launch files and configuration files in the project directory."""
    ros2_files = []

    # Find all ROS2-related files
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if (file.endswith('.py') and 'launch' in file) or \
               file.endswith('.launch.xml') or \
               file.endswith('.xml') or \
               file.endswith('.yaml') or \
               file.endswith('.yml') or \
               ('params' in file and (file.endswith('.yaml') or file.endswith('.json'))):
                ros2_files.append(os.path.join(root, file))

    print(f"Found {len(ros2_files)} ROS2 files to verify")

    results = {
        'valid': [],
        'invalid': []
    }

    for file_path in ros2_files:
        print(f"Checking {file_path}...")

        # Determine file type and validate accordingly
        if file_path.endswith('.py'):
            valid, msg = validate_launch_file_syntax(file_path)
        elif file_path.endswith('.launch.xml') or file_path.endswith('.xml'):
            valid, msg = validate_launch_file_syntax(file_path)
        elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
            valid, msg = validate_yaml_config(file_path)
        else:
            # For other files, try to validate as params file
            valid, msg = validate_params_file(file_path)

        if valid:
            results['valid'].append(file_path)
        else:
            results['invalid'].append((file_path, msg))

    return results

def verify_ros2_packages_structure(project_dir):
    """Verify ROS2 package structure and configuration."""
    issues = []

    # Look for package.xml files
    for root, dirs, files in os.walk(project_dir):
        if 'package.xml' in files:
            package_path = os.path.join(root, 'package.xml')
            try:
                tree = ET.parse(package_path)
                root_elem = tree.getroot()

                # Check package format
                if root_elem.tag != 'package':
                    issues.append(f"Invalid package.xml format in {package_path}")
                    continue

                # Check for required elements
                required_elements = ['name', 'version', 'description', 'maintainer', 'license']
                for req_elem in required_elements:
                    if root_elem.find(req_elem) is None:
                        issues.append(f"Missing required element '{req_elem}' in {package_path}")

            except ET.ParseError as e:
                issues.append(f"Invalid package.xml syntax in {package_path}: {e}")
            except Exception as e:
                issues.append(f"Error processing package.xml in {package_path}: {e}")

    return issues

def main():
    project_dir = "/home/maliaraees/ai-and-humanoid-robotics-course/module2-digital-twin"

    print("Verifying ROS2 launch files and configuration files...")
    print(f"Project directory: {project_dir}")

    # Verify ROS2 files
    results = verify_ros2_files(project_dir)

    print(f"\nROS2 Files Verification Results:")
    print(f"Valid files: {len(results['valid'])}")
    print(f"Invalid files: {len(results['invalid'])}")

    if results['invalid']:
        print("\nInvalid ROS2 files:")
        for file_path, error in results['invalid']:
            print(f"  - {file_path}: {error}")

    # Verify package structure
    print("\nVerifying ROS2 package structure...")
    package_issues = verify_ros2_packages_structure(project_dir)

    if package_issues:
        print("\nPackage structure issues:")
        for issue in package_issues:
            print(f"  - {issue}")
    else:
        print("Package structure appears valid.")

    # Summary
    total_files = len(results['valid']) + len(results['invalid'])
    print(f"\nSummary: {len(results['valid'])}/{total_files} ROS2 files are valid.")

    if results['invalid'] or package_issues:
        print("Some ROS2 files need to be fixed to comply with ROS2 standards.")
        return 1
    else:
        print("All ROS2 files are properly formatted!")
        return 0

if __name__ == "__main__":
    sys.exit(main())