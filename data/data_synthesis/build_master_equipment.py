"""
build_master_equipment.py
-------------------------

Final synthesis step:
Builds the canonical a_master_equipment table using:

- contextual_mapping (passed in from synthesize_equipment.py)
- a_table_categories (table → branch/domain/type/platform/ignore)
- ontology/super_columns.txt (canonical schema)
"""

from pathlib import Path
from utils.safe_SQL_caller import q, ql


# LOAD SUPPORTING DATA
def load_table_categories(conn):
    """
    Load table categories from a_table_categories.

    Returns:
        dict: { table_name : {branch, role, domain, type, platform, ignore} }
    """
    sql = """
        SELECT table_name, branch, role, domain, type, platform, ignore
        FROM a_table_categories
    """
    categories = {}
    for row in conn.execute(sql).fetchall():
        table_name, branch, role, domain, type_, platform, ignore = row
        categories[table_name] = {
            "branch": branch,
            "role": role,
            "domain": domain,
            "type": type_,
            "platform": platform,
            "ignore": bool(ignore)
        }
    return categories


def load_super_columns(path):
    """
    Load canonical super-column names from ontology/super_columns.txt.
    """
    cols = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            c = line.strip()
            if c:
                cols.append(c)
    return cols


def list_equipment_tables(conn):
    """
    Return all scraped equipment tables (excluding meta tables).
    """
    sql = "SELECT name FROM sqlite_master WHERE type='table'"
    tables = [row[0] for row in conn.execute(sql).fetchall()]
    return [t for t in tables if not t.startswith("a_")]


def get_raw_columns(conn, table):
    """
    Return list of raw column names for a given table.
    """
    sql = f'PRAGMA table_info("{table}")'
    return [row[1] for row in conn.execute(sql).fetchall()]


# ALIGNMENT LOGIC
def build_aligned_select(table, conn, contextual_map, super_cols, categories):
    """
    Build SELECT that aligns a raw table to canonical schema.

    - Uses contextual mapping (table_name, raw_col) → super_col
    - Inserts "MISSING" where a value SHOULD exist but does not
    - Inserts NULL where a value is not applicable

    Returns:
        str: SQL SELECT statement
    """

    raw_cols = get_raw_columns(conn, table)
    cat = categories[table]

    parts = [
        f"{q(table)} AS source_table",
        f"{ql(cat['branch'])} AS branch",
        f"{ql(cat['domain'])} AS domain",
        f"{ql(cat['type'])} AS type",
        f"{ql(cat['platform'])} AS platform"
    ]

    # Add canonical super-columns
    for super_col in super_cols:

        # Find raw column mapped to this super-column
        matches = [
            rc for rc in raw_cols
            if contextual_map.get((table, rc)) == super_col
        ]

        if matches:
            parts.append(f"{q(matches[0])} AS {q(super_col)}")
        else:
            # Placeholder for ontology-based required fields
            parts.append(f"NULL AS {q(super_col)}")

    return "SELECT " + ", ".join(parts) + f" FROM {q(table)}"


def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i+size]


# MASTER TABLE BUILDER
def build_master_equipment(conn, contextual_mapping, super_cols_path):
    """
    Build a_master_equipment using contextual mapping + table categories.
    """

    cursor = conn.cursor()

    categories = load_table_categories(conn)
    super_cols = load_super_columns(super_cols_path)

    tables = list_equipment_tables(conn)

    # Filter out ignored tables
    tables = [t for t in tables if not categories.get(t, {}).get("ignore", False)]

    # Chunk tables to avoid SQLite UNION limits
    batches = list(chunked(tables, 300))
    temp_tables = []

    for i, batch in enumerate(batches):
        temp_name = f"temp_batch_{i}"
        temp_tables.append(temp_name)

        selects = [
            build_aligned_select(t, conn, contextual_mapping, super_cols, categories)
            for t in batch
        ]

        union_sql = " UNION ALL ".join(selects)
        cursor.execute(f"CREATE TEMP TABLE {temp_name} AS {union_sql}")

    # Final merge
    final_union = " UNION ALL ".join(
        f"SELECT * FROM {q(t)}" for t in temp_tables
    )

    cursor.execute("DROP TABLE IF EXISTS a_master_equipment")
    cursor.execute(f"CREATE TABLE a_master_equipment AS {final_union}")

    conn.commit()
    print("Created a_master_equipment")
