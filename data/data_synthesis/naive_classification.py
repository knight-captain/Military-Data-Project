from utils.nav_tree import *
import re

def naive_match(header):
    """
    Return all ontology classes whose regex patterns match the header.
    Uses nav_tree.get_regex() dynamically.
    """
    header = header.lower()
    matched = []

    # Iterate over all ontology classes
    for cls_label in get_all_class_labels():
        cls = get_class(cls_label)
        if cls is None:
            print(f"somehow got a non-class: {cls_label}")
            continue
        for pattern in get_regex(cls):
            try:
                if re.search(pattern, header, re.IGNORECASE):
                    matched.append(cls_label)
            except re.error as e:
                print(f"[REGEX ERROR] {cls_label}: '{pattern}' → {e}")
    return matched


def classify_naively(headers):
    """
    Try to classify using h4 → h3 → h2.
    Collapse hierarchical matches using get_descendants().
    Identify equipment classes using get_ancestor().
    """

    h2, h3, h4 = headers
    header_hierarchy = [h4, h3, h2]

    # 1. Collect regex matches for the headers
    all_matches = []
    for header in header_hierarchy:
        if not header:
            continue
        matches = naive_match(header)
        all_matches.extend(matches)

    if not all_matches:
        print(f"no matches for {header}")
        return {
            "equipment_class": None,
            "other_classes": [],
            "confidence": 0.0
        }

    # 2. Collapse to leafmost classes using ontology tree & Deduplicate
    other_classes = list(set(get_descendants(all_matches)))

    # 3. Identify equipment-branch classes (not non-Equipment)
    equipment_branches = []
    for match in other_classes:
        cls = get_class(match)
        if cls is None:
            print(f"Somehow, naive_match returned a non-class: {match}")
            continue #this shouldn't happen

        # Root = get_ancestor(cls, 0) → "Equipment"
        root = get_ancestor(cls, 0)
        root_label = root.label[0] if root.label else root.name
        if root_label == "Equipment":
            equipment_branches.append(match)

    # 4. If exactly one leafmost equipment class → assign it
    if len(equipment_branches) == 1:
        equipment_class = equipment_branches[0]
        other_classes.remove(equipment_branches[0])

        return {
            "equipment_class": equipment_class,
            "other_classes": other_classes,
            "confidence": 1.0
        }

    # 5. Otherwise → ambiguous
    return {
        "equipment_class": None,
        "other_classes": other_classes,
        "confidence": 0.0
    }
