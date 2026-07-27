import pandas as pd

from utils.edit_df import add_to_cell
from utils.nav_tree import *
from utils.normalization import normalize_text, singularize
from utils.regex_match import regex_match_to_ontology

# FOR DEBUGGING
def is_sql_safe(val):
    return isinstance(val, (str, int, float)) or val is None
def debug_sql(func, val):
    if not is_sql_safe(val):
        print(f"{func}: {val} - {type(val)}")


def deduplicate_classes(matches_to_deduplicate):
    '''
    DEDUPLICATE:
    - if same path, get_descendants to use leaf_most, delete the other
    - if different paths, use get_ancestors to get closest common ancestor, add both to note col and print flag
    '''
    leaf_classes = get_descendants(matches_to_deduplicate)

    if len(set(leaf_classes)) == 1:
        return leaf_classes[0]

    # Find nearest common ancestor
    shared_ancestral_path = []
    for depth in range(0, 10):
        try:
            generation = [get_name(get_ancestor(c, depth)) for c in leaf_classes]
        except:
            # delved too greedily and too deep
            return shared_ancestral_path[depth-1]

        # If all ancestors at this depth are identical → keep going
        if len(set(generation)) == 1:
            shared_ancestral_path.append(generation[0])
        else:
            # Diverged → return deepest common ancestor
            return shared_ancestral_path[depth-1]

    return shared_ancestral_path[depth]


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

    df = a_master_equipment.copy()

    not_in_ontology = []

    for idx, row in df.iterrows():
        raw_sub = row["sub_class"]

        if idx % 1000 == 0:
            print(f"On row: {idx}")

        if not raw_sub:
            # CASE 6
            continue

        contestants = [singularize(c.strip()) for c in raw_sub.split(";") if singularize(c.strip())]
        # super_cols_to_edit[super_col] = value to add/replace in that super_col
        super_cols_to_edit = {}

        for contestant in contestants:
            matches = regex_match_to_ontology(contestant)

            if not matches:
                # CASE 7
                not_in_ontology.append(contestant)
                super_cols_to_edit.setdefault("note", []).append(contestant)
                continue

            for match in matches:
                cls = get_class(match, warn=False)

                if cls is not None:
                    '''
                    Class Path; Cases: 1-5 possible
                    '''
                    ancestor0 = get_ancestor(cls, 0)

                    if ancestor0 == get_class("Equipment"):
                        # CASE 1: add for deduping
                        super_cols_to_edit.setdefault("sub_class", []).append(match)
                        super_cols_to_edit.setdefault("note", []).append(contestant)
                        continue

                    elif ancestor0 != get_class("EquipMission"):
                        # CASE 2: ignore
                        # this is a class we don't care about (country, rank, being, infrustructure)
                        # we don't even want these moved to note
                        continue

                    # CASE 3-5: for EquipMission classes
                    entity_for_property = get_ancestor(match, 1)
                else:
                    # CASE 4–5
                    entity_for_property = match

                # super_col = evaluate_property(idx, entity_for_property)
                super_col = get_super_col(entity_for_property)

                if super_col is None:
                    # CASE 3 or CASE 4 (already flagged)
                    super_cols_to_edit.setdefault("note", []).append(contestant)
                    continue
                
                # CASE 5 → move
                super_cols_to_edit.setdefault(super_col, []).append(match)
                super_cols_to_edit.setdefault("note", []).append(contestant)

        # After all contestants:
        # Handle CASE 1: sub_class assignment
        if "sub_class" in super_cols_to_edit and super_cols_to_edit["sub_class"]:
            # Deduplicate equipment classes
            final_sub = deduplicate_classes(super_cols_to_edit["sub_class"])
            path = get_ancestral_path(final_sub)
            debug_sql("final_sub",final_sub)
            df.at[idx, "sub_class"] = final_sub
            df.at[idx, "class_path"] = path

            # Any remaining equipment classes go to notes
            rejects = [
                reject for reject in super_cols_to_edit["sub_class"]
                if reject != final_sub
            ]
            if rejects:
                super_cols_to_edit.setdefault("note", []).extend(rejects)
        else:
            # No equipment classes found
            df.at[idx, "sub_class"] = None

        # Handle CASE 5: all other super_cols (except note)
        for super_col, values in super_cols_to_edit.items():
            if super_col in ("sub_class", "note"):
                continue

            # values are just ontology matches (strings or class names)
            for match in values:
                add_to_cell(df, idx, super_col, match)

        # Handle notes (CASE 3, 4, 7, leftovers)
        if "note" in super_cols_to_edit:
            # Remove duplicates
            note_values = list(set(super_cols_to_edit["note"]))

            # Remove any values already present in other columns
            row_values = set()
            for col in df.columns:
                if col != "note":
                    val = df.at[idx, col]
                    if isinstance(val, list):
                        row_values.update(val)
                    elif val not in (None, "") and not pd.isna(val):
                        row_values.add(val)

            # Only keep note items not found elsewhere in the row
            final_notes = [v for v in note_values if v not in row_values]

            # Append to note column
            for v in final_notes:
                add_to_cell(df, idx, "note", v)

    # At end:
    print("Consider adding to Ontology:", set(not_in_ontology))
    return df
