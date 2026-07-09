from collections import defaultdict, Counter
from utils.normalization import singularize

STRICT_THRESHOLD = 0.5   # Higher = more groups
LOOSE_THRESHOLD  = 0.35    # Lower = merges easier
HEADER_WEIGHT = 0.4
PARENT_WEIGHT = 0.1
CAT_WEIGHT = 0.4
RAW_COL_WEIGHT = 0.1     # Higher = countries clump to themselves more since tables within the same country were likely written by the same author. Keep low!

#STEP 1
def get_raw_cols(conn, allowed_tables):
    raw_cols = defaultdict(set)
    cur = conn.cursor()

    for table in allowed_tables:
        cols = cur.execute(f"PRAGMA table_info('{table}')").fetchall()
        for _, col_name, *_ in cols:
            raw_cols[table].add(col_name.lower().strip())

    return raw_cols


#STEP 2
def build_fingerprints(table_categories_w_h234, raw_cols):
    fingerprints = {}

    for table, (classification, h2, h3, h4) in table_categories_w_h234.items():

        cats = {singularize(c.lower().strip()) for c in classification}

        # leaf header
        leaf = h4 or h3 or h2
        if leaf:
            leaf_norm = singularize(leaf.lower().strip().replace(" ", "_"))
            headers = {leaf_norm}
        else:
            headers = set()

        # parent header
        if h4:
            parent = h3 or h2
        elif h3:
            parent = h2
        else:
            parent = None

        if parent:
            parent_norm = singularize(parent.lower().strip().replace(" ", "_"))
            parents = {parent_norm}
        else:
            parents = set()

        # raw columns
        cols = {singularize(col) for col in raw_cols.get(table, set())}

        fingerprints[table] = {
            "headers": headers,
            "parents": parents,     # ALWAYS present
            "cats": cats,
            "cols": cols,
        }

    return fingerprints


#STEP 3
#for Step 3.1
def jaccard(a, b):
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)

def table_similarity(fpA, fpB):
    sim_h = jaccard(fpA["headers"], fpB["headers"])
    sim_p = jaccard(fpA["parents"], fpB["parents"])
    sim_c = jaccard(fpA["cats"],    fpB["cats"])
    sim_r = jaccard(fpA["cols"],    fpB["cols"])

    return (HEADER_WEIGHT * sim_h +
            PARENT_WEIGHT * sim_p +
            CAT_WEIGHT    * sim_c +
            RAW_COL_WEIGHT * sim_r)

#STEP 3.1
def strict_pass(fingerprints):
    tables = list(fingerprints.keys())
    clusters = []
    used = set()
    skipped = []   # tables that matched something but were not assigned yet

    for t in tables:
        if t in used:
            continue

        # start a new cluster
        cluster = [t]
        used.add(t)

        for u in tables:
            if u in used:
                continue

            sim = table_similarity(fingerprints[t], fingerprints[u])

            if sim >= STRICT_THRESHOLD:
                # this table *might* belong here, but we skip it for now
                skipped.append(u)
                used.add(u)

        clusters.append(cluster)
    print(len(clusters))
    return clusters, skipped

#for Step 3.2
def merge_fingerprints(cluster, fingerprints):
    """Union the fingerprints of all tables in a cluster."""
    merged = {
        "headers": set(),
        "parents": set(),   # <-- ADD THIS
        "cats": set(),
        "cols": set(),
    }

    for table in cluster:
        fp = fingerprints[table]
        merged["headers"] |= fp["headers"]
        merged["parents"] |= fp["parents"]   # <-- AND THIS
        merged["cats"]    |= fp["cats"]
        merged["cols"]    |= fp["cols"]

    return merged

#STEP 3.2
def assign_skipped_tables(clusters, skipped, fingerprints):
    # Build cluster fingerprints
    cluster_fps = [merge_fingerprints(cl, fingerprints) for cl in clusters]

    for table in skipped:
        fp = fingerprints[table]

        # compute similarity to each cluster
        sims = [table_similarity(fp, cfp) for cfp in cluster_fps]
        best_idx = max(range(len(sims)), key=lambda i: sims[i])
        best_sim = sims[best_idx]

        if best_sim >= LOOSE_THRESHOLD:
            clusters[best_idx].append(table)
            # update cluster fingerprint
            cluster_fps[best_idx] = merge_fingerprints(clusters[best_idx], fingerprints)
        else:
            # no good match → new cluster
            clusters.append([table])
            cluster_fps.append(fp)

    return clusters

#for step 3.0 pipe
def label_and_strength(cluster, fingerprints):
    leafs = []
    for table in cluster:
        leafs.extend(fingerprints[table]["headers"])  # leaf-only headers

    if not leafs:
        return "unknown", 0.0

    counts = Counter(leafs)
    label, freq = counts.most_common(1)[0]
    strength = freq / len(cluster)

    return label, strength

def build_cluster_objects(clusters, fingerprints):
    cluster_objects = []

    for cl in clusters:
        label, strength = label_and_strength(cl, fingerprints)
        cluster_objects.append({
            "tables": cl,
            "label": label,
            "strength": strength
        })

    return cluster_objects


#Step 3 pipe
def strategy_b_cluster(fingerprints):
    # Pass 1: strict clustering
    clusters, skipped = strict_pass(fingerprints)

    # Pass 2: best-match assignment
    clusters = assign_skipped_tables(clusters, skipped, fingerprints)

    cluster_objects = build_cluster_objects(clusters, fingerprints)

    return cluster_objects

#STEP 4
def print_clusters(cluster_objects):
    print("\n=== Table Clusters (DEBUG) ===")
    for idx, obj in enumerate(cluster_objects):
        print(f"{obj['label']}: {idx} ({len(obj['tables'])} tables) strength: {obj['strength']:.2f}")
        for t in obj["tables"][:10]:
            print("   ", t)
    print("\n=== End Clusters ===\n")

def cluster_tables(conn, table_categories_w_h234):
    allowed_tables = table_categories_w_h234.keys()
    raw_cols = get_raw_cols(conn, allowed_tables)

    fingerprints = build_fingerprints(table_categories_w_h234, raw_cols)

    # Strategy B instead of greedy_cluster
    cluster_objects = strategy_b_cluster(fingerprints)

    print_clusters(cluster_objects)
    return cluster_objects

