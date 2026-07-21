import re
from utils.normalization import normalize_text, esc_literal, esc_ident
from utils.safe_SQL_caller import q

def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i+size]


def build_master_equipment(conn, raw_col_map, super_cols):
    """
    Build the canonical a_master_equipment table using the new architecture:

    raw_col_map:
        (table_name, raw_col) -> super_col
        (table_name, "__metadata__") -> metadata_dict

    super_cols:
        canonical list of super columns
    """

    cursor = conn.cursor()

    # ----------------------------------------------------------------------
    # 1. Drop old master table
    # ----------------------------------------------------------------------
    cursor.execute("DROP TABLE IF EXISTS a_master_equipment")

    # ----------------------------------------------------------------------
    # 2. Create new master table schema
    # ----------------------------------------------------------------------
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

    # ----------------------------------------------------------------------
    # 3. Load table list + URLs
    # ----------------------------------------------------------------------
    table_rows = cursor.execute("SELECT table_name FROM a_meta_table").fetchall()
    all_tables = [r[0] for r in table_rows]

    meta_rows = cursor.execute("SELECT table_name, url FROM a_meta_table").fetchall()
    table_to_url = {t: url for t, url in meta_rows}

    # Filter out meta tables
    tables = [t for t in all_tables if not t.startswith("a_")]

    # ----------------------------------------------------------------------
    # 4. Process tables in chunks
    # ----------------------------------------------------------------------
    for batch in chunked(tables, 50):

        for table_name in batch:

            # ------------------------------------------------------------------
            # 4A. Extract metadata for this table
            # ------------------------------------------------------------------
            metadata = raw_col_map.get((table_name, "__metadata__"), {})

            # ------------------------------------------------------------------
            # 4B. Get raw columns from SQLite
            # ------------------------------------------------------------------
            raw_cols = cursor.execute(
                f"PRAGMA table_info({q(table_name)})"
            ).fetchall()

            raw_col_names = [normalize_text(r[1]) for r in raw_cols]

            # ------------------------------------------------------------------
            # 4C. Build mapping: super_col -> list of raw_cols
            # ------------------------------------------------------------------
            mapping_for_table = {col: [] for col in super_cols}

            for raw_col in raw_col_names:
                base = re.sub(r'\.\d+$', '', raw_col)
                key = (table_name, base)

                if key in raw_col_map:
                    super_col = raw_col_map[key]
                    mapping_for_table[super_col].append(raw_col)

            # ------------------------------------------------------------------
            # 4D. Build SELECT statement for this table
            # ------------------------------------------------------------------
            url = table_to_url.get(table_name)
            select_parts = [
                f"'{esc_literal(table_name)}' AS table_name",
                f"'{esc_literal(url)}' AS url"
            ]

            # ------------------------------------------------------------------
            # 4E. Add metadata columns (merged into super_cols)
            # ------------------------------------------------------------------
            for super_col in super_cols:

                # If metadata contains this super_col, use metadata value
                if super_col in metadata:
                    val = metadata[super_col]
                    if val is None:
                        select_parts.append(f"NULL AS \"{esc_ident(super_col)}\"")
                    else:
                        select_parts.append(
                            f"'{esc_literal(str(val))}' AS \"{esc_ident(super_col)}\""
                        )
                    continue

                # Otherwise, use raw column values
                raw_list = mapping_for_table[super_col]
                unique_raws = list(dict.fromkeys(raw_list))

                if len(unique_raws) == 0:
                    select_parts.append(f"NULL AS \"{esc_ident(super_col)}\"")

                elif len(unique_raws) == 1:
                    raw = unique_raws[0]
                    select_parts.append(
                        f'"{esc_ident(raw)}" AS "{esc_ident(super_col)}"'
                    )

                else:
                    # Merge multiple raw columns
                    expr = f'"{esc_ident(unique_raws[0])}"'
                    for r in unique_raws[1:]:
                        expr = (
                            f"CASE WHEN {expr} = \"{esc_ident(r)}\" "
                            f"THEN {expr} ELSE {expr} || '; ' || \"{esc_ident(r)}\" END"
                        )

                    select_parts.append(f"({expr}) AS \"{esc_ident(super_col)}\"")

            # ------------------------------------------------------------------
            # 4F. Execute SELECT + INSERT
            # ------------------------------------------------------------------
            select_sql = (
                "SELECT " + ", ".join(select_parts) +
                f" FROM \"{esc_ident(table_name)}\""
            )

            cursor.execute(f"INSERT INTO a_master_equipment {select_sql}")

            # ------------------------------------------------------------------
            # 4G. Drop cleaned table now that it's merged
            # ------------------------------------------------------------------
            cursor.execute(f"DROP TABLE IF EXISTS {q(table_name)}")

    # ----------------------------------------------------------------------
    # 5. Finalize
    # ----------------------------------------------------------------------
    conn.commit()
    cursor.execute("VACUUM")
    print("Created a_master_equipment and cleaned up after myself.")
