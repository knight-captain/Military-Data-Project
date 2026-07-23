from utils.nav_tree import *
from utils.normalization import normalize_text
from utils.regex_match import regex_match_to_ontology


def evaluate_class(match):
    """
    Return:
      True  → match is an Equipment class
      False → match is not in ontology or maps to nothing
      super_col → match maps to a non-equipment ontology root (status, etc.)
    """
    try:
        ancestor = get_ancestor(match, 0)
        if ancestor == get_class("Equipment"):
            return True

        # Non-equipment ontology class → return its super_col
        #TODO: but super_cols are mostly properties, not classes. 
        is_class = get_class(match)
        if is_class is None:
            col = get_super_col(match)
            if col:
                return col
            #No super_col
            return False
    except:
        return None


def deduplicate_classes(classes_to_deduplicate):
    '''
    DEDUPLICATE:
    - if same path, get_descendants to use leaf_most, delete the other
    - if different paths, use get_ancestors to get closest common ancestor, add both to note col and print flag
    '''
    leaf_classes = get_descendants(classes_to_deduplicate)
    
    if len(set(leaf_classes)) == 1:
        return leaf_classes[0]

    # Find nearest common ancestor
    for depth in range(0, 6):
        try:
            generation = [get_ancestor(c, depth) for c in leaf_classes]
        except:
            # delved too greedily and too deep
            return leaf_classes[0]

        # If all ancestors at this depth are identical → keep going
        if len(set(generation)) == 1:
            common_ancestor = generation[0]
        else:
            # Diverged → return deepest common ancestor
            return common_ancestor

    return common_ancestor


def fix_classes(a_master_equipment):
    """
    Fix the sub_class column in a_master_equipment.

    For each row:
      - evaluate ontology matches
      - deduplicate equipment classes
      - move non-equipment classes to notes
      - move unknown classes to notes
      - set final_subclass in the DataFrame
    """

    fixed = a_master_equipment.copy()

    not_in_ontology = set()

    for idx, row in fixed.iterrows():

        if idx % 1000 == 0:
            print(f"Rows checked: {idx}")

        raw_sub = row["sub_class"]

        if not raw_sub:
            continue

        # Split merged values
        contestants = raw_sub.split(";")

        equip_candidates = []
        non_equip_classes = []
        unknown_classes = []

        for raw_contestant in contestants:
            contestant = normalize_text(raw_contestant)
            matches = regex_match_to_ontology(contestant)

            if not matches:
                unknown_classes.append(contestant)
                continue

            for match in matches:
                cls = get_class(match, warn=False)
                if cls is None:
                    #Not a class, but maybe a property
                    try:
                        col = evaluate_class(match)
                        print(f"col found for non-class: {idx} {contestant} - {match} - {is_equip}")
                    except:
                        continue
                    continue

                is_equip = evaluate_class(match)
                if is_equip is True:
                    equip_candidates.append(match)
                elif is_equip is False:
                    print(f"No super_col: {idx} - {contestant} - {match}")
                    non_equip_classes.append((contestant, is_equip))
                elif is_equip is None:
                    # print(f"evaluate broke: {idx} - {contestant} - {match}")
                    # unknown_classes.append(contestant)
                else:
                    # is_equip is a super_col (status, etc.)
                    print(f"{idx} {contestant} - {match} matched to super_col {is_equip}")
                    non_equip_classes.append((contestant, is_equip))

        # Deduplicate equipment classes
        if equip_candidates:
            final_subclass = deduplicate_classes(equip_candidates)
        else:
            final_subclass = None

        # Write final_subclass into the DataFrame
        fixed.at[idx, "sub_class"] = final_subclass

        # Move leftovers into notes
        notes = row.get("notes", "")

        #TODO: send to best col, like role or status
        if non_equip_classes:
            notes += f"; Non-equipment classes: {non_equip_classes}"

        if unknown_classes:
            notes += f"; Unknown classes: {unknown_classes}"
            not_in_ontology.update(unknown_classes)

        fixed.at[idx, "notes"] = notes.strip(" |")

    print(f"Consider adding to Ontology: {len(not_in_ontology)}")

    return fixed
