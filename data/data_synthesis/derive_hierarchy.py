from collections import defaultdict, Counter
from utils.normalization import singularize

def extract_leaf_parent(h2, h3, h4):
    # leaf = deepest header
    leaf = None
    for h in (h4, h3, h2):
        if h:
            leaf = singularize(h.lower().strip().replace(" ", "_"))

    # parent = next-deepest header
    parent = None
    if h4 and h3:
        parent = singularize(h3.lower().strip().replace(" ", "_"))
    elif h3 and h2:
        parent = singularize(h2.lower().strip().replace(" ", "_"))
    elif h2:
        parent = singularize(h2.lower().strip().replace(" ", "_"))

    return leaf, parent

def build_nodes(merged):
    nodes = {}

    # First create nodes for cluster cluster_name
    for key, obj in merged.items():
        parent, cluster_name = key
        nodes[cluster_name] = {
            "cluster_name": cluster_name,
            "parent": parent,
            "tables": obj["tables"],
            "strength": obj["strength"],
            "parent_strength": obj["parent_strength"],
            "children": []
        }

    # Now ensure parent nodes exist too
    for key, obj in merged.items():
        parent = obj["parent"]
        if parent not in nodes:
            nodes[parent] = {
                "cluster_name": parent,   # use parent as its own cluster_name
                "parent": None,
                "tables": [],
                "strength": 1.0,
                "parent_strength": 1.0,
                "children": []
            }

    # Resolve parent-of-parent relationships
    for cluster_name, node in nodes.items():
        if node["tables"]:
            continue  # this will skip synthetic nodes with empty table lists

        parents = []
        for key, obj in merged.items():
            p, child_name = key
            if child_name == cluster_name:   # child’s parent is this node
                parents.append(p)

        if parents:
            counts = Counter(parents)
            node["parent"] = counts.most_common(1)[0][0]

    return nodes

def link_nodes(nodes):
    roots = []

    for cluster_name, node in nodes.items():
        parent = node["parent"]

        # avoid self-parent
        if parent == cluster_name:
            parent = None
            node["parent"] = None

        if parent in nodes:
            nodes[parent]["children"].append(node)
        else:
            roots.append(node)

    return roots

def prune_singleton_parents(raw_roots):
    roots = list(raw_roots)
    changed = True

    while changed:
        changed = False
        stack = list(roots)

        while stack:
            node = stack.pop()
            stack.extend(node["children"])

            if node["tables"]:
                continue

            if len(node["children"]) == 1:
                child = node["children"][0]
                child["parent"] = node["parent"]

                # Replace node with child in the tree ONLY
                if node["parent"] is None:
                    roots.remove(node)
                    roots.append(child)
                else:
                    parent = find_node_by_name(roots, node["parent"])
                    parent["children"] = [
                        child if c is node else c
                        for c in parent["children"]
                    ]

                changed = True
                break

    return roots

def promote_unreachable_nodes(roots, nodes):
    reachable = set()

    def walk(node):
        stack = [node]
        while stack:
            n = stack.pop()
            reachable.add(n["cluster_name"])
            stack.extend(n["children"])

    for r in roots:
        walk(r)

    # Build new_nodes: copy nodes so we can modify safely
    new_nodes = {name: dict(node) for name, node in nodes.items()}

    # Promote unreachable nodes
    for name, node in nodes.items():
        if name not in reachable:
            new_nodes[name]["parent"] = None

    return new_nodes


def print_tree(nodes, indent=""):
    # nodes is a list of node objects
    for node in sorted(nodes, key=lambda n: n["cluster_name"]):
        print(f"{indent}{node['cluster_name']}  "
              f"(tables={len(node['tables'])}, "
              f"strength={node['strength']:.2f}, "
              f"parent_strength={node['parent_strength']:.2f})")

        if node["children"]:
            print_tree(node["children"], indent+"\t")

def derive_hierarchy(conn, clusters, table_categories_w_h234):
    # Step 1: collect parent headers for each cluster
    for obj in clusters:
        parents = []
        for table in obj["tables"]:
            classification, h2, h3, h4 = table_categories_w_h234[table]
            leaf, parent = extract_leaf_parent(h2, h3, h4)
            if parent:
                parents.append(parent)

        if parents:
            counts = Counter(parents)
            parent, freq = counts.most_common(1)[0]
            parent_strength = freq / len(parents)
        else:
            parent = "root"
            parent_strength = 0.0

        obj["parent"] = parent
        obj["parent_strength"] = parent_strength

    # Step 2: merge clusters with identical (parent, cluster_name)
    merged = {}
    for obj in clusters:
        key = (obj["parent"], obj["cluster_name"])
        if key not in merged: 
            merged[key] = {
                "parent": obj["parent"],
                "cluster_name": obj["cluster_name"],
                "tables": [],
                "strength": obj["strength"],
                "parent_strength": obj["parent_strength"]
            }
        merged[key]["tables"].extend(obj["tables"])

    # Step 3: build nodes
    nodes = build_nodes(merged) #dict of dicts
    raw_roots = link_nodes(nodes) #returns list

    # Step 4: prune useless parents and promote orphans
    pruned_roots = prune_singleton_parents(raw_roots) #accepts list, returns cleaned list
    new_nodes = promote_unreachable_nodes(pruned_roots, nodes) #accepts list, dict of dicts, updates nodes
    roots = link_nodes(new_nodes) #don't really need to rebuild the tree, as we don't use it after this unless it's to print, but it's fun

    print_tree(roots, indent="")
    print("FROM hierarchy")
    print(f"nodes: {len(nodes)}")
    # print(f"raw_roots/roots: {len(raw_roots)}/{len(roots)}")

    return new_nodes # no longer roots list of nodes

