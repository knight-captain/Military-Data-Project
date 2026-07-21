import re
from utils.normalization import normalize_text
from utils.safe_SQL_caller import q

#TODO: TEMP! (not necessary, but useful) IDK: maybe I'll just have build_master_equip work off of this?
def build_mapping_table(conn, table_classes, contextual_mapping, super_cols_list):
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS a_mapping_table")

    # Build dynamic CREATE TABLE with one column per super_col
    cols_sql = ",\n".join([f'"{col}" TEXT' for col in super_cols_list])

    cursor.execute(f"""
        CREATE TABLE a_mapping_table (
            table_name TEXT,
            equipment_class TEXT,
            other_classes TEXT,
            confidence REAL,
            {cols_sql}
        )
    """)

    # Iterate over all tables in table_classes
    for table_name, class_info in table_classes.items():

        # Skip meta tables
        if table_name.startswith("a_"):
            continue

        # Extract classification info
        equipment_class = class_info.get("equipment_class")
        other_classes = ", ".join(class_info.get("other_classes", []))
        confidence = class_info.get("confidence")

        # Extract contextual mapping for this table
        mapping_for_table = contextual_mapping.get(table_name, {})

        # Convert lists to comma-separated strings
        row_values = []
        for col in super_cols_list:
            values = mapping_for_table.get(col, [])
            if not values:
                row_values.append(None)
            else:
                # Filter out None and convert everything to string
                clean_values = [str(v) for v in values if v is not None]
                row_values.append(", ".join(clean_values) if clean_values else None)


        cursor.execute(
            f"""
            INSERT INTO a_mapping_table
            (table_name, equipment_class, other_classes, confidence,
             {", ".join([f'"{c}"' for c in super_cols_list])})
            VALUES (?, ?, ?, ?, {", ".join(["?"] * len(super_cols_list))})
            """,
            [table_name, equipment_class, other_classes, confidence] + row_values
        )

    conn.commit()
    print("Created wide-format a_mapping_table")

def recategorize_ontologically(conn, smart_col_mapping, smart_col_list):
    """
    Convert dict-of-dicts column mapping into the flat
    (table_name, raw_col) -> super_col mapping required by
    build_master_equipment.

    Input:
        smart_col_mapping = {
            table_name: {
                super_col: [raw_cols]
            }
        }

        smart_col_list = canonical list of super_cols

    Output:
        contextual_mapping = {
            (table_name, raw_col): super_col
        }
    """

    contextual_mapping = {}

    for table_name, mapping in smart_col_mapping.items():

        for super_col, raw_cols in mapping.items():

            # Skip unexpected super_cols
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
                contextual_mapping[(table_name, raw_col)] = super_col

    return contextual_mapping

