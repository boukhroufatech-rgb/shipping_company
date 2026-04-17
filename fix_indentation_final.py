#!/usr/bin/env python3
"""
Final indentation fixer using a clean, tested approach.
"""

from pathlib import Path


def fix_file(file_path):
    """Fix a single Python file's indentation."""
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    if not lines:
        return False, "Empty file"

    fixed = []
    in_class = False
    in_method = False
    in_nested = False
    i = 0

    # Skip module-level content before first class
    first_class_idx = None
    for idx, line in enumerate(lines):
        if line.strip().startswith('class '):
            first_class_idx = idx
            break

    # Process module-level
    if first_class_idx:
        for idx in range(first_class_idx):
            line = lines[idx]
            # Remove 4-space indent from module level
            if line.startswith('    ') and not line.startswith('        '):
                stripped = line.lstrip()
                if any(stripped.startswith(x) for x in ('"""', "'''", 'from ', 'import ', '#')):
                    fixed.append(stripped)
                else:
                    fixed.append(line)
            else:
                fixed.append(line)
        i = first_class_idx
    else:
        return False, "No class found"

    # Process class and methods
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()

        if not stripped.strip():
            fixed.append('\n')
            i += 1
            continue

        # Class
        if stripped.startswith('class '):
            in_class = True
            in_method = False
            in_nested = False
            fixed.append(stripped)
            i += 1
            continue

        if in_class:
            # Class docstring
            if (stripped.startswith('"""') or stripped.startswith("'''")) and not in_method:
                quote = '"""' if '"""' in stripped else "'''"
                fixed.append('    ' + stripped)
                if stripped.count(quote) < 2:
                    i += 1
                    while i < len(lines):
                        n = lines[i].lstrip()
                        fixed.append('    ' + n)
                        if quote in n:
                            break
                        i += 1
                i += 1
                continue

            # Def
            if stripped.startswith('def '):
                has_self = '(self' in stripped or ', self' in stripped

                if has_self:
                    in_method = True
                    in_nested = False
                    fixed.append('    ' + stripped)
                else:
                    in_nested = True
                    fixed.append('        ' + stripped)
                i += 1
                continue

            # Docstring in method
            if (stripped.startswith('"""') or stripped.startswith("'''")) and in_method:
                quote = '"""' if '"""' in stripped else "'''"
                indent = '            ' if in_nested else '        '
                fixed.append(indent + stripped)
                if stripped.count(quote) < 2:
                    i += 1
                    while i < len(lines):
                        n = lines[i].lstrip()
                        fixed.append(indent + n)
                        if quote in n:
                            break
                        i += 1
                i += 1
                continue

            # Content
            if in_nested:
                fixed.append('            ' + stripped)
            elif in_method:
                fixed.append('        ' + stripped)
            else:
                fixed.append('    ' + stripped)

            i += 1
            continue

        fixed.append(line)
        i += 1

    # Write
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed)
        return True, "Fixed"
    except Exception as e:
        return False, str(e)


def main():
    base = Path(r"D:\CLAUDE CODE\shipping_company\modules\settings\views")
    files = [
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
    print("Indentation Fixer - Final")
    print("=" * 70)
    print()

    for f in files:
        p = base / f
        if not p.exists():
            print(f"SKIP {f}: Not found")
            continue

        ok, msg = fix_file(p)
        status = "OK" if ok else "FAIL"
        print(f"{status:4} {f:25} {msg}")


if __name__ == "__main__":
    main()
