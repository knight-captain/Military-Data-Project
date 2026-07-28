import re
from utils.normalization import esc_literal, esc_ident
from utils.safe_SQL_caller import q

def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i+size]


def build_master_equipment(conn, contextual_mapping, super_cols):
    """
    Build the canonical a_master_equipment table using contextual_mapping.
    contextual_mapping:
        {
            table_name: {
                "__metadata__": {country, class_path, sub_class, ...},
                super_col: [raw_cols],
                ...
            }
        }
    super_cols: [canonical list of super columns]
    """

    cursor = conn.cursor()

    # 1. Drop old master table
    cursor.execute("DROP TABLE IF EXISTS a_master_equipment")

    # 2. Create new master table schema
    col_defs = ", ".join(f"{q(col)} TEXT" for col in super_cols)
    cursor.execute(
        f"""
        CREATE TABLE a_master_equipment (
            table_name TEXT,
            url TEXT,
            {col_defs}
        )
        """
    )

    # 3. Process tables in chunks (optional but safe)
    table_names = list(contextual_mapping.keys())

    for batch in chunked(table_names, 50):

        for table_name in batch:

            mapping = contextual_mapping[table_name]
            metadata = mapping.get("__metadata__", {})

            # URL is stored in metadata (same as classify_tables)
            url = metadata.get("url", "")

            # 4. Build SELECT statement
            select_parts = [
                f"'{esc_literal(table_name)}' AS table_name",
                f"'{esc_literal(url)}' AS url"
            ]

            for super_col in super_cols:

                meta_val = metadata.get(super_col)
                raw_cols = mapping.get(super_col, [])

                # Build raw column expression
                raw_expr = " || '; ' || ".join(
                    f'"{esc_ident(r)}"' for r in raw_cols
                )

                # Case 1: metadata + raw_cols
                if meta_val is not None:
                    meta_expr = f"'{esc_literal(str(meta_val))}'"
                    if raw_expr:
                        expr = f"{meta_expr} || '; ' || {raw_expr}"
                    else:
                        expr = meta_expr

                # Case 2: raw_cols only
                else:
                    expr = raw_expr if raw_expr else "NULL"

                select_parts.append(f"{expr} AS \"{esc_ident(super_col)}\"")

            # 5. Insert into master table
            select_sql = (
                "SELECT " + ", ".join(select_parts) +
                f" FROM \"{esc_ident(table_name)}\""
            )

            cursor.execute(f"INSERT INTO a_master_equipment {select_sql}")

            # 6. Drop cleaned table now that it's merged
            cursor.execute(f"DROP TABLE IF EXISTS {q(table_name)}")

    # 7. Finalize
    conn.commit()
    cursor.execute("VACUUM")
    print("Created a_master_equipment and cleaned up after myself.")
