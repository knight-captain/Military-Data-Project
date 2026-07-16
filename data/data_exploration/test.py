from owlready2 import *
import xml.etree.ElementTree as ET
import re
from pathlib import Path

SRC = Path("ontology/Military_Ontology.txt")
OUT = Path("ontology/Military_Ontology_clean.owl")

BASE = "http://military.org/ontology#"


ns = {
    "rdf":  "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "owl":  "http://www.w3.org/2002/07/owl#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "u25":  "http://www.semanticweb.org/mckay/ontologies/2026/6/untitled-ontology-25#",
}

tree = ET.parse(SRC)
root = tree.getroot()

# ---------------------------
# 1. Extract Classes
# ---------------------------
classes = {}

for cls in root.findall("owl:Class", ns):
    old_iri = cls.attrib.get(f"{{{ns['rdf']}}}about")
    if not old_iri:
        continue

    label_el = cls.find("rdfs:label", ns)
    label = label_el.text.strip() if label_el is not None else None

    parent_el = cls.find("rdfs:subClassOf", ns)
    parent_iri = parent_el.attrib.get(f"{{{ns['rdf']}}}resource") if parent_el is not None else None

    regex_el = None
    for child in cls:
        if child.tag.endswith("OWLAnnotationProperty_ffc7ead9_0a40_4c6a_9671_d089282131ac"):
            regex_el = child
            break

    regex = None
    if regex_el is not None and regex_el.text:
        regex = "REGEX:" + regex_el.text.strip()

    classes[old_iri] = {
        "label": label,
        "parent": parent_iri,
        "regex": regex,
    }

# ---------------------------
# 2. Extract Object Properties
# ---------------------------
obj_props = {}

for prop in root.findall("owl:ObjectProperty", ns):
    iri = prop.attrib.get(f"{{{ns['rdf']}}}about")
    label_el = prop.find("rdfs:label", ns)
    label = label_el.text.strip() if label_el is not None else None

    domain_el = prop.find("rdfs:domain", ns)
    domain = domain_el.attrib.get(f"{{{ns['rdf']}}}resource") if domain_el is not None else None

    range_el = prop.find("rdfs:range", ns)
    range_ = range_el.attrib.get(f"{{{ns['rdf']}}}resource") if range_el is not None else None

    types = [t.attrib.get(f"{{{ns['rdf']}}}resource") for t in prop.findall("rdf:type", ns)]

    obj_props[iri] = {
        "label": label,
        "domain": domain,
        "range": range_,
        "types": types,
    }

# ---------------------------
# 3. Extract Data Properties
# ---------------------------
data_props = {}

for prop in root.findall("owl:DatatypeProperty", ns):
    iri = prop.attrib.get(f"{{{ns['rdf']}}}about")
    label_el = prop.find("rdfs:label", ns)
    label = label_el.text.strip() if label_el is not None else None

    domain_el = prop.find("rdfs:domain", ns)
    domain = domain_el.attrib.get(f"{{{ns['rdf']}}}resource") if domain_el is not None else None

    range_el = prop.find("rdfs:range", ns)
    range_ = range_el.attrib.get(f"{{{ns['rdf']}}}resource") if range_el is not None else None

    types = [t.attrib.get(f"{{{ns['rdf']}}}resource") for t in prop.findall("rdf:type", ns)]

    data_props[iri] = {
        "label": label,
        "domain": domain,
        "range": range_,
        "types": types,
    }

# ---------------------------
# 4. Build Clean Ontology
# ---------------------------
onto = get_ontology(BASE)

XSD = onto.world.get_ontology("http://www.w3.org/2001/XMLSchema#")


def proper_case(label):
    if not label:
        return None
    label = re.sub(r"[^A-Za-z0-9]", "_", label)
    return label[0].upper() + label[1:]

with onto:
    class hasRegex(AnnotationProperty):
        pass

    iri_to_class = {}

    # Create classes
    for old_iri, info in classes.items():
        name = proper_case(info["label"])
        if not name:
            continue
        cls = type(name, (Thing,), {})
        iri_to_class[old_iri] = cls

    # Set parents
    for old_iri, info in classes.items():
        cls = iri_to_class[old_iri]
        parent_iri = info["parent"]
        if parent_iri and parent_iri in iri_to_class:
            cls.is_a = [iri_to_class[parent_iri]]
        else:
            cls.is_a = [Thing]

    # Attach regex
    for old_iri, info in classes.items():
        if info["regex"]:
            iri_to_class[old_iri].hasRegex.append(info["regex"])

    # Create Object Properties
    for iri, info in obj_props.items():
        name = proper_case(info["label"])
        if not name:
            continue

        prop = type(name, (ObjectProperty,), {})

        # domain
        if info["domain"] in iri_to_class:
            prop.domain = [iri_to_class[info["domain"]]]

        # range
        if info["range"] in iri_to_class:
            prop.range = [iri_to_class[info["range"]]]

        # characteristics
        bases = [ObjectProperty]

        for t in info["types"]:
            if t.endswith("#FunctionalProperty"):
                bases.append(FunctionalProperty)
            if t.endswith("#InverseFunctionalProperty"):
                bases.append(InverseFunctionalProperty)
            if t.endswith("#TransitiveProperty"):
                bases.append(TransitiveProperty)
            if t.endswith("#SymmetricProperty"):
                bases.append(SymmetricProperty)
            if t.endswith("#AsymmetricProperty"):
                bases.append(AsymmetricProperty)
            if t.endswith("#ReflexiveProperty"):
                bases.append(ReflexiveProperty)
            if t.endswith("#IrreflexiveProperty"):
                bases.append(IrreflexiveProperty)

        prop = type(name, tuple(bases), {})


    # Create Data Properties
    for iri, info in data_props.items():
        name = proper_case(info["label"])
        if not name:
            continue

        prop = type(name, (DataProperty,), {})

        if info["domain"] in iri_to_class:
            prop.domain = [iri_to_class[info["domain"]]]

        def map_datatype(iri):
            if iri is None:
                return None
            iri = iri.lower()

            if iri.endswith("#string"):
                return XSD.string
            if iri.endswith("#integer"):
                return XSD.integer
            if iri.endswith("#float"):
                return XSD.float
            if iri.endswith("#boolean"):
                return XSD.boolean
            if iri.endswith("#double"):
                return XSD.double
            if iri.endswith("#date"):
                return XSD.date
            if iri.endswith("#datetime"):
                return XSD.dateTime

            return None


        dt = map_datatype(info["range"])
        if dt:
            prop.range = [dt]

        for t in info["types"]:
            if t == "http://www.w3.org/2002/07/owl#FunctionalProperty":
                prop.is_functional = True

onto.save(file=str(OUT), format="rdfxml")
print("Clean ontology written:", OUT)
