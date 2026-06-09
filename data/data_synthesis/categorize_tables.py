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

def classify_table(title, rules):
    """
    Apply regex rules to a table title.

    Returns:
        dict with keys:
            branch, role, domain, group_1, group_2, platform, ignore
    """
    result = {
        "branch": None,
        "role": None,
        "domain": None,
        "group_1": None,
        "group_2": None,
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

    # Load rules from CSV
    rules = read_csv.to_regex_rules(
        Path(__file__).resolve().parents[2] / "ontology" / "table_regex_rules.csv"
    )

    cursor = conn.cursor()
    
    sql = """
        SELECT table_name, section_h2, section_h3, section_h4
        FROM a_meta_table
    """
    rows = cursor.execute(sql).fetchall()

    table_categories = {}

    for table_name, h2, h3, h4 in rows:

        if table_name.startswith("a_"):
            continue
        
        title = " ".join([h2 or "", h3 or "", h4 or ""])
        classification = classify_table(title, rules)

        if classification["ignore"]:
            continue

        table_categories[table_name] = classification

    print(f"Categorized {len(table_categories)} tables")
    return table_categories