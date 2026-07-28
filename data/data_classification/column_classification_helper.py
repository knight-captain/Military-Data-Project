from owlready2 import ThingClass

from utils.regex_match import regex_match_to_ontology
from utils.nav_tree import *

def classify_raw_col(raw_col):
    """
    Regex-based column classifier.
    Returns a list of super_cols matched through:
      - direct property matches
      - class matches (via inherited properties)
    """
    raw_col = raw_col.lower()
    super_col_matches = []

    # 1. Regex match to ontology entities
    entities = regex_match_to_ontology(raw_col)

    for ent_label in entities:
        # ent_label is the name of a class or property
        entity = get_class(ent_label) or get_property(ent_label)
        if entity is None:
            continue

        # 2. Direct super_col annotation
        sc = get_super_col(entity)
        if sc:
            super_col_matches.append(sc)
            continue

        # 3. If entity is a class, climb its property tree
        if isinstance(entity, ThingClass):
            props = get_all_properties_of_class(entity)
            for prop in props:
                sc_prop = get_super_col(prop)
                if sc_prop:
                    super_col_matches.append(sc_prop)

    return super_col_matches

