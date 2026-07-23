# utils/paths.py

from pathlib import Path

def update_path(db_path: Path | str) -> Path:
    """
    Advance a database file to the next pipeline stage.

    Stages:
        -RAW.db      → -CLEANED.db
        -CLEANED.db  → -SYNTHED.db
        -SYNTHED.db  → (reserved for future phases)

    Parameters
    ----------
    db_path : Path or str
        The current database path.

    Returns
    -------
    Path
        The updated path for the next pipeline stage.

    Raises
    ------
    ValueError
        If the filename does not match a known stage.
    """

    db_path = Path(db_path)
    name = db_path.name

    if name.endswith("-REFINED.db"):
        # Placeholder for future phases (Phase IV, V, etc.)
        raise ValueError("No next stage defined after -REFINED.db")

    elif name.endswith("-SYNTHED.db"):
        return db_path.with_name(name.replace("-SYNTHED.db", "-REFINED.db"))

    elif name.endswith("-CLEANED.db"):
        return db_path.with_name(name.replace("-CLEANED.db", "-SYNTHED.db"))

    elif name.endswith("-RAW.db"):
        return db_path.with_name(name.replace("-RAW.db", "-CLEANED.db"))

    else:
        raise ValueError(f"Unrecognized DB stage in filename: {name}")
