import re

def q(identifier: str) -> str:
    """Safely quote a SQLite identifier."""
    escaped = identifier.replace('"', '""')
    return f'"{escaped}"'

def ql(value: str) -> str:
    """Safely quote a SQLite string literal."""
    escaped = value.replace("'", "''")
    return f"'{escaped}'"

def clean_name(name: str) -> str:
    """Convert a country/page name into a safe SQLite table name."""
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")