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
from data.data_classification.classify_tables import classify_tables
from data.data_classification.classify_columns import classify_columns
from data.data_classification.build_master_equipment import build_master_equipment


def classify_all_equipment(db_path=None):
    """
    Phase III: Classification.
    Takes a CLEANED db, copies it to a CLASSIFIED db, classifies,
    and returns the CLASSIFIED db path.
    """

    if db_path is None:
        raise ValueError("db_path must be provided.")

    # Build CLASSIFIED path & Copy CLEANED → CLASSIFIED, then connec to the new .db
    classified_path = update_path(db_path)
    shutil.copy(db_path, classified_path)
    conn = sqlite3.connect(classified_path)

    print("\n[1/3] Classifying tables...")
    table_classes = classify_tables(conn) 
    
    print("\n[2/3] Classifying columns...")
    contextual_mapping, smart_col_list = classify_columns(conn, table_classes)
    # print(smart_col_mapping)

    # STEP 3: Build master equipment table
    print("\n[3/3] Building master equipment table...")
    build_master_equipment(conn, contextual_mapping, smart_col_list)

    conn.close()
    print("\nEquipment classification pipeline completed successfully.")

    return classified_path
