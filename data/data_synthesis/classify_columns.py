from data.data_synthesis.column_classification_helper import *
from utils.execute_SQL import build_mapping_table

CANONICAL_COLUMNS = [
	"country", #WE HAVE: the country that owns this equipment. this is in a_meta_table
	"quantity", #VITAL: some tables have quantity, others had it built during cleaning from a spanned row; this will need to be cleaned
	#the following isn't as important
	"origin", #might be a manufacturer or counrty (or a list of either)
	"cost", # DON'T HAVE YET
	"dates", #list of dates with type, like [Commissioned: 1941/12/07, Retired: 2026/7/16]. If it looks like a date, put it with the raw_col name and combine them all 
	"status", 
	#ONTOLOGY STUFF
	"ancestral_class", #"Equipment->[Aircraft, Smallarm, System, Vehicle, Vessel]" else: NOT_EQUIPMENT = 
	"sub_class", #actual ontological class as well as "section" raw_col from merged/repeaded rows
	"role", #mostly other_classes, specifically non-equipment ones
	"capability", #for things like role 
	"propulsion", #might even be in the name like SSBN's are all have a nuclear reactor
	"equip_type", #THIS IS THE MAIN NAME FOR DE-DUPLICATING!!!
	"other_names", #non-english names, meanings, NATO designations
	"variant", #THIS IS IMPORTANT FOR quantities
	"ship_name", #technically a sub-property of variant
	#THE FOLLOWING CAN TECHNICALLY BE GROUPED UNDER "dimensions" FOR NOW
	"dimensions",
	"weight", 
	"displacement", #technically a sub-property of weight
	"width",
	"caliber", #technically a sub-property of width
	"length",
	"range", #need new name, as this is python reserved
	"speed",
	#Relational stuff: this can sit in notes for now unless obvious
	"armament",
	"carrier",
	"note"
	]  # your list


def classify_columns(conn, table_classes):
	"""
	Pipeline: classify raw columns into canonical super-columns
	Output:
		contextual_mapping = {
			table_name: {
				"super_col": [],
				...
			}
		}
		super_cols_list = [...] 
	"""

	# 0. Initialize data structures
	'''
	contextual_mapping = dict of dicts:
	  table_name -> {super_col: []}
	canonical_columns = your fixed list
	ontology_columns = optional: expectedColumns per class (later)
	'''

	contextual_mapping = {}
	super_cols_list = CANONICAL_COLUMNS #to clean out notes and stale super_cols
	# ontology_columns = {}      # TODO: load expectedColumns from ontology

	for table_name, info in table_classes.items():

		# 1. For each table, initialize empty super_col buckets
		contextual_mapping[table_name] = {col: [] for col in super_cols_list}

		raw_cols = info["raw_cols"]

		# 2. Assign known non-raw-col values (from classify_tables)
		'''
		These come from earlier pipeline stages:
		- country
		- ancestral_class (equipment sub_class)
		- sub_class (leaf ontological class)
		'''
		table_metadata = {
			"country": table_classes[table_name]["country"],
			"ancestral_class": table_classes[table_name]["ancestral_class"],
			"sub_class": table_classes[table_name]["equipment_class"],
		}
		contextual_mapping[table_name]["__metadata__"] = table_metadata


		# 3. Assign raw_cols that match canonical columns directly
		'''		
		Strategy:
		- regex
		''' 	
		column_matches = []
		for raw_col in raw_cols:
			column_matches = classify_raw_col(raw_col)
			if len(column_matches) == 1:
				contextual_mapping[table_name][column_matches[0]].append(raw_col)
			

		# TODO: detect date columns and append to contextual_mapping[table_name]["dates"]
		# 4. Assign date-like raw_cols to "dates"
		'''
		Strategy:
		- detect YYYY/MM/DD or YYYY-MM-DD or MM/DD/YYYY (these are values, not raw_col names)
		- store as {"raw_col_name": parsed_date}
		'''

		# TODO: map other_classes → role/capability/propulsion can pull from Ontology
		# 5. Assign role / capability / propulsion from other_classes
		'''
		Strategy:
		- other_classes contains non-equipment ontology classes
		- map them to role/capability/propulsion when appropriate
		'''
		other_classes = info["other_classes"]


		# TODO: fallback ambiguous raw_cols → "note"
		# 6. Assign ambiguous raw_cols later (Phase IV)
		'''
		Examples:
		- equip_type vs variant vs ship_name
		- dimensions → displacement/length/width
		- relationship → armament/carrier/crew complement
		
		For now:
		- leave ambiguous raw_cols unassigned
		- or assign them to "note"
		'''
		#TODO: We don't have this; this is the most important column and we need to fugure out a system to classify it
		# contextual_mapping[table_name]["equip_type"].append(info["equip_type"]) 


		# TODO: enforce required super_cols
		# 7. Ensure required super_cols exist for ALL tables
		'''
		Required:
		- country
		- quantity
		- ancestral_class
		- sub_class
		- equip_type
		
		If missing:
		- assign placeholder values ("variant" raw_col for equip_type if there is one, None or "" otherwise for now)
		'''

	# print(contextual_mapping)
	# 8. Return contextual_mapping and canonical_columns
	build_mapping_table(conn, table_classes, contextual_mapping, super_cols_list)

	return contextual_mapping, super_cols_list

