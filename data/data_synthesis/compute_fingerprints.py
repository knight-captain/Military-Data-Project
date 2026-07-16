def compute_group_fingerprint(group, paths):
    """
    Build a frequency-weighted fingerprint for a group.
    Each feature gets a weight = (# tables containing feature) / (group size)
    """

    freq = {
        "classes": {},
        "ancestors": {},
        "children": {},
        "raw_cols": {},
        "leaf_headers": {}
    }

    tables = group["tables_included"]
    n = len(tables)

    if n == 0:
        group["fingerprint"] = freq
        return freq

    for table_name, table_info in tables.items():
        fp = compute_table_fingerprint(table_name, table_info, paths)

        # Count frequencies
        for key in ["classes", "ancestors", "children", "raw_cols"]:
            for item in fp[key]:
                freq[key][item] = freq[key].get(item, 0) + 1

        if fp["leaf_header"]:
            lh = fp["leaf_header"]
            freq["leaf_headers"][lh] = freq["leaf_headers"].get(lh, 0) + 1

    # Normalize frequencies
    for key in freq:
        for item in freq[key]:
            freq[key][item] /= n

    group["fingerprint"] = freq
    return freq


def compute_table_fingerprint(table_name, table_info, paths):
    """
    Build a fingerprint for a single table.
    Binary features:
      - classes
      - ancestors
      - children
      - raw_cols
      - leaf_header
    """

    fp = {
        "classes": set(),
        "ancestors": set(),
        "children": set(),
        "raw_cols": set(table_info["raw_cols"]),
        "leaf_header": table_info["leaf_header"]
    }

    eq_class = table_info["equipment_class"]
    other_classes = table_info["other_classes"]

    # 1. Equipment class
    if eq_class:
        fp["classes"].add(eq_class)

        # 2. Parent of equipment class
        if eq_class in paths and len(paths[eq_class]) > 1:
            fp["ancestors"].add(paths[eq_class][1])

        # 3. Children of equipment class
        for cls, path in paths.items():
            if len(path) > 1 and path[-2] == eq_class:
                fp["children"].add(cls)

    # 4. Other classes
    for oc in other_classes:
        fp["classes"].add(oc)

        # 5. Parents of other classes
        if oc in paths and len(paths[oc]) > 1:
            fp["ancestors"].add(paths[oc][1])

    return fp


