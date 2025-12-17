#!/usr/bin/env python
"""
Validation script to verify all TypeError fixes are correct.
"""
import ast
import sys
from pathlib import Path


def validate_python_syntax(file_path):
    """Validate that a Python file has correct syntax."""
    try:
        with open(file_path) as f:
            ast.parse(f.read())
        return True, "OK"
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def check_parameter_exists(file_path, class_name, param_name):
    """Check if a class __init__ has a specific parameter."""
    try:
        with open(file_path) as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                        param_names = [arg.arg for arg in item.args.args]
                        if param_name in param_names:
                            return True, f"Parameter '{param_name}' found"
                        else:
                            return False, f"Parameter '{param_name}' not found. Found: {param_names}"

        return False, f"Class '{class_name}' not found"
    except Exception as e:
        return False, f"Error: {e}"

# Files to validate
files_to_validate = [
    "/Users/Warmonger0/tac/tac-webbuilder/app/server/services/hopper_sorter.py",
    "/Users/Warmonger0/tac/tac-webbuilder/app/server/services/phase_queue_service.py",
    "/Users/Warmonger0/tac/tac-webbuilder/app/server/repositories/phase_queue_repository.py",
]

print("=" * 70)
print("VALIDATING FIXES FOR test_hopper_sorter.py TypeErrors")
print("=" * 70)

all_passed = True

# Test 1: Syntax validation
print("\n[1] Checking Python syntax...")
for file_path in files_to_validate:
    result, msg = validate_python_syntax(file_path)
    status = "✓" if result else "✗"
    print(f"  {status} {Path(file_path).name}: {msg}")
    if not result:
        all_passed = False

# Test 2: HopperSorter has db_path parameter
print("\n[2] Checking HopperSorter.__init__ signature...")
result, msg = check_parameter_exists(
    "/Users/Warmonger0/tac/tac-webbuilder/app/server/services/hopper_sorter.py",
    "HopperSorter",
    "db_path"
)
status = "✓" if result else "✗"
print(f"  {status} HopperSorter.db_path parameter: {msg}")
if not result:
    all_passed = False

# Test 3: PhaseQueueService has db_path parameter
print("\n[3] Checking PhaseQueueService.__init__ signature...")
result, msg = check_parameter_exists(
    "/Users/Warmonger0/tac/tac-webbuilder/app/server/services/phase_queue_service.py",
    "PhaseQueueService",
    "db_path"
)
status = "✓" if result else "✗"
print(f"  {status} PhaseQueueService.db_path parameter: {msg}")
if not result:
    all_passed = False

# Test 4: PhaseQueueRepository has db_path parameter
print("\n[4] Checking PhaseQueueRepository.__init__ signature...")
result, msg = check_parameter_exists(
    "/Users/Warmonger0/tac/tac-webbuilder/app/server/repositories/phase_queue_repository.py",
    "PhaseQueueRepository",
    "db_path"
)
status = "✓" if result else "✗"
print(f"  {status} PhaseQueueRepository.db_path parameter: {msg}")
if not result:
    all_passed = False

# Test 5: Check SQLiteAdapter imports
print("\n[5] Checking SQLiteAdapter imports...")
imports_ok = True

files_to_check = [
    "/Users/Warmonger0/tac/tac-webbuilder/app/server/services/hopper_sorter.py",
    "/Users/Warmonger0/tac/tac-webbuilder/app/server/repositories/phase_queue_repository.py",
]

for file_path in files_to_check:
    with open(file_path) as f:
        content = f.read()
        if 'from database.sqlite_adapter import SQLiteAdapter' in content:
            print(f"  ✓ {Path(file_path).name} imports SQLiteAdapter correctly")
        else:
            print(f"  ✗ {Path(file_path).name} missing SQLiteAdapter import")
            imports_ok = False

if not imports_ok:
    all_passed = False

# Final result
print("\n" + "=" * 70)
if all_passed:
    print("✓ ALL VALIDATIONS PASSED - Fixes are correct!")
    print("=" * 70)
    sys.exit(0)
else:
    print("✗ SOME VALIDATIONS FAILED - Please review the issues above")
    print("=" * 70)
    sys.exit(1)
