"""
categorize_tables.py
--------------------
This module classifies each cleaned equipment table using
regex rules defined in ontology/table_regex_rules.csv.

Output:
    a_table_categories:
        table_name | branch | role | domain | type | platform | ignore

This table is consumed by categorize_columns.py and
build_master_equipment.py.
"""

import csv
import re
from pathlib import Path
from utils.safe_SQL_caller import q


# ------------------------------------------------------------
# LOAD REGEX RULES
# ------------------------------------------------------------

def load_table_regex_rules(path):
    """
    Load table classification regex rules from CSV.

    CSV format: category,type,regex

    Returns:
        list[dict]: [
            {
                "category": "NAVY",
                "type": "BRANCH",
                "pattern": compiled_regex
            },
            ...
        ]
    """
    rules = []
    path = Path(path)

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rules.append({
                "category": row["category"].strip(),
                "type": row["type"].strip().lower(),   # branch/role/domain/type/platform/ignore
                "pattern": re.compile(row["regex"], re.IGNORECASE)
            })

    return rules


# ------------------------------------------------------------
# APPLY RULES TO A SINGLE TABLE
# ------------------------------------------------------------

def classify_table(title, rules):
    """
    Apply all regex rules to a table title.

    Args:
        title (str): table title or combined <h2>/<h3>/<h4>
        rules (list): loaded regex rules

    Returns:
        dict: {
            "branch": str | None,
            "role": str | None,
            "domain": str | None,
            "type": str | None,
            "platform": str | None,
            "ignore": bool
        }
    """
    result = {
        "branch": None,
        "role": None,
        "domain": None,
        "type": None,
        "platform": None,
        "ignore": False
    }

    for rule in rules:
        if rule["pattern"].search(title):
            t = rule["type"]

            if t == "ignore":
                result["ignore"] = True
            else:
                result[t] = rule["category"]

    return result


# ------------------------------------------------------------
# MAIN PIPELINE FUNCTION
# ------------------------------------------------------------

def categorize_all_tables(conn, regex_rules_path=None):
    """
    Classify all tables using regex rules and write results to a_table_categories.

    Returns:
        dict: {
            table_name: {
                "branch": str | None,
                "role": str | None,
                "domain": str | None,
                "type": str | None,
                "platform": str | None,
                "ignore": bool
            }
        }
    """
    if regex_rules_path is None:
        regex_rules_path = Path(__file__).resolve().parents[2] / "ontology" / "table_regex_rules.csv"

    rules = load_table_regex_rules(regex_rules_path)
    cursor = conn.cursor()

    # Load table names + headings
    sql = "SELECT table_name, section_h2, section_h3, section_h4 FROM a_meta_table"
    rows = cursor.execute(sql).fetchall()

    # Drop + recreate output table
    cursor.execute("DROP TABLE IF EXISTS a_table_categories")
    cursor.execute("""
        CREATE TABLE a_table_categories (
            table_name TEXT PRIMARY KEY,
            branch TEXT,
            role TEXT,
            domain TEXT,
            type TEXT,
            platform TEXT,
            ignore INTEGER
        )
    """)

    # In-memory return structure
    table_rules = {}

    for table_name, section_h2, section_h3, section_h4 in rows:
        title = " ".join([section_h2 or "", section_h3 or "", section_h4 or "", table_name or ""])
        classification = classify_table(title, rules)

        # Write to DB
        cursor.execute(
            """
            INSERT INTO a_table_categories
            (table_name, branch, role, domain, type, platform, ignore)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                table_name,
                classification["branch"],
                classification["role"],
                classification["domain"],
                classification["type"],
                classification["platform"],
                1 if classification["ignore"] else 0
            )
        )

        # Add to return dict
        table_rules[table_name] = classification

    conn.commit()
    print("Created a_table_categories")

    return table_rules
