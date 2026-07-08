import math
import sqlite3

GROUP_THRESHOLD = 0.7
SIM_CAT_WEIGHT = 0.7
SIM_COL_WEIGHT = 1 - SIM_CAT_WEIGHT
ONTOLOGY_PENTALY = -0.3


def jaccard(a, b):
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)
    
def weighted_jaccard(colsA, colsB, weights):
    #added with compute_supercol_weights
    inter = sum(weights[c] for c in colsA & colsB)
    union = sum(weights[c] for c in colsA | colsB)
    return inter / union if union else 0.0

def ontology_penalty(catsA, catsB):
    # artillery vs aircraft → penalty
    if ("artillery" in catsA and "aircraft" in catsB) or \
       ("aircraft" in catsA and "artillery" in catsB):
        return ONTOLOGY_PENTALY
    return 0.0


def table_similarity(catsA, colsA, catsB, colsB):
    sim_cat = jaccard(catsA, catsB)
    sim_cols = jaccard(colsA, colsB)
    sim = (
        SIM_CAT_WEIGHT * sim_cat +
        SIM_COL_WEIGHT * sim_cols +
        ontology_penalty(catsA, catsB)
    )
    return sim

def compute_supercol_weights(table_supercols):
    # Count frequency of each super_col across all tables
    freq = {}
    for cols in table_supercols.values():
        for c in cols:
            freq[c] = freq.get(c, 0) + 1

    total_tables = len(table_supercols)

    # Inverse frequency weight
    weights = {}
    for c, f in freq.items():
        weights[c] = math.log(total_tables / f)

    return weights

def greedy_cluster(table_categories, table_supercols, threshold=GROUP_THRESHOLD):
    clusters = []  # list of lists of table_names
    centroids = [] # representative table for each cluster

    tables_sorted = sorted(
        table_categories.keys(),
        key=lambda t: (len(table_categories[t]), len(table_supercols[t])),
        reverse=True
    )

    for table in tables_sorted:
        catsA = table_categories[table]
        colsA = table_supercols[table]

        placed = False

        for i, centroid in enumerate(centroids):
            sim = max(
                table_similarity(catsA, colsA, table_categories[t], table_supercols[t])
                for t in clusters[i]
            )

            if sim >= threshold:
                clusters[i].append(table)
                placed = True
                break

        if not placed:
            clusters.append([table])
            centroids.append(table)

    return clusters

def load_category_expansions(path="ontology/table_regex_rules.csv"):
    expansions = {}
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            cls = row[0].strip().lower()
            kws = [r.strip().lower() for r in row[1:]]
            expansions[cls] = set(kws)
    return expansions

def expand_categories(cats, expansions):
    expanded = set(cats)
    for c in cats:
        expanded |= expansions.get(c, set())
    return expanded

def load_fingerprints(conn):
    cur = conn.cursor()

    # 1. Load categories from a_mapping_table
    cat_rows = cur.execute("""
        SELECT table_name, classification
        FROM a_mapping_table
    """).fetchall()

    table_categories = {}
    for table_name, class_str in cat_rows:
        # classification is "key:value | key:value | ..."
        cats = set()
        if class_str:
            parts = class_str.split("|")
            for p in parts:
                p = p.strip()
                if ":" in p:
                    k, v = p.split(":", 1)
                    cats.add(v.strip().lower())
        table_categories[table_name] = cats

    # 2. Load super-col signatures from a_master_equipment
    col_rows = cur.execute("PRAGMA table_info(a_master_equipment)").fetchall()
    super_cols = [r[1] for r in col_rows if r[1] not in ("table_name", "url")]

    table_supercols = {}
    rows = cur.execute("""
        SELECT table_name, *
        FROM a_master_equipment
    """).fetchall()

    for row in rows:
        table_name = row[0]
        # row[2:] corresponds to super_cols
        present = set()
        for col_name, value in zip(super_cols, row[2:]):
            if value not in (None, "", "NULL"):
                present.add(col_name.lower())
        table_supercols[table_name] = present

    return table_categories, table_supercols

def grouping_func():
    conn = sqlite3.connect("data\db\military_equipment_260707183145-SYNTHED.db")

    table_categories, table_supercols = load_fingerprints(conn)
    clusters = greedy_cluster(table_categories, table_supercols, threshold=GROUP_THRESHOLD)

    for i, cl in enumerate(clusters):
        cats = set().union(*(table_categories[t] for t in cl))
        cols = set().union(*(table_supercols[t] for t in cl))
        print(f"\nCluster {i}: {len(cl)} tables")
        print("Categories:", cats)
        print("Super-cols:", cols)
        for t in cl:
            print("   ", t)


if __name__ == "__main__":
    grouping_func()