from utils.execute_SQL import get_a_meta_table
from utils.nav_tree import *
import re


def naive_match(header, rules):
    """
    Return all ontology classes whose regex patterns match the header.
    """
    classes_matched = []
    header = header.lower()

    for cls_label, regex_list in rules.items():
        for pattern in regex_list:
            try:
                if re.search(pattern, header, re.IGNORECASE):
                    classes_matched.append(cls_label)
            except re.error as e:
                print(f"[REGEX ERROR] {cls_label}: '{pattern}' → {e}")

    return classes_matched


def collapse_hierarchy(matches, paths):
    """
    Given multiple matched classes, collapse them to the leaf-most class
    IF they are in the same branch.

    Example:
        ["Vessel", "Warship", "Destroyer"] → ["Destroyer"]
        ["Aircraft", "Vessel"] → ["Aircraft", "Vessel"]  (different branches)
    """
    if len(matches) <= 1:
        return matches

    leaf = max(matches, key=lambda m: len(paths[m]))

    root = paths[leaf][1] if len(paths[leaf]) > 1 else None

    same_branch = all(
        len(paths[m]) > 1 and paths[m][1] == root
        for m in matches
    )

    if same_branch:
        return [leaf]

    return matches


def classify_naively(headers, rules, paths):
    """
    Try to classify using h4 → h3 → h2.
    Collapse hierarchical matches.
    Return a single class if possible.
    Otherwise return None (advanced needed).
    """
    h2, h3, h4 = headers
    header_hierarchy = [h4, h3, h2]

    for header in header_hierarchy:
        if not header:
            continue

        matches = naive_match(header, rules)

        if len(matches) == 0:
            # print(f"Not in Ontology: {header}")
            continue

        # Collapse hierarchical matches
        collapsed = collapse_hierarchy(matches, paths)

        if len(collapsed) == 1:
            return collapsed[0]  # SUCCESS

        # More than one class → advanced sorting needed
        return collapsed #this will trigger on the first header: we want up to 3 headers analyzed

    return None

def classify_tables(conn):
    # Load table metadata
    a_meta_table = get_a_meta_table(conn)

    parents, children, paths, rules = get_relationships("ontology/Military_Ontology.rdf")
    print(rules)
    # print(parents)

    table_classes = {}  # table_name → class or list of classes

    # First pass: naive classification
    for table_name, meta in a_meta_table.items():
        headers = (
            meta["section_h2"],
            meta["section_h3"],
            meta["section_h4"]
        )
        table_classes[table_name] = classify_naively(headers, rules, paths)

    # Second pass: advanced classification
    for table_name in a_meta_table:
        if isinstance(table_classes[table_name], list):
            table_classes[table_name] = classify_advanced(
                table_name,
                table_classes[table_name],
                a_meta_table[table_name],
                parents,
                children,
                paths,
                rules
            )

    classified_count = sum(
        1 for c in table_classes.values() if isinstance(c, str)
    )

    print(f"{classified_count}/{len(a_meta_table)} tables classified")

    return table_classes #dict[table_name] = single_class_from_ontology