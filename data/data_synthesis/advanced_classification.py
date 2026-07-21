from data.data_synthesis.compute_fingerprints import *
from data.data_synthesis.group_tables import find_best_group, assign_table_to_group
from utils.nav_tree import *

def build_groups(table_classes):
    groups = {}

    equipment_root = get_class("Equipment")

    # Collect all classes
    def collect_all(cls_obj, out):
        out.add(cls_obj)
        for child in get_children(cls_obj):
            collect_all(child, out)

    all_equipment_classes = set()
    collect_all(equipment_root, all_equipment_classes)

    # Helper: direct parent
    def get_parent(cls_obj):
        for candidate in all_equipment_classes:
            if cls_obj in get_children(candidate):
                return candidate
        return None

    # Build groups
    for cls in all_equipment_classes:
        label = cls.label[0] if cls.label else cls.name

        parent_obj = get_parent(cls)
        parent_label = (
            parent_obj.label[0] if parent_obj and parent_obj.label else
            parent_obj.name if parent_obj else None
        )

        children = [
            child.label[0] if child.label else child.name
            for child in get_children(cls)
        ]

        regex_patterns = get_regex(cls)

        starter_fp = {
            "classes": {label},
            "parent": {parent_label} if parent_label else set(),
            "children": set(children),
            "raw_cols": set(),
            "leaf_headers": set(),
            "regex": set(regex_patterns)
        }

        groups[label] = {
            "name": label,
            "class_obj": cls,
            "parent_class": parent_label,
            "parent_class_obj": parent_obj,
            "child_classes": children,
            "tables_included": {},
            "fingerprint": starter_fp
        }

    return groups


def classify_advanced(table_classes):
    """
    Advanced classification:
      - Build groups for ALL ontology equipment classes
      - Compute table fingerprints
      - Use starter fingerprints for groups
      - Iteratively assign tables based on similarity threshold
    """

    # 1. Build groups (starter fingerprints only)
    groups = build_groups(table_classes)

    # 2. Compute table fingerprints for ALL tables
    table_fps = {}
    for table_name, info in table_classes.items():
        table_fps[table_name] = compute_table_fingerprint(table_name, info)

    # 3. ALL tables start in waiting list
    waiting = list(table_classes.keys())

    # 4. Threshold loop: start at 1.0
    threshold = 1.0
    while waiting and threshold >= 0.1:
        newly_assigned = []

        for table_name in waiting:
            table_fp = table_fps[table_name]

            # Find best matching group
            if table_classes[table_name]["confidence"] == 1.0:
                #assign
                best_group_label = table_classes[table_name]["equipment_class"]
                score = 1.0
            else:
                best_group_label, score = find_best_group(table_fp, groups)

            # Assign if similarity is high enough
            if score >= threshold:
                assign_table_to_group(
                    table_name,
                    best_group_label,
                    score,
                    table_classes,
                    groups
                )
                newly_assigned.append(table_name)

                # Merge table fingerprint into group fingerprint
                merge_fingerprints(groups[best_group_label]["fingerprint"], table_fp)

        # Remove assigned tables
        waiting = [t for t in waiting if t not in newly_assigned]

        if threshold <= 0.2 and waiting:
            print(f"Consider adding the following to the Ontology: {waiting}")

        threshold -= 0.2
        print(f"Tables remaining to classify: {len(waiting)}")

    return table_classes
