from utils.normalization import normalize_text

def recategorize_ontologically(conn, contextual_mapping, smart_col_list):
    """
    Convert dict-of-dicts column mapping into the flat
    (table_name, raw_col) -> super_col mapping required by
    build_master_equipment.

    Input:
        contextual_mapping = {
            table_name: {
                super_col: [raw_cols],
                ...
            }
        }
        smart_col_list = canonical list of super_cols 
    Output:
        raw_col_map = {(table_name, raw_col): super_col}
    """

    raw_col_map = {}

    for table_name, mapping in contextual_mapping.items():

        for super_col, raw_cols in mapping.items():

            if super_col == "__metadata__":
                raw_col_map[(table_name, "__metadata__")] = raw_cols
                continue

            # Skip unexpected super_cols DON"T REALLY NEED THIS ANY MORE!!! Turn into __metadata__ check!
            if super_col not in smart_col_list:
                print(f"WARNING: Unexpected super_col '{super_col}' in table {table_name}")
                continue

            # Clean raw_cols: remove None, empty strings, duplicates
            safe_raw_cols = [
                str(v).strip()
                for v in raw_cols
                if v is not None and str(v).strip() != ""
            ]

            # Skip empty lists
            if not safe_raw_cols:
                continue

            # Convert dict-of-dicts → flat mapping
            for raw_col in safe_raw_cols:
                raw_col_map[(table_name, raw_col)] = super_col

    return raw_col_map

