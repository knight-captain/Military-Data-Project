"""
Phase III orchestrator:
1. Categorize tables (branch/domain/type/platform/ignore)
2. Categorize columns (context-aware raw→super mapping). Super complex
3. Build the canonical a_master_equipment table
"""

import shutil
import sqlite3
from utils.update_path import update_path

# Submodules
from data.data_synthesis.classify_tables import classify_tables
from data.data_synthesis.classify_columns import classify_columns
from data.data_synthesis.recategorize_ontologically import recategorize_ontologically
from data.data_synthesis.build_master_equipment import build_master_equipment


def synthesize_equipment(db_path=None):
    """
    Phase III: Synthesis.
    Takes a CLEANED db, copies it to a SYNTHED db, runs synthesis,
    and returns the SYNTHED db path.
    """

    if db_path is None:
        raise ValueError("db_path must be provided.")

    # Build SYNTHED path & Copy CLEANED → SYNTHED, then connec to the new .db
    synthed_path = update_path(db_path)
    shutil.copy(db_path, synthed_path)
    conn = sqlite3.connect(synthed_path)

    print("\n[1/3] Classifying tables...")
    table_classes = classify_tables(conn) 
    
    print("\n[2/3] Classifying columns...")
    contextual_mapping, smart_col_list = classify_columns(conn, table_classes)
    # print(smart_col_mapping)

    # STEP 3: Re-categorize the tables using a_mapping_table's info
    #dict raw_col_map [(table_name,raw_col)] = super_col
    # but build master needed a dict of super_cols after all
    # raw_col_map = recategorize_ontologically(conn, contextual_mapping, smart_col_list)

    # STEP 3: Build master equipment table
    print("\n[3/3] Building master equipment table...")
    build_master_equipment(conn, contextual_mapping, smart_col_list)

    conn.close()
    print("\nEquipment synthesis pipeline completed successfully.")

    return synthed_path
