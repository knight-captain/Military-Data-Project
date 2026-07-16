from utils.jaccard_idx import calc_diff

def build_table_to_cluster(nodes):
    table_to_cluster = {}
    for node in nodes.values():
        for t in node.get("tables", []):
            table_to_cluster[t] = node
    return table_to_cluster

def build_cluster_name_fingerprints(nodes, fingerprints):
    cluster_name_fps = {}

    for name, node in nodes.items():
        cluster_name = node["cluster_name"]
        rep_fp = None

        # find a table whose leaf header matches the cluster_name
        for t in node.get("tables", []):
            if cluster_name in fingerprints[t]["headers"]:
                rep_fp = fingerprints[t]
                break

        # fallback: use first table in node
        if rep_fp is None and node.get("tables"):
            rep_fp = fingerprints[node["tables"][0]]

        cluster_name_fps[cluster_name] = rep_fp

    return cluster_name_fps


def calculate_confidence(fingerprints, nodes):
    table_to_cluster = build_table_to_cluster(nodes)
    cluster_name_fps = build_cluster_name_fingerprints(nodes, fingerprints)

    new_table_categories = {}

    for table, fp in fingerprints.items():
        node = table_to_cluster.get(table)
        if node is None:
            continue

        cluster_name = node["cluster_name"]     # FIXED
        cluster_fp = cluster_name_fps[cluster_name]

        conf = calc_diff(fp, cluster_fp)

        new_table_categories[table] = (cluster_name, conf)

    print("FROM calc_conf")
    print(f"table_to_cluster: {len(table_to_cluster)}")
    print(f"cluster_name_fps: {len(cluster_name_fps)}")
    # print(cluster_name_fps)
    print("missing_fps:", sum(1 for fp in cluster_name_fps.values() if fp is None))

    return new_table_categories
 

