#!/usr/bin/env python3
"""
Script to fix indentation issues in Python files.
"""

from pathlib import Path


def fix_indentation_simple(file_path):
    """
    Fix indentation by detecting the indentation level of each line
    and applying correct indentation based on context.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        return False, "File is empty"

    fixed_lines = []

    # Phase 1: Remove 4-space indent from module-level content (before first class)
    i = 0
    # Find first class
    first_class = None
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            if stripped.startswith('class '):
                first_class = idx
                break

    # Process module-level section
    while i < len(lines) and (first_class is None or i < first_class):
        line = lines[i]

        # Remove 4-space indentation from module level
        if line.startswith('    ') and not line.startswith('        '):
            stripped = line.lstrip()
            if (stripped.startswith('"""') or stripped.startswith("'''") or
                stripped.startswith('from ') or stripped.startswith('import ') or
                stripped.startswith('#') or stripped == ''):
                fixed_lines.append(stripped)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)

        i += 1

    # Phase 2: Manual fixing of class/method structure
    class_started = False
    in_method_body = False
    in_nested_func = False

    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        leading = len(line) - len(stripped)

        # Empty lines
        if not stripped:
            fixed_lines.append('\n')
            i += 1
            continue

        # Class definition
        if stripped.startswith('class '):
            class_started = True
            in_method_body = False
            in_nested_func = False
            fixed_lines.append(stripped)  # Column 0
            i += 1
            continue

        if class_started:
            # Class docstring (right after class definition)
            if (stripped.startswith('"""') or stripped.startswith("'''")) and not in_method_body and not in_nested_func:
                quote = '"""' if '"""' in stripped else "'''"
                fixed_lines.append('    ' + stripped)  # 4 spaces

                # Multi-line?
                if stripped.count(quote) < 2:
                    i += 1
                    while i < len(lines):
                        next_line = lines[i]
                        next_stripped = next_line.lstrip()
                        fixed_lines.append('    ' + next_stripped)  # 4 spaces
                        if quote in next_stripped:
                            break
                        i += 1
                i += 1
                continue

            # Any def statement
            if stripped.startswith('def '):
                is_class_method = '(self' in stripped or ', self' in stripped

                if is_class_method:
                    # Class method - reset nested func flag
                    in_method_body = True
                    in_nested_func = False
                    fixed_lines.append('    ' + stripped)  # 4 spaces
                else:
                    # Nested function
                    in_nested_func = True
                    fixed_lines.append('        ' + stripped)  # 8 spaces

                i += 1
                continue

            # Docstring inside method/nested function
            if (stripped.startswith('"""') or stripped.startswith("'''")) and (in_method_body or in_nested_func):
                quote = '"""' if '"""' in stripped else "'''"
                indent_level = '            ' if in_nested_func else '        '
                fixed_lines.append(indent_level + stripped)

                if stripped.count(quote) < 2:
                    i += 1
                    while i < len(lines):
                        next_line = lines[i]
                        next_stripped = next_line.lstrip()
                        fixed_lines.append(indent_level + next_stripped)
                        if quote in next_stripped:
                            break
                        i += 1
                i += 1
                continue

            # Content in nested function
            if in_nested_func:
                fixed_lines.append('            ' + stripped)  # 12 spaces
                i += 1
                continue

            # Content in method body
            if in_method_body:
                fixed_lines.append('        ' + stripped)  # 8 spaces
                i += 1
                continue

            # Class-level content
            fixed_lines.append('    ' + stripped)  # 4 spaces
            i += 1
            continue

        # Not in class
        fixed_lines.append(line)
        i += 1

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)

    return True, "Fixed"


def main():
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
    print("Python Indentation Fixer v2")
    print("=" * 70)
    print()

    for filename in files_to_fix:
        file_path = base_dir / filename
        if not file_path.exists():
            print(f"SKIP: {filename} - Not found")
            continue

        success, msg = fix_indentation_simple(file_path)
        status = "OK" if success else "ERROR"
        print(f"{status:6} {filename:25} - {msg}")


if __name__ == "__main__":
    main()
