from utils.nav_tree import *
from utils.regex_match import regex_match_to_ontology
import re

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
        matches = regex_match_to_ontology(header)
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
            print(f"Somehow, regex_match_to_ontology returned a non-class: {match}")
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
