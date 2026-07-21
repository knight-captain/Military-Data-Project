"""
Builds a context-aware column mapping for every raw table.
Input:
    conn : sqlite3.Connection
Reads:
    ontology/column_mapping.csv   (raw_col → super_col)
Outputs:
    super_cols : sorted list of unique super columns
"""
from pathlib import Path
from utils import read_csv
from utils.normalization import normalize_text

def categorize_columns(conn):
    """
    Step 2: Load raw→super mapping from column_mapping.csv.
    """

    raw_map = read_csv.to_dict(
        Path(__file__).resolve().parents[2]
        / "ontology"
        / "column_mapping.csv"
    )

    super_col_map = {}
    for raw, sup in raw_map.items():
        raw = normalize_text(raw)
        sup = normalize_text(sup)
        if raw:
            super_col_map[raw] = sup

    return super_col_map
