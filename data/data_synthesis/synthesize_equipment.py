"""
synthesize_equipment.py
-----------------------

Phase III orchestrator:
1. Categorize tables (branch/domain/type/platform/ignore)
2. Categorize columns (context-aware raw→super mapping)
3. Build the canonical a_master_equipment table
"""

import shutil
import sqlite3
from pathlib import Path

# Submodules
from data.data_synthesis.categorize_tables import categorize_all_tables
from data.data_synthesis.categorize_columns import build_contextual_column_mapping
from data.data_synthesis.build_master_equipment import build_master_equipment


def synthesize_equipment(db_path=None):
    """
    Phase III: Synthesis.
    Takes a CLEANED db, copies it to a SYNTHED db, runs synthesis,
    and returns the SYNTHED db path.
    """

    if db_path is None:
        raise ValueError("db_path must be provided.")

    # Build SYNTHED path & Copy CLEANED → SYNTHED
    synthed_path = Path(str(db_path).replace("-CLEANED.db", "-SYNTHED.db"))
    shutil.copy(db_path, synthed_path)

    # Open connection to SYNTHED DB
    conn = sqlite3.connect(synthed_path)

    print("\n[1/3] Categorizing tables...")
    categorize_all_tables(conn)

    print("\n[2/3] Categorizing columns...")
    contextual_mapping = build_contextual_column_mapping(conn)

    print("\n[3/3] Building master equipment table...")
    super_cols_path = Path("ontology/super_columns.txt")
    build_master_equipment(
        conn=conn,
        contextual_mapping=contextual_mapping,
        super_cols_path=super_cols_path
    )

    conn.close()
    print("\nEquipment synthesis pipeline completed successfully.")

    return synthed_path
