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

# def collapse_hierarchy(matches, paths):
#     """
#     Given multiple matched classes, collapse them to the leaf-most class
#     IF they are in the same branch.

#     Example:
#         ["Vessel", "Warship", "Destroyer"] → ["Destroyer"]
#         ["Aircraft", "Vessel"] → ["Aircraft", "Vessel"]  (different branches)
#     """
#     if len(matches) <= 1:
#         return matches

#     leaf = max(matches, key=lambda m: len(paths[m]))

#     root = paths[leaf][1] if len(paths[leaf]) > 1 else None

#     same_branch = all(
#         len(paths[m]) > 1 and paths[m][1] == root
#         for m in matches
#     )

#     if same_branch:
#         return [leaf]

#     return matches


def classify_naively(headers, rules, paths):
    """
    Try to classify using h4 → h3 → h2.
    Collapse hierarchical matches.
    Return a single class if possible.
    Otherwise return None (advanced needed).
    """
    h2, h3, h4 = headers
    header_hierarchy = [h4, h3, h2]

    all_matches = []

    # Collect all matches from all headers
    for header in header_hierarchy:
        if not header:
            continue
        matches = naive_match(header, rules)
        if matches:
            all_matches.extend(matches)

    if not all_matches:
        return {
            "equipment_class": None,
            "other_classes": [],
            "confidence": 0.0
        }
        print(f"No match for headers: {headers}")

    # Collapse hierarchical matches
    collapsed = get_descendants(all_matches, paths)

    # Identify Equipment-branch classes
    equipment_branch = [
        cls for cls in collapsed
        if get_ancestor(cls, 0, paths) == "Equipment"
    ]

    # If exactly one Equipment class → assign it
    if len(equipment_branch) == 1:
        equipment_class = equipment_branch[0]
        other_classes = [cls for cls in collapsed if cls != equipment_class]
        return {
            "equipment_class": equipment_class,
            "other_classes": other_classes,
            "confidence": 1.0
        }

    # Otherwise → no Equipment class assigned
    return {
        "equipment_class": None,
        "other_classes": collapsed,
        "confidence": 0.0
    }