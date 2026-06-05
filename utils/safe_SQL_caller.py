def q(identifier: str) -> str:
    """Safely quote a SQLite identifier."""
    escaped = identifier.replace('"', '""')
    return f'"{escaped}"'

def ql(value: str) -> str:
    """Safely quote a SQLite string literal."""
    escaped = value.replace("'", "''")
    return f"'{escaped}'"
