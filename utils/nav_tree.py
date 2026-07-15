from owlready2 import get_ontology

def get_tree(path):
    """
    Load OWL and build a recursive dict-of-dicts representing the Equipment hierarchy.
    """
    onto = get_ontology(path).load()

    # Find the Equipment root class
    Equipment = onto.search_one(iri="*Equipment")

    def build_subtree(cls):
        children = [c for c in cls.subclasses()]
        return {cls.name: {child.name: build_subtree(child)[child.name] for child in children}}

    return build_subtree(Equipment)
    
def get_parent(onto_class):
    """
    Return the immediate parent of an OWL class.
    """
    if not onto_class.is_a:
        return None

    # First parent that is a class (not restrictions)
    for parent in onto_class.is_a:
        if hasattr(parent, "label[0]"):
            return parent
    return None

def get_ancestor(onto_class, depth, class_to_path):
    """
    Return ancestor at given depth using class_to_path dict.
    """
    path = class_to_path.get(onto_class.label[0], [])
    if depth < 0 or depth >= len(path):
        return None
    return path[depth]

def build_path(cls):
    # Build ancestry paths
    path = []
    current = cls
    while current:
        path.insert(0, current.label[0])
        current = get_parent(current)
    return path

def get_children(onto_class):
    """
    Return immediate children of an OWL class.
    """
    return list(onto_class.subclasses())

def get_descendant(onto_classes, class_to_path):
    """
    Return the leaf-most class from a list of OWL classes.
    """
    # Compare path lengths
    return max(onto_classes, key=lambda cls: len(class_to_path.get(cls.label[0], [])))

def get_class(onto_class):
    regex_list = []

    # Owlready2 exposes annotation properties as attributes
    for prop_name in ("hasRegex", "hasRegex_1"):
        if hasattr(onto_class, prop_name):
            for ann in getattr(onto_class, prop_name):
                val = str(ann)
                if val.startswith("REGEX:"):
                    regex_list.append(val[len("REGEX:"):])

    return regex_list


def cls_id(cls):
    # Use rdfs:label if present, fallback to name
    return cls.label[0] if cls.label else cls.name

def get_relationships(path):
    onto = get_ontology(path).load()

    # Load ALL ontologies inside the file
    all_ontos = list(onto.imported_ontologies) + [onto]

    onto_classes = []
    for o in all_ontos:
        onto_classes.extend(list(o.classes()))

    for o in all_ontos:
        print("Ontology:", o.base_iri)
        print("Classes:", [str(c.label[0]) if c.label else c.name for c in o.classes()])

    parents = {}
    children = {}
    rules = {}
    paths = {}

    def cls_id(cls):
        return str(cls.label[0]) if cls.label else cls.name

    for cls in onto_classes:
        cid = cls_id(cls)

        p = get_parent(cls)
        parents[cid] = cls_id(p) if p else None

        children[cid] = [cls_id(c) for c in get_children(cls)]

        rules[cid] = get_class(cls)   # FIXED

    def build_path(cls):
        path = []
        current = cls
        while current:
            path.insert(0, cls_id(current))
            current = get_parent(current)
        return path

    for cls in onto_classes:
        cid = cls_id(cls)
        paths[cid] = build_path(cls)

    # print(rules)
    # print(parents)

    return parents, children, paths, rules



