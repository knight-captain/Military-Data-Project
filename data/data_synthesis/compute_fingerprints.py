from utils.nav_tree import *

def compute_group_fingerprint(group):
    """
    Normalize group fingerprint if tables exist.
    Starter fingerprint stays intact.
    """

    tables = group["tables_included"]
    n = len(tables)

    if n == 0:
        return group["fingerprint"]

    freq = {
        "classes": {},
        "parent": {},
        "children": {},
        "raw_cols": {},
        "leaf_headers": {}
    }

    for table_name, table_info in tables.items():
        fp = compute_table_fingerprint(table_name, table_info)

        for key in ["classes", "parent", "children", "raw_cols"]:
            for item in fp[key]:
                freq[key][item] = freq[key].get(item, 0) + 1

        if fp["leaf_header"]:
            lh = fp["leaf_header"]
            freq["leaf_headers"][lh] = freq["leaf_headers"].get(lh, 0) + 1

    # Normalize
    for key in freq:
        for item in freq[key]:
            freq[key][item] /= n

    group["fingerprint"]["freq"] = freq
    return group["fingerprint"]

def compute_table_fingerprint(table_name, table_info):
    """
    Build a fingerprint for a single table.
    Uses direct parent, not ancestor.
    """

    fp = {
        "classes": set(),
        "parent": set(),
        "children": set(),
        "raw_cols": set(table_info["raw_cols"]),
        "leaf_header": table_info["leaf_header"],
        "regex": set()
    }

    eq_label = table_info["equipment_class"]
    other_labels = table_info["other_classes"]

    # 1. Equipment class
    if eq_label:
        eq_obj = get_class(eq_label)
        fp["classes"].add(eq_label)

        # DIRECT PARENT
        parent_obj = get_parent(eq_obj)
        if parent_obj:
            parent_label = parent_obj.label[0] if parent_obj.label else parent_obj.name
            fp["parent"].add(parent_label)

        # Children
        for child in get_children(eq_obj):
            child_label = child.label[0] if child.label else child.name
            fp["children"].add(child_label)

        # Regex patterns
        for pattern in get_regex(eq_obj):
            fp["regex"].add(pattern)

    # 2. Other classes
    for oc_label in other_labels:
        oc_obj = get_class(oc_label)
        fp["classes"].add(oc_label)

        parent_obj = get_parent(oc_obj)
        if parent_obj:
            parent_label = parent_obj.label[0] if parent_obj.label else parent_obj.name
            fp["parent"].add(parent_label)

        for pattern in get_regex(oc_obj):
            fp["regex"].add(pattern)

    return fp

def merge_fingerprints(group_fp, table_fp):
    """
    Merge table fingerprint into group fingerprint.
    """

    for key in ["classes", "parent", "children", "raw_cols", "regex"]:
        group_fp[key].update(table_fp[key])

    if table_fp["leaf_header"]:
        if "leaf_headers" not in group_fp:
            group_fp["leaf_headers"] = set()
        group_fp["leaf_headers"].add(table_fp["leaf_header"])
