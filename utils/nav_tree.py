from owlready2 import get_ontology, ThingClass

_ONTO = None
_CLASS_INDEX = {}      # label/name -> class
_PARENTS = {}          # class -> parent class (single, for now)
_CHILDREN = {}         # class -> list of children
_REGEX = {}            # class -> list of regex strings


def _create_tree(path="ontology/Military_Ontology.owl"):
    global _ONTO, _CLASS_INDEX, _PARENTS, _CHILDREN, _REGEX
    if _ONTO is not None:
        return

    print("Building ontology tree...")
    _ONTO = get_ontology(path).load()
    all_ontos = list(_ONTO.imported_ontologies) + [_ONTO]

    # Index classes
    for onto in all_ontos:
        for cls in onto.classes():
            label = cls.label[0] if getattr(cls, "label", []) else cls.name
            _CLASS_INDEX[label] = cls

    # Build parent/children maps
    for cls in _CLASS_INDEX.values():
        children = list(cls.subclasses())
        _CHILDREN[cls] = children
        for child in children:
            _PARENTS[child] = cls

    # Build regex map
    for cls in _CLASS_INDEX.values():
        regex_list = []
        if hasattr(cls, "hasRegex"):
            for ann in cls.hasRegex:
                val = str(ann)
                if val.startswith("REGEX:"):
                    regex_list.append(val[len("REGEX:"):])
        _REGEX[cls] = regex_list

    print("Loaded classes:", len(_CLASS_INDEX))

def get_class(input_, warn=False):
    _create_tree()  # ensure tree exists

    if not isinstance(input_, str):
        return input_

    cls = _CLASS_INDEX.get(input_)
    if cls is None and warn:
        print(f"[NAV WARNING] Class '{input_}' not found in ontology")
    return cls


def get_all_classes():
    _create_tree()
    return list(_CLASS_INDEX.values())

def get_all_class_labels():
    _create_tree()
    return list(_CLASS_INDEX.keys())

def get_all_ontology_entities():
    """
    Return all ontology classes + object properties + data properties.
    """
    _create_tree()

    entities = []
    # Classes
    entities.extend(_CLASS_INDEX.values())
    # Object properties
    for prop in _ONTO.object_properties():
        entities.append(prop)
    # Data properties
    for prop in _ONTO.data_properties():
        entities.append(prop)

    return entities


def get_parent(input_):
    _create_tree()
    cls = get_class(input_,True)
    if cls is None:
        return None
    return _PARENTS.get(cls)


def get_children(input_):
    _create_tree()
    cls = get_class(input_,True)
    if cls is None:
        return []
    return _CHILDREN.get(cls, [])

def get_ancestor(input_, depth_from_root):
    """
    depth_from_root:
      0 = root ("Equipment")
      1 = first-level ("Aircraft", "Vessel", etc.)
      ...
    """
    _create_tree()
    cls = get_class(input_,True)
    if cls is None:
        return None

    # Build full path from root to cls
    path = []
    current = cls
    while current is not None:
        path.insert(0, current)
        current = _PARENTS.get(current)

    if depth_from_root < 0 or depth_from_root >= len(path):
        return None
    return path[depth_from_root]

def get_descendants(inputs):
    """
    Given a list of class labels/names, return only the leaf-most ones
    when they share a path.
    """
    _create_tree()
    classes = [get_class(i) for i in inputs if get_class(i) is not None]

    # Build paths for each class
    paths = {}
    for cls in classes:
        path = []
        current = cls
        while current is not None:
            path.insert(0, current)
            current = _PARENTS.get(current)
        paths[cls] = path

    # Remove ancestors if a descendant is also present
    leaf_classes = []
    for cls in classes:
        path = paths[cls]
        # if any other class is deeper on same path, skip this one
        if any(
            (other in path) and (paths[other].index(other) > path.index(cls))
            for other in classes
            if other is not cls
        ):
            continue
        leaf_classes.append(cls)

    # Return labels
    return [c.label[0] if getattr(c, "label", []) else c.name for c in leaf_classes]

def get_regex(entity):
    patterns = []

    # Case 1: direct attribute (Owlready2 annotation)
    if hasattr(entity, "hasRegex"):
        for val in entity.hasRegex:
            val = str(val).strip()
            if val.lower().startswith("regex:"):
                patterns.append(val[6:].strip())
            else:
                patterns.append(val)

    # # Case 2: regex stored inside super_col
    # if hasattr(entity, "super_col"):
    #     for val in entity.super_col:
    #         val = str(val).strip()
    #         if val.lower().startswith("regex:"):
    #             patterns.append(val[6:].strip())

    return patterns

def get_super_col(entity):
    if hasattr(entity, "super_col"):
        for val in entity.super_col:
            val = str(val).strip()
            if not val.lower().startswith("regex:"):
                return val
    return None

def get_property(name):
    """
    Return an ontology object or data property by its name.
    """
    # Object properties
    for prop in _ONTO.object_properties():
        if prop.name == name:
            return prop

    # Data properties
    for prop in _ONTO.data_properties():
        if prop.name == name:
            return prop

    return None

def get_all_properties_of_class(cls):
    """
    Return all object + data properties applicable to a class,
    including inherited ones.
    """
    if not isinstance(cls, ThingClass):
        return []

    try:
        return list(cls.get_properties())
    except Exception:
        return []
