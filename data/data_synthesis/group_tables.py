
import math

def cosine_similarity(table_fp, group_fp):
    """
    Compute cosine similarity between a table fingerprint (binary)
    and a group fingerprint (frequency-weighted).
    """

    # Build unified feature set
    features = set()
    for key in ["classes", "ancestors", "children", "raw_cols", "leaf_headers"]:
        if key in table_fp:
            features.update(table_fp[key])
        if key in group_fp:
            features.update(group_fp[key].keys())

    # Build vectors
    t_vec = []
    g_vec = []

    for feat in features:
        # Table vector: 1 if feature present, else 0
        t_val = (
            1 if (
                feat in table_fp.get("classes", set()) or
                feat in table_fp.get("ancestors", set()) or
                feat in table_fp.get("children", set()) or
                feat in table_fp.get("raw_cols", set()) or
                feat == table_fp.get("leaf_header")
            ) else 0
        )

        # Group vector: frequency if present, else 0
        g_val = (
            group_fp["classes"].get(feat, 0) +
            group_fp["ancestors"].get(feat, 0) +
            group_fp["children"].get(feat, 0) +
            group_fp["raw_cols"].get(feat, 0) +
            group_fp["leaf_headers"].get(feat, 0)
        )

        t_vec.append(t_val)
        g_vec.append(g_val)

    # Compute cosine similarity
    dot = sum(t * g for t, g in zip(t_vec, g_vec))
    norm_t = math.sqrt(sum(t * t for t in t_vec))
    norm_g = math.sqrt(sum(g * g for g in g_vec))

    if norm_t == 0 or norm_g == 0:
        return 0.0

    return dot / (norm_t * norm_g)

def find_best_group(table_fp, groups):
    """
    Return (best_group_name, best_score)
    """

    best_group = None
    best_score = 0.0

    for group_name, group_obj in groups.items():
        group_fp = group_obj["fingerprint"]
        score = cosine_similarity(table_fp, group_fp)

        if score > best_score:
            best_score = score
            best_group = group_name

    return best_group, best_score

def assign_table_to_group(table_name, best_group, score, table_classes, groups):
    """
    Assign table to a group with confidence score.
    Update table_classes and groups.
    """

    # Update table info
    table_info = table_classes[table_name]
    table_info["equipment_class"] = best_group
    table_info["confidence"] = score

    # Remove equipment class from other_classes if present
    table_info["other_classes"] = [
        oc for oc in table_info["other_classes"]
        if oc != best_group
    ]

    # Add table to group
    groups[best_group]["tables_included"][table_name] = table_info
