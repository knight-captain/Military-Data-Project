from map_columns import 

canonical_columns =[
    country, #WE HAVE: the country that owns this equipment. this is in a_meta_table
    quantity, #VITAL: some tables have quantity, others had it built during cleaning from a spanned row; this will need to be cleaned
    #the following isn't as important
    origin, #might be a manufacturer or counrty (or a list of either)
    cost, # DON'T HAVE YET
    status, 
    dates, #list of dates with type, like [Commissioned: 1941/12/07, Retired: 2026/7/16]. If it looks like a date, put it with the raw_col name and combine them all 
    #ONTOLOGY STUFF
    ancestral_class, #"Equipment->[Aircraft, Smallarm, System, Vehicle, Vessel]" else: NOT_EQUIPMENT
    sub_class, #actual ontological class
    role, #mostly other_classes, specifically non-equipment ones
    capability, #for things like role 
    propulsion, #might even be in the name like SSBN's are all have a nuclear reactor
    equip_type, #THIS IS THE MAIN NAME FOR DE-DUPLICATING!!!
    other_names, #non-english names, meanings, NATO designations
    variant, #THIS IS IMPORTANT FOR quantities
    ship_name, #technically a sub-property of variant
    #THE FOLLOWING CAN TECHNICALLY BE GROUPED UNDER "dimensions" FOR NOW
    dimensions
    # weight, 
    # displacement, #technically a sub-property of weight
    # width,
    # caliber, #technically a sub-property of width
    # length,
    # range, #need new name, as this is python reserved
    # speed,
    #Relational stuff: this can sit in notes for now unless obvious
    # armament,
    # carrier,
    note
]



def classify_columns(table_classes):
    contextual_mapping = {}

    for table_name, info in table_classes.items():
        eq_class = info["equipment_class"]
        raw_cols = info["raw_cols"]
        other_classes = info["other_classes"]



        for raw_col in raw_cols:
            super_col = map_raw_col_to_super_col(
                raw_col,
                eq_class,
                other_classes
                canonical_columns
            )

            contextual_mapping[(table_name, raw_col)] = super_col

    return contextual_mapping
