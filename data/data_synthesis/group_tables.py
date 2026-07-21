import math

def cosine_similarity(table_fp, group_fp):
    """
    Compute cosine similarity between:
      - table_fp: sets + leaf_header + regex
      - group_fp: sets + leaf_headers + regex (+ optional freq)
    """

    features = set()

    # Table features
    for key in ["classes", "parent", "children", "raw_cols", "regex"]:
        features.update(table_fp.get(key, set()))
    if table_fp.get("leaf_header"):
        features.add(table_fp["leaf_header"])

    # Group features
    for key in ["classes", "parent", "children", "raw_cols", "regex"]:
        features.update(group_fp.get(key, set()))
    features.update(group_fp.get("leaf_headers", set()))

    # Frequency keys
    if "freq" in group_fp:
        for key in ["classes", "parent", "children", "raw_cols", "leaf_headers"]:
            features.update(group_fp["freq"].get(key, {}).keys())

    t_vec = []
    g_vec = []

    for feat in features:
        t_val = (
            1 if (
                feat in table_fp.get("classes", set()) or
                feat in table_fp.get("parent", set()) or
                feat in table_fp.get("children", set()) or
                feat in table_fp.get("raw_cols", set()) or
                feat in table_fp.get("regex", set()) or
                feat == table_fp.get("leaf_header")
            ) else 0
        )

        g_val = 0

        for key in ["classes", "parent", "children", "raw_cols", "regex"]:
            if feat in group_fp.get(key, set()):
                g_val += 1

        if feat in group_fp.get("leaf_headers", set()):
            g_val += 1

        if "freq" in group_fp:
            for key in ["classes", "parent", "children", "raw_cols", "leaf_headers"]:
                g_val += group_fp["freq"].get(key, {}).get(feat, 0)

        t_vec.append(t_val)
        g_vec.append(g_val)

    dot = sum(t * g for t, g in zip(t_vec, g_vec))
    norm_t = math.sqrt(sum(t * t for t in t_vec))
    norm_g = math.sqrt(sum(g * g for g in g_vec))

    if norm_t == 0 or norm_g == 0:
        return 0.0

    return dot / (norm_t * norm_g)

def find_best_group(table_fp, groups):
    best_group = None
    best_score = 0.0

    for group_name, group_obj in groups.items():
        if group_name == "Equipment":
            continue

        score = cosine_similarity(table_fp, group_obj["fingerprint"])

        if score > best_score:
            best_score = score
            best_group = group_name

    return best_group, best_score

def assign_table_to_group(table_name, best_group, score, table_classes, groups):
    """
    Assign table to a group with confidence score.
    Update table_classes and groups.
    """

    table_info = table_classes[table_name]

    # Update table info
    table_info["equipment_class"] = best_group
    table_info["confidence"] = score

    # Remove equipment class from other_classes
    table_info["other_classes"] = [
        oc for oc in table_info["other_classes"]
        if oc != best_group
    ]

    # Add table to group
    groups[best_group]["tables_included"][table_name] = table_info

