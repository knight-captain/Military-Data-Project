from owlready2 import get_ontology, ThingClass, ObjectProperty, DataProperty

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

def get_name(entity):
    """
    Normalize any ontology entity (class, individual, or string)
    into a SQL-safe string name/label.
    """
    # Already a string → return as-is
    if isinstance(entity, str):
        return entity

    # OWL class or individual with label
    if hasattr(entity, "label") and entity.label:
        return entity.label[0]

    # OWL class or individual with name
    if hasattr(entity, "name"):
        return entity.name

    # Fallback
    return str(entity)


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

def get_ancestral_path(input_):
    """
    i.e. Equipment>Aircraft>FixedWing
      ...
    """
    _create_tree()
    cls = get_class(input_,True)
    if cls is None:
        return None

    # Build full path from root to cls
    path = []
    target = get_name(cls)
    for depth in range(0, 10):
        ancestor = get_ancestor(cls, depth)  # pass the class, not the name
        if ancestor is None:
            break
        name = get_name(ancestor)
        path.append(name)
        if name == target:
            return ">".join(path)

    return None

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
    """
    Return the super_col annotation for a property or class.
    Assumes super_col contains only meaningful column names.
    """
    if hasattr(entity, "super_col"):
        for val in entity.super_col:
            return str(val).strip()
    return None


def get_property(entity):
    """
    Return the ontology property object associated with `entity`.

    Accepts:
      - property object
      - property name (string)
      - class (EquipMission sub-class)
      - class name (EquipMission sub-class string)

    Returns:
      - ontology property object
      - None if no property exists
    """

    # 1. If entity is already a property object
    if isinstance(entity, ObjectProperty) or isinstance(entity, DataProperty):
        return entity

    # 2. If entity is a string, try resolving it to a property first
    if isinstance(entity, str):
        # Try object properties
        for prop in _ONTO.object_properties():
            if prop.name == entity:
                return prop

        # Try data properties
        for prop in _ONTO.data_properties():
            if prop.name == entity:
                return prop

        # Try resolving string to a class
        cls = get_class(entity, warn=False)
        if cls is None:
            return None
        entity = cls  # continue as class

    # 3. If entity is a class, check if it has a property annotation
    if hasattr(entity, "hasProperty"):
        # Ontology annotation: class → property
        for ann in entity.hasProperty:
            # ann is something like "HasRole"
            # resolve it to a property object
            prop = get_property(str(ann))
            if prop is not None:
                return prop

    # 4. No property found
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
