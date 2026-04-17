#!/usr/bin/env python3
"""
Script to fix indentation issues in Python files.
Removes incorrect 4-space indentation from module-level docstrings and imports,
and ensures proper indentation for class and method definitions.
"""

import os
import re
from pathlib import Path


def fix_indentation(file_path):
    """
    Fix indentation in a Python file.
    Returns (success: bool, message: str)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        return False, "File is empty"

    fixed_lines = []
    in_class = False
    in_method_body = False
    in_nested_function = False

    i = 0

    # Phase 1: Fix module-level content (before first class)
    while i < len(lines):
        line = lines[i]

        # Check if we've reached class definition
        if line.strip().startswith('class '):
            break

        # Remove 4-space indentation from module-level content
        if line.startswith('    ') and not line.startswith('        '):
            stripped = line.lstrip()
            # Only remove indentation for docstrings, imports, and comments
            if (stripped.startswith('"""') or
                stripped.startswith("'''") or
                stripped.startswith('from ') or
                stripped.startswith('import ') or
                stripped.startswith('#') or
                stripped == ''):
                fixed_lines.append(stripped)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)

        i += 1

    # Phase 2: Process class and method definitions
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        leading_spaces = len(line) - len(stripped)

        # Empty lines
        if not stripped:
            fixed_lines.append('\n')
            i += 1
            continue

        # Class definition - should be at column 0
        if stripped.startswith('class '):
            in_class = True
            in_method_body = False
            in_nested_function = False
            fixed_lines.append(stripped)
            i += 1
            continue

        if in_class:
            # Docstring for class - indent 4 spaces (must be right after class def)
            if (stripped.startswith('"""') or stripped.startswith("'''")) and not in_method_body and not in_nested_function:
                quote = '"""' if '"""' in stripped else "'''"
                fixed_lines.append('    ' + stripped)

                # Handle multi-line docstring
                if stripped.count(quote) < 2:
                    i += 1
                    while i < len(lines):
                        next_line = lines[i]
                        next_stripped = next_line.lstrip()
                        fixed_lines.append('    ' + next_stripped)
                        if quote in next_stripped:
                            break
                        i += 1

                i += 1
                continue

            # Method or nested function definition
            if stripped.startswith('def '):
                # Determine if this is a class method or nested function
                # Class methods have 'self' as first parameter
                # Nested functions do not have 'self'
                is_class_method = '(self' in stripped or ', self' in stripped

                if is_class_method:
                    # This is a class method - always 4 spaces
                    # Reset nested function flag
                    in_nested_function = False
                    in_method_body = True
                    fixed_lines.append('    ' + stripped)
                else:
                    # This is a nested function - 8 spaces (inside method body)
                    in_nested_function = True
                    fixed_lines.append('        ' + stripped)

                i += 1
                continue

            # Handle docstrings inside methods/nested functions
            if (stripped.startswith('"""') or stripped.startswith("'''")) and (in_method_body or in_nested_function):
                quote = '"""' if '"""' in stripped else "'''"
                if in_nested_function:
                    # Docstring in nested function - 12 spaces
                    fixed_lines.append('            ' + stripped)
                else:
                    # Docstring in method - 8 spaces
                    fixed_lines.append('        ' + stripped)

                # Handle multi-line docstring
                if stripped.count(quote) < 2:
                    i += 1
                    while i < len(lines):
                        next_line = lines[i]
                        next_stripped = next_line.lstrip()
                        if in_nested_function:
                            fixed_lines.append('            ' + next_stripped)
                        else:
                            fixed_lines.append('        ' + next_stripped)
                        if quote in next_stripped:
                            break
                        i += 1

                i += 1
                continue

            # Handle content inside class
            if in_nested_function:
                # Inside a nested function - content should be 12 spaces
                fixed_lines.append('            ' + stripped)
                i += 1
                continue
            elif in_method_body:
                # Inside a method body
                # Content should be 8 spaces
                fixed_lines.append('        ' + stripped)
                i += 1
                continue
            else:
                # Class-level content (not in a method) - should be 4 spaces
                fixed_lines.append('    ' + stripped)
                i += 1
                continue
        else:
            # Not in class, keep as is
            fixed_lines.append(line)
            i += 1

    # Write back to file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
        return True, "Successfully fixed"
    except Exception as e:
        return False, f"Error writing file: {str(e)}"


def main():
    """Main function to process all files."""
    base_dir = Path(r"D:\CLAUDE CODE\shipping_company\modules\settings\views")

    files_to_fix = [
        "__init__.py",
        "institution_tab.py",
        "rules_tab.py",
        "interface_tab.py",
        "backup_tab.py",
        "print_tab.py",
        "database_tab.py",
        "theme_tab.py",
    ]

    print("=" * 70)
    print("Python Indentation Fixer")
    print("=" * 70)
    print()

    results = []
    for filename in files_to_fix:
        file_path = base_dir / filename

        if not file_path.exists():
            results.append((filename, False, "File not found"))
            print(f"SKIP: {filename} - File not found")
            continue

        success, message = fix_indentation(file_path)
        results.append((filename, success, message))
        status = "OK" if success else "ERROR"
        print(f"{status:6} {filename:25} - {message}")

    print()
    print("=" * 70)
    print("Summary:")
    print("=" * 70)

    fixed_count = sum(1 for _, success, _ in results if success)
    failed_count = sum(1 for _, success, _ in results if not success)

    print(f"Fixed:  {fixed_count}")
    print(f"Failed: {failed_count}")
    print(f"Total:  {len(results)}")

    if fixed_count > 0:
        print()
        print("Fixed files:")
        for filename, success, _ in results:
            if success:
                print(f"  - {filename}")

    if failed_count > 0:
        print()
        print("Failed files:")
        for filename, success, message in results:
            if not success:
                print(f"  - {filename}: {message}")


if __name__ == "__main__":
    main()
