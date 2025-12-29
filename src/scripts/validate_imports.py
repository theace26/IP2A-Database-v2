"""
Fail fast if the import graph is broken.
This should run before app startup, alembic, and seed.
"""

import sys
import traceback
from pathlib import Path

# -------------------------------------------------------------------
# Ensure project root is importable no matter how this script is run
# -------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# -------------------------------------------------------------------
# Explicit import targets (order matters)
# -------------------------------------------------------------------
MODEL_MODULES = [
    "src.models",
    "src.models.location",
    "src.models.student",
    "src.models.jatc_application",
]

SERVICE_MODULES = [
    "src.services.cohort_service",
    "src.services.instructor_service",
]

MODULES_TO_VALIDATE = MODEL_MODULES + SERVICE_MODULES


# -------------------------------------------------------------------
# Validation
# -------------------------------------------------------------------
def main() -> None:
    failures: list[tuple[str, Exception, str]] = []

    for module in MODULES_TO_VALIDATE:
        try:
            __import__(module)
        except Exception as e:
            failures.append((module, e, traceback.format_exc()))

    if failures:
        print("\n❌ IMPORT VALIDATION FAILED\n")
        for module, error, tb in failures:
            print(f"Module: {module}")
            print(error)
            print(tb)
            print("-" * 80)
        sys.exit(1)

    print("✅ Import validation passed")


if __name__ == "__main__":
    main()
