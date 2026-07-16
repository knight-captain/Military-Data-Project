from owlready2 import get_ontology
from owlready2.entity import ThingClass
from owlready2 import Thing

def safe_label(cls):
    if isinstance(cls, str):
        return cls
    if hasattr(cls, "label") and cls.label:
        return cls.label[0]
    return cls.name

def get_tree(path):
    """Load OWL and build a recursive dict-of-dicts representing the Equipment hierarchy."""
    onto = get_ontology(path).load()
    Equipment = onto.search_one(label="Equipment")

    def build_subtree(cls):
        children = list(cls.subclasses())
        return {safe_label(cls): {safe_label(child): build_subtree(child)[safe_label(child)] for child in children}}

    return build_subtree(Equipment)
    
def get_parent(onto_class):
    """
    Return the immediate parent OWL class (ignore restrictions).
    """
    for parent in onto_class.is_a:
        # Skip restrictions
        if not isinstance(parent, ThingClass):
            continue

        # Skip Thing (root)
        if parent is Thing:
            continue

        return parent

    return None

def get_ancestor(onto_class, depth, class_to_path):
    """
    Return ancestor at given depth using class_to_path dict.
    Depth 0 = root (Equipment, etc).
    """
    #used to find Equipment classes mostly in naive classification
    label = safe_label(onto_class)
    path = class_to_path.get(label, [])

    if depth < 0 or depth >= len(path):
        return None

    return path[depth]

def build_path(cls):
    """Build ancestry paths"""
    path = []
    current = cls
    while current:
        path.insert(0, safe_label(current))
        current = get_parent(current)
    return path

def get_children(onto_class):
    """Return immediate children of an OWL class."""
    return list(onto_class.subclasses())

def get_descendants(matches, paths):
    """
    Given multiple matched classes, collapse them to the leaf-most class
    IF they are in the same branch.

    Example:
        ["Vessel", "Warship", "Destroyer"] → ["Destroyer"]
        ["Aircraft", "Vessel"] → ["Aircraft", "Vessel"]  (different branches)
    """
    if len(matches) <= 1:
        return matches

    # Find deepest class
    leaf = max(matches, key=lambda m: len(paths[m]))

    # Determine branch root (depth 1)
    leaf_path = paths.get(leaf, [])
    if len(leaf_path) < 2:
        return matches

    branch_root = leaf_path[1]

    # Check if all classes share the same branch root
    same_branch = all(
        len(paths[m]) > 1 and paths[m][1] == branch_root
        for m in matches
    )

    if same_branch:
        return [leaf]

    return matches


def get_class(onto_class):
    regex_list = []
    if hasattr(onto_class, "hasRegex"):
        for ann in onto_class.hasRegex:
            val = str(ann)
            if val.startswith("REGEX:"):
                regex_list.append(val[len("REGEX:"):])
    return regex_list


def get_class(onto_class):
    regex_list = []
    if hasattr(onto_class, "hasRegex"):
        for ann in onto_class.hasRegex:
            val = str(ann)
            if val.startswith("REGEX:"):
                regex_list.append(val[len("REGEX:"):])
    return regex_list

def get_relationships(path):
    onto = get_ontology(path).load()
    all_ontos = list(onto.imported_ontologies) + [onto]

    onto_classes = []
    for o in all_ontos:
        onto_classes.extend(list(o.classes()))

    parents = {}
    children = {}
    rules = {}
    paths = {}

    for cls in onto_classes:
        cid = safe_label(cls)
        p = get_parent(cls)
        parents[cid] = safe_label(p) if p else None
        children[cid] = [safe_label(c) for c in get_children(cls)]
        rules[cid] = get_class(cls)

    for cls in onto_classes:
        cid = safe_label(cls)
        paths[cid] = build_path(cls)
    
    # print([p for p in onto.annotation_properties()])
    # # print(parents)
    # print(children)
    # print(rules)
    # print(paths)

    # cls = onto.search_one(label="Rifle")
    # print("Rifle class:", cls)

    return parents, children, paths, rules