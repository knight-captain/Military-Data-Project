"""
Classifies each cleaned equipment table using regex rules from
ontology/table_regex_rules.csv.

Output (returned to synthesize_equipment.py):
    table_categories : dict {
        table_name : {
            "branch": str | None,
            "role": str | None,
            "domain": str | None,
            "group_1": str | None,
            "group_2": str | None,
            "platform": str | None,
            "ignore": bool
        }
    }

This module DOES NOT write anything to the database.
"""

import re
from pathlib import Path
from utils import read_csv
from utils.normalization import normalize_text


# Classification of a single table title
def classify_table(title, rules):
    """
    Apply regex rules to a table title.

    Dynamically builds the classification schema based on the rule types
    present in the CSV. Only "ignore" is treated as a special case.

    Returns:
        dict with keys dynamically derived from rules, plus "ignore".
    """

    # Build ontology keys dynamically from the rules
    ontology_keys = set()

    for rule in rules:
        t = rule["type"]
        if t != "ignore":
            ontology_keys.add(t)

    # Initialize result dict dynamically
    result = {key: None for key in ontology_keys}
    result["ignore"] = False

    # Apply rules
    for rule in rules:
        if rule["pattern"].search(title):
            t = rule["type"]

            if t == "ignore":
                result["ignore"] = True
                continue

            # Assign category to the dynamically created key
            result[t] = rule["category"]

    return result


# Main categorization function
def categorize_all_tables(conn):
    """
    Classify all cleaned tables using regex rules.

    Returns:
        table_categories : dict {
            table_name : {
                branch, role, domain, group_1, group_2, platform, ignore
            }
        }

    Notes:
        - DOES NOT write to the DB.
        - Skips tables starting with "a_".
        - Skips tables classified as ignore=True.
    """

    # Load raw rules from CSV
    rules_raw = read_csv.to_list_of_dicts(
        Path(__file__).resolve().parents[2] / "ontology" / "table_regex_rules.csv"
    )
    if not rules_raw:
        raise ValueError("table_regex_rules.csv is empty or unreadable.")

    # Normalize header names dynamically
    header_map = {}
    for key in rules_raw[0].keys():
        nk = normalize_text(key)
        header_map[nk] = key

    required = {"category", "type", "regex"}
    missing = required - set(header_map.keys())
    if missing:
        raise ValueError(f"Missing required columns in regex CSV: {missing}")

    # Build compiled rule objects
    rules = []

    for row in rules_raw:
        category = row[header_map["category"]].strip()
        type_ = normalize_text(row[header_map["type"]])
        regex_text = row[header_map["regex"]].strip()

        try:
            #TODO: do we need (?i) vs re.IGNORECASE?
            pattern = re.compile(regex_text, re.IGNORECASE)
        except re.error as e:
            print(f"[REGEX ERROR] Invalid regex '{regex_text}': {e}")
            continue

        rules.append({
            "category": category,
            "type": type_,
            "pattern": pattern
        })

    # Load table metadata
    cursor = conn.cursor()
    sql = """
        SELECT table_name, section_h2, section_h3, section_h4
        FROM a_meta_table
    """
    rows = cursor.execute(sql).fetchall()

    table_categories = {}

    # Classify each table
    for table_name, h2, h3, h4 in rows:

        # Skip meta tables
        if table_name.startswith("a_"):
            print(f"skipping meta-table: {table_name}")
            continue

        # Build title string
        title = " ".join([h2 or "", h3 or "", h4 or ""])
        title = normalize_text(title)

        classification = classify_table(title, rules)

        # Skip ignored tables
        if classification["ignore"]:
            # print(f"ignoring {table_name}")
            continue

        table_categories[table_name] = classification

    print(f"Categorized {len(table_categories)} tables")
    return table_categories
