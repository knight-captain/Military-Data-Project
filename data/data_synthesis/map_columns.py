def map_raw_col_to_super_col(raw_col, eq_class, other_classes, canonical_columns, ontology_columns):
    """
    Ontology-driven column classification.
    """

    col = raw_col.strip().lower()
    tokens = col.replace("_", " ").split()

    # 1. Get ontology-expected columns for this equipment class
    expected = ontology_columns.get(eq_class, {})

    # 2. Score each canonical column
    best_col = "note"
    best_score = 0.0

    for super_col in canonical_columns:
        # Ontology synonyms for this super_col
        synonyms = expected.get(super_col, [])

        # Compute lexical match score
        lex_score = sum(1 for t in tokens if t in synonyms)

        # Equipment-class match bonus
        class_bonus = 1.0 if super_col in expected else 0.0

        # Other-class bonus
        oc_bonus = 0.0
        for oc in other_classes:
            oc_lower = oc.lower()
            if any(s in oc_lower for s in synonyms):
                oc_bonus += 0.5

        # Total score
        score = lex_score + class_bonus + oc_bonus

        if score > best_score:
            best_score = score
            best_col = super_col

    return best_col
