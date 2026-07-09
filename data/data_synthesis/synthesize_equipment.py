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
from data.data_synthesis.categorize_tables import categorize_all_tables
from data.data_synthesis.categorize_columns import categorize_columns
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

    # STEP 1: Categorize tables via regexed table_name (which came from the <h2/3/4>'s)
    #dict table_categories[table_name] = classification
    # now with grouping and hierarchy!
    print("\n[1/4] Categorizing tables...")
    table_categories = categorize_all_tables(conn) 

    # STEP 2: Categorize columns
    #dict super_col_map [raw_cols] = super_cols
    print("\n[2/4] Categorizing columns...")
    super_col_map = categorize_columns(conn)

    # STEP 3: Re-categorize the tables using a_mapping_table's info
    #dict contextual_mapping [(table_name,raw_col)] = super_col
    #list new_super_cols [super_col1,super_col2...]
    print("\n[3/4] Recategorizing tables...")
    contextual_mapping, new_super_cols = recategorize_ontologically(conn, table_categories, super_col_map)

    # STEP 4: Build master equipment table
    print("\n[4/4] Building master equipment table...")
    build_master_equipment(conn, contextual_mapping, new_super_cols)

    conn.close()
    print("\nEquipment synthesis pipeline completed successfully.")

    return synthed_path
