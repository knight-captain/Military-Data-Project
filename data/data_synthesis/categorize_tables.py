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

from data.data_synthesis.calculate_confidence import calculate_confidence
from data.data_synthesis.cluster_tables import cluster_tables
from data.data_synthesis.derive_hierarchy import derive_hierarchy
from utils import read_csv
from utils.normalization import normalize_text


# Classification of a single table title
def classify_table(title, rules):
    """
    Apply regex rules to a table via <h2/3/4>.

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
    #TODO: make sure this can hit miltiple categories
    for rule in rules:
        if rule["pattern"].search(title):
            t = rule["type"]

            if t == "ignore":
                result["ignore"] = True
                continue

            # Assign category to the dynamically created key
            result[t] = rule["category"]

    return result

'''FOR debugging'''
def report_cluster_stats(clusters, roots):
    """Prints summary statistics about the clustering results."""

    num_clusters = len(clusters)
    num_roots = len(roots)

    # cluster strength
    strengths = [c.get("strength", 0.0) for c in clusters]
    avg_strength = sum(strengths) / num_clusters if num_clusters else 0.0

    # parent strength
    parent_strengths = [c.get("parent_strength", 0.0) for c in clusters]
    avg_parent_strength = sum(parent_strengths) / num_clusters if num_clusters else 0.0

    print("\n=== CLUSTER REPORT ===")
    print(f"Total clusters: {num_clusters}")
    print(f"Root clusters: {num_roots}")
    print(f"Average cluster strength: {avg_strength:.2f}")
    print(f"Average parent strength: {avg_parent_strength:.2f}")
    print("======================\n")


# Main categorization function
def categorize_all_tables(conn):
    """
    Classify all cleaned tables using regex rules.

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
    table_categories_w_h234 = {}

    # Classify each table
    for table_name, h2, h3, h4 in rows:

        # Skip meta tables
        if table_name.startswith("a_"):
            print(f"skipping meta-table: {table_name}")
            continue

        # Build title string
        title = " ".join([h2 or "", h3 or "", h4 or ""])
        title = (title)

        classification = classify_table(title, rules)

        # Skip ignored tables
        if classification["ignore"]:
            # print(f"ignoring {table_name}")
            continue

        table_categories[table_name] = classification
        table_categories_w_h234[table_name] = (classification, h2, h3, h4)

    print(f"Categorized {len(table_categories)} tables")

    #now group tables by the <h2/3/4> as well as the regexed categories from those <h2/3/4>
    clusters, fingerprints = cluster_tables(conn, table_categories_w_h234)
    nodes = derive_hierarchy(conn, clusters, table_categories_w_h234)
    smart_table_categories = calculate_confidence(fingerprints, nodes)

    print("FROM CAT_TABLES")
    # report_cluster_stats(clusters, nodes) #for fine-tuning
    print(f"Categorized {len(smart_table_categories)} smart_tables")
    return table_categories