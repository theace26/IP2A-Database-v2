"""
Migration CLI commands for ip2adb.
"""

import click
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


@click.group()
def migrate():
    """Migration management commands."""
    pass


@migrate.command("new")
@click.argument("description")
@click.option("--no-autogenerate", is_flag=True, help="Don't autogenerate from models")
def migrate_new(description: str, no_autogenerate: bool):
    """
    Create a new timestamped migration.

    Example:
        ip2adb migrate new "add user preferences"
    """
    script = PROJECT_ROOT / "scripts" / "alembic_wrapper.py"

    cmd = [sys.executable, str(script), "new", description]
    if no_autogenerate:
        cmd.append("--no-autogenerate")

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    sys.exit(result.returncode)


@migrate.command("validate")
def migrate_validate():
    """Validate migration naming conventions."""
    script = PROJECT_ROOT / "scripts" / "alembic_wrapper.py"

    result = subprocess.run([sys.executable, str(script), "validate"], cwd=PROJECT_ROOT)
    sys.exit(result.returncode)


@migrate.command("list")
def migrate_list():
    """List all migrations with timestamps."""
    script = PROJECT_ROOT / "scripts" / "alembic_wrapper.py"

    result = subprocess.run([sys.executable, str(script), "list"], cwd=PROJECT_ROOT)
    sys.exit(result.returncode)


@migrate.command("upgrade")
@click.argument("revision", default="head")
def migrate_upgrade(revision: str):
    """
    Upgrade database to a revision.

    Example:
        ip2adb migrate upgrade head
        ip2adb migrate upgrade +1
    """
    result = subprocess.run(["alembic", "upgrade", revision], cwd=PROJECT_ROOT)
    sys.exit(result.returncode)


@migrate.command("downgrade")
@click.argument("revision")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def migrate_downgrade(revision: str, yes: bool):
    """
    Downgrade database to a revision.

    Example:
        ip2adb migrate downgrade -1
        ip2adb migrate downgrade base
    """
    if not yes:
        click.confirm(
            f"Downgrade to '{revision}'? This may cause data loss.", abort=True
        )

    result = subprocess.run(["alembic", "downgrade", revision], cwd=PROJECT_ROOT)
    sys.exit(result.returncode)


@migrate.command("current")
def migrate_current():
    """Show current database revision."""
    result = subprocess.run(["alembic", "current"], cwd=PROJECT_ROOT)
    sys.exit(result.returncode)


@migrate.command("history")
@click.option("--verbose", "-v", is_flag=True, help="Show verbose output")
def migrate_history(verbose: bool):
    """Show migration history."""
    cmd = ["alembic", "history"]
    if verbose:
        cmd.append("-v")

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    sys.exit(result.returncode)
