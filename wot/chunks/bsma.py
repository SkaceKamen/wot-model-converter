""" SkaceKamen (c) 2015-2016 """



#####################################################################
# imports

from wot.chunks.utility import *

def get(f, strings, debug=False):
	result = []

	table = read_table(f)

	if debug:
		print_table(table)

	"""
	MATERIALS TABLE

	uint32 fx index
	uint32 properties_index_from
	uint32 properties_index_to
	"""

	materials = []
	for item in table["entries"]:
		ints = unpack("<" + ("I" * (table["entry_size"]//4)), item)

		info = {
			"fx": ints[0],
			"from": ints[1],
			"to": ints[2]
		}

		# print(hex2(info["from"], 8), hex2(info["to"], 8))

		materials.append(info);

	"""
	FX TABLE

	uint32 key in BWST
	"""

	table = read_table(f)

	fx = []
	for item in table["entries"]:
		key = unp("<I", item)
		fx.append(strings[key])

		# print(strings[key])

	"""
	PROPERTIES TABLE

	uint32 key in BWST -> property name
	uint32 value_type
	uint32 value (dependent on type)

	Property value types:
		1 - Bool
		2 - Float
		3 - Int
		4 - ???
		5 - Vector4 (how to get it?)
		6 - String (from WBST)
		7 - ???

	"""

	table = read_table(f)

	if debug:
		print_table(table)

	index = 0
	properties = []
	for item in table["entries"]:
		ints = unpack("<" + ("I" * (table["entry_size"]//4)), item)

		info = {
			"index": index,
			"property": strings[ints[0]],
			"value_type": ints[1],
			"value": ints[2]
		}

		if info["value_type"] == 1:
			info["value"] = True if info["value"] > 0 else False

		if info["value_type"] == 2:
			info["value"] = unp("<f", item[8:])

		if info["value_type"] == 6:
			info["value"] = strings[ints[2]]

		properties.append(info)
		index += 1

	"""
	MATRIX4 TABLE ?
	 Size: 64
	"""

	table = read_table(f)

	if debug:
		print_table(table)

	matrixes = []

	for item in table["entries"]:
		floats = unpack("<" + ("f" * (table["entry_size"]//4)), item)
		matrixes.append(floats)

	"""
	VECTOR4 TABLE
	 Size: 16
	"""

	table = read_table(f)

	if debug:
		print_table(table)

	vectors = []

	for item in table["entries"]:
		floats = unpack("<" + ("f" * (table["entry_size"]//4)), item)
		vectors.append(floats)

	index = 0
	for mat in materials:
		info = {
			"properties": {}
		}

		if mat["fx"] != 0xFFFFFFFF:
			info["fx"] = fx[mat["fx"]]

		if mat["from"] != 0xFFFFFFFF and mat["to"] != 0xFFFFFFFF:
			for i in range(mat["from"], mat["to"] + 1):
				property = properties[i]
				if property["value_type"] == 5:
					property["value"] = vectors[property["value"]]

				info["properties"][property["property"]] = property["value"]

		result.append(info)

		index += 1
		# print(index, info)
	return result
