import re
from utils.nav_tree import *

def regex_match_to_ontology(_input):
    """
    Return all ontology classes or properties whose regex patterns match the input.
    Works for table names, headers, raw_cols, etc.
    """
    _input = _input.lower()
    matches = []

    for entity in get_all_ontology_entities():
        for pattern in get_regex(entity):
            try:
                if re.search(pattern, _input, re.IGNORECASE):
                    # Use entity.name if available, else str(entity)
                    label = getattr(entity, "name", str(entity))
                    matches.append(label)
            except re.error as e:
                print(f"[REGEX ERROR] {entity}: '{pattern}' → {e}")

    return matches
