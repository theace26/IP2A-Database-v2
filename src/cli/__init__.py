"""
IP2A Database CLI.

Command-line interface for database management operations.
"""

import click

from src.cli.migrations import migrate


@click.group()
def cli():
    """IP2A Database CLI - manage migrations and database operations."""
    pass


# Register command groups
cli.add_command(migrate)


if __name__ == "__main__":
    cli()
