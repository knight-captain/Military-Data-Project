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

    # First create nodes for cluster labels
    for key, obj in merged.items():
        parent, label = key
        nodes[label] = {
            "name": label,
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
                "name": parent,
                "parent": None,     # will be resolved later
                "tables": [],
                "strength": 1.0,
                "parent_strength": 1.0,
                "children": []
            }
    
    # Resolve parent-of-parent relationships
    for name, node in nodes.items():
        if node["tables"]:  # real cluster
            continue

        # This is a parent node; find its own parent from table headers
        # Look for any cluster whose parent == this node
        parents = []
        for key, obj in merged.items():
            p, label = key
            if label == name:
                parents.append(p)

        if parents:
            counts = Counter(parents)
            node["parent"] = counts.most_common(1)[0][0]
            
    return nodes


def link_nodes(nodes):
    roots = []

    for name, node in nodes.items():
        parent = node["parent"]

        if parent in nodes:
            # parent exists → link child to parent
            nodes[parent]["children"].append(node)
        else:
            # parent does not exist → this is a root
            roots.append(node)

    return roots

def print_tree(nodes, indent=""):
    # nodes is a list of node objects
    for node in sorted(nodes, key=lambda n: n["name"]):
        print(f"{indent}{node['name']}  "
              f"(tables={len(node['tables'])}, "
              f"strength={node['strength']:.2f}, "
              f"parent_strength={node['parent_strength']:.2f})")

        if node["children"]:
            print_tree(node["children"], indent + "    ")

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

    # Step 2: merge clusters with identical (parent, label)
    merged = {}
    for obj in clusters:
        key = (obj["parent"], obj["label"])
        if key not in merged:
            merged[key] = {
                "parent": obj["parent"],
                "label": obj["label"],
                "tables": [],
                "strength": obj["strength"],
                "parent_strength": obj["parent_strength"]
            }
        merged[key]["tables"].extend(obj["tables"])

    # Step 3: build nodes
    nodes = build_nodes(merged)

    # Step 4: link nodes into a tree
    roots = link_nodes(nodes)

    print_tree(roots, indent="")

    return roots

