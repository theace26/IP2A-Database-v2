import subprocess
import sys

STEPS = [
    ["python", "src/scripts/validate_imports.py"],
    ["python", "src/scripts/validate_alembic_drift.py"],
]

for step in STEPS:
    print(f"\n▶ Running: {' '.join(step)}")
    result = subprocess.run(step)
    if result.returncode != 0:
        sys.exit(result.returncode)

print("\n✅ Preflight checks passed")
