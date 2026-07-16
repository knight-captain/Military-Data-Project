from data.data_synthesis.compute_fingerprints import compute_group_fingerprint, compute_table_fingerprint
from data.data_synthesis.group_tables import find_best_group, assign_table_to_group

def build_groups(table_classes, paths):
    """
    Build group objects for each Equipment class found in naive classification.

    groups = {
        equipment_class_name: {
            "name": equipment_class_name,
            "parent_class": parent_of_equipment_class,
            "child_classes": [],   # optional, filled later if needed
            "tables_included": { table_name: table_class_info },
            "fingerprint": {}      # computed later
        }
    }
    """

    groups = {}

    # 1. Identify all Equipment classes from naive classification
    for table_name, info in table_classes.items():
        eq_class = info["equipment_class"]

        # Only create groups for real Equipment subclasses
        if eq_class is None:
            continue

        # Create group if not already present
        if eq_class not in groups:
            parent = None
            # Use paths to find parent: ancestor at depth 1
            if eq_class in paths and len(paths[eq_class]) > 1:
                parent = paths[eq_class][1]

            groups[eq_class] = {
                "name": eq_class,
                "parent_class": parent,
                "child_classes": [],        # optional, fill later
                "tables_included": {},      # table_name -> table_class_info
                "fingerprint": {}           # computed later
            }

        # Add table to this group
        groups[eq_class]["tables_included"][table_name] = info
    
    # for g, obj in groups.items():
    #     print(g, len(obj["tables_included"]))

    return groups

def classify_advanced(table_classes, paths):
    """
    Advanced classification:
      - Build groups from naive equipment classes
      - Compute group fingerprints
      - Compute table fingerprints
      - Iteratively assign unclassified tables to best groups
    """

    # 1. Build groups from naive equipment classes
    groups = build_groups(table_classes, paths)

    # 2. Compute fingerprints for each group
    for group_name, group_obj in groups.items():
        compute_group_fingerprint(group_obj, paths)

    # 3. Collect tables needing advanced classification
    waiting = [
        table_name
        for table_name, info in table_classes.items()
        if info["equipment_class"] is None
    ]

    # 4. Iterative assignment loop
    threshold = 0.9
    while waiting and threshold >= 0.1:
        newly_assigned = []

        for table_name in waiting:
            table_info = table_classes[table_name]

            # Compute table fingerprint
            table_fp = compute_table_fingerprint(table_name, table_info, paths)

            # Find best matching group
            best_group_name, score = find_best_group(table_fp, groups)

            # Assign if similarity is high enough
            if score >= threshold:
                assign_table_to_group(
                    table_name,
                    best_group_name,
                    score,
                    table_classes,
                    groups
                )
                newly_assigned.append(table_name)

                # Recompute fingerprint for the updated group
                compute_group_fingerprint(groups[best_group_name], paths)

        # Remove assigned tables from waiting list
        waiting = [t for t in waiting if t not in newly_assigned]

        # Lower threshold
        threshold -= 0.1

    return table_classes