import re
from data.data_classification.column_classification_helper import *
from utils.execute_SQL import build_mapping_table
from utils.normalization import normalize_text

CANONICAL_COLUMNS = [
	"country", #WE HAVE: the country that owns this equipment. this is in a_meta_table
	"quantity", #VITAL: some tables have quantity, others had it built during cleaning from a spanned row; this will need to be cleaned
	#the following isn't as important
	"origin", #might be a manufacturer or counrty (or a list of either)
	"cost", # DON'T HAVE YET
	"dates", #list of dates with type, like [Commissioned: 1941/12/07, Retired: 2026/7/16]. If it looks like a date, put it with the raw_col name and combine them all 
	"status", 
	#ONTOLOGY STUFF
	"class_path", #"Equipment->[Aircraft, Smallarm, System, Vehicle, Vessel]" else: NOT_EQUIPMENT = 
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
	]  # this list is *almost* big enough to warrant a .csv


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
	contextual_mapping = {}
	super_cols_list = CANONICAL_COLUMNS #to clean out notes and stale super_cols
	# ontology_columns = {}      # TODO: load expectedColumns from ontology

	for table_name, info in table_classes.items():

		# 1. For each table, initialize empty super_col buckets and a bucket for unassigned raw_cols
		raw_cols = info["raw_cols"]
		unassigned_matched_cols = {raw_col: [] for raw_col in raw_cols} 	
		contextual_mapping[table_name] = {col: [] for col in super_cols_list}

		# 2. Assign known non-raw-col values (from classify_tables) as metadata (i.e.: country, etc.)
		table_metadata = {
			"country": table_classes[table_name]["country"],
			"class_path": table_classes[table_name]["class_path"],
			"sub_class": table_classes[table_name]["equipment_class"],
			"url": table_classes[table_name]["url"],
		}
		contextual_mapping[table_name]["__metadata__"] = table_metadata


		# 3. Assign raw_cols that match canonical columns directly via regex or previous architecture
		for raw_col in raw_cols:
			column_matches = classify_raw_col(raw_col)
			unassigned_matched_cols[raw_col] = column_matches
			
			#assign easy ones while we're here
			if raw_col == "section":
				contextual_mapping[table_name]["sub_class"].append(raw_col)
				unassigned_matched_cols.pop(raw_col)
			elif len(set(column_matches)) == 1:
				contextual_mapping[table_name][column_matches[0]].append(raw_col)
				unassigned_matched_cols.pop(raw_col)
			elif raw_col == "quantity":
				contextual_mapping[table_name]["quantity"].append(raw_col)
				unassigned_matched_cols.pop(raw_col)
		
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

		# 6. Ensure required super_cols exist for ALL tables
		'''
		Required:
		- equip_type
		If missing:
		- see if any remaining raw_cols have [...,equip_type,...] -> if only one, assign & win
		- find any raw_cols matching the ambiguous ^(class|model|type|make|family|name)$ -> if only one, assign & win
		- assign placeholder values ("variant" or "other names" raw_col for equip_type if there is one
		- cry: None or "" otherwise for now)
		'''
		if not contextual_mapping[table_name]["equip_type"]:
			candidates = []

			# 6.1 Look at unassigned raw_cols for good equip_type candidates
			for raw_col in unassigned_matched_cols:
				matches = unassigned_matched_cols[raw_col]
				# ontology/regex already thinks this might be equip_type
				if "equip_type" in matches or re.search(r"^(name|ship$|model|make|family)$", raw_col, re.IGNORECASE): #Still to ambiguous: type
					candidates.append(raw_col)

			# 6.2 If exactly one candidate → promote it to equip_type
			if len(candidates) == 1:
				chosen_one = candidates[0]
				contextual_mapping[table_name]["equip_type"].append(chosen_one)
				unassigned_matched_cols.pop(chosen_one, None)

			# 6.3 If no candidates → try reassigning from other_names / variant
			elif len(candidates) == 0:
				# simple heuristic: if other_names has exactly one raw_col, promote it
				if len(contextual_mapping[table_name]["other_names"]) == 1:
					chosen_one = contextual_mapping[table_name]["other_names"][0]
					contextual_mapping[table_name]["equip_type"].append(chosen_one)
					contextual_mapping[table_name]["other_names"].remove(chosen_one)
					unassigned_matched_cols.pop(chosen_one, None)
				elif len(contextual_mapping[table_name]["variant"]) == 1:
					chosen_one = contextual_mapping[table_name]["variant"][0]
					contextual_mapping[table_name]["equip_type"].append(chosen_one)
					contextual_mapping[table_name]["variant"].remove(chosen_one)
					unassigned_matched_cols.pop(chosen_one, None)

				else:
					candidates.extend(contextual_mapping[table_name]["other_names"])
					candidates.extend(contextual_mapping[table_name]["variant"])
				# if still nothing, Phase IV can cry later

			# 6.4 Multiple candidates → strongest match (placeholder for now)
			else:
				#TODO: For now, pick the first;
				chosen_one = candidates[0]
				contextual_mapping[table_name]["equip_type"].append(chosen_one)
				unassigned_matched_cols.pop(chosen_one, None)


		# 7. Assign ambiguous raw_cols later (Phase IV)
		'''
		Examples:
		- equip_type vs variant vs ship_name
		- dimensions → displacement/length/width
		- relationship → armament/carrier/crew complement
		
		For now:
		- leave ambiguous raw_cols unassigned
		- or assign them to "note"
		'''
		for raw_col in unassigned_matched_cols:
			contextual_mapping[table_name]["note"].append(raw_col)
		
		if len(list(contextual_mapping)) % 500 == 0:
			print(f"Columns classified: {len(list(contextual_mapping))}")

	print(f"Columns classified: {len(list(contextual_mapping))}")
	# 8. Return contextual_mapping and canonical_columns
	build_mapping_table(conn, table_classes, contextual_mapping, super_cols_list)

	return contextual_mapping, super_cols_list

