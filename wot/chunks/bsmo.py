""" SkaceKamen (c) 2015-2016 """



#####################################################################
# imports

from wot.chunks.utility import *

def get(f, strings, materials, bwsg, matrices, debug=False):
	if debug:
		print("1.Table - Nodes ranges")

	"""
	NODES RANGES TABLE

	uint32 index from (refering 6. TABLE - Nodes)
	uint32 index to
	"""

	table = read_table(f)

	if debug:
		print_table(table)

	nodes_ranges = []

	for item in table["entries"]:
		ints = unpack("<" + ("I" * (table["entry_size"]//4)), item)
		nodes_ranges.append({
			"from": ints[0],
			"to": ints[1]
		})

	if debug:
		print("2.Table - models")

	"""
	MODELS TABLE

	6 * float32 bounding box
	uint32      BWST key -> model name
	uint32      index from (probably refering 3.table)
	uint32      index to
	"""

	table = read_table(f)

	if debug:
		print_table(table)

	models = []

	index = 0
	for item in table["entries"]:
		ints = unpack("<" + ("I" * (table["entry_size"]//4)), item)
		floot = unpack("<" + ("f" * (table["entry_size"]//4)), item)
		name = None
		if ints[6] in strings:
			name = strings[ints[6]]

		info = {
			"bounding_box": {
				"min": floot[0:3],
				"max": floot[3:6]
			},
			"name": name,
			"from": ints[7],
			"to": ints[8],
			"matrices": matrices.get(index)
		}

		models.append(info)

		if debug:
			print(index, info["name"], info["from"], info["to"])

		index += 1

	if debug:
		print("3.Table")

	"""
	PURPOSE UNKNOWN
	probably refered by 2. TABLE

	uint32 ?
	uint32 ?
	"""

	table = read_table(f)

	if debug:
		print_table(table)

	for item in table["entries"]:
		if debug:
			print([ hex2(v, 8) for v in unpack("<" + ("I" * (table["entry_size"]//4)), item) ])

	if debug:
		print("4.Table - Bounding boxes")

	"""
	BOUDING BOXES TABLE
	actual bouding boxes (respecting scale and position?) probably as
	bounding boxes are already defined in models table

	6 * float64 bounding box
	"""

	table = read_table(f)

	if debug:
		print_table(table)

	index = 0
	for item in table["entries"]:
		models[index]["bounding_box_real"] = {
			"min": unpack("<fff", item[:12]),
			"max": unpack("<fff", item[12:])
		}
		index += 1

	if debug:
		print("5.Table")

	"""
	UKNOWN TABLE
	Size: 4
	Count: Same as models
	"""

	table = read_table(f)

	if debug:
		print_table(table)

	for item in table["entries"]:
		ints = unpack("<" + ("I" * (table["entry_size"]//4)), item)

		if debug:
			print([ hex2(v, 8) for v in ints ])

	if debug:
		print("6.Table - Nodes")

	"""
	NODES TABLE
	Links primitive groups to nodes (which then links to models)

	uint32 index_from
	uint32 index_to
	"""

	table = read_table(f)

	if debug:
		print_table(table)

	nodes = []

	for item in table["entries"]:
		ints = unpack("<" + ("I" * (table["entry_size"]//4)), item)

		if debug:
			print([ hex2(v, 8) for v in ints ])

		nodes.append({
			"from": ints[0],
			"to": ints[1]
		})

	if debug:
		print("7.Table - Primitive groups")

	"""
	PRIMITIVE GROUPS
	List of primitive groups

	uint32 uknown (always FFFFFFFF)
	uint32 uknown (always FFFFFFFF)
	uint32 material index
	uint32 group index (referring different blocks from BWSG?)
	uint32 BWST key -> vertices name
	uint32 BWST key -> indicies name
	uint32 uknown (always 00000000)
	"""

	table = read_table(f)

	if debug:
		print_table(table)

	groups = []
	index = 0

	for item in table["entries"]:
		ints = unpack("<" + ("I" * (table["entry_size"]//4)), item)

		info = {
			"int0": ints[0],
			"int1": ints[1],
			"material": materials[ints[2]],
			"group_index": ints[3],
			"vertices": strings[ints[4]],
			"indicies": strings[ints[5]],
			"int6": ints[6]
		}

		vertices = bwsg.get(info["vertices"])
		if vertices:
			for block in vertices["blocks"]:
				if block["type"] == 0:
					info["data"] = block["data"]

		groups.append(info)

		if debug:
			print([ hex2(v, 8) for v in ints ])
			print(index, info["vertices"], info["indicies"])

		index += 1

	if debug:
		print("8.Table")

	"""
	UNKNOWN
	"""

	table = read_table(f)

	if debug:
		print_table(table)

	for item in table["entries"]:
		ints = unpack("<" + ("I" * (table["entry_size"]//4)), item)
		if debug:
			print([ hex2(v, 8) for v in ints ])

	if debug:
		print("9.Table")

	"""
	UNKNOWN
	"""

	table = read_table(f)

	if debug:
		print_table(table)

	for item in table["entries"]:
		ints = unpack("<" + ("I" * (table["entry_size"]//4)), item)

		if debug:
			print([ hex2(v, 8) for v in ints ])

	if debug:
		print("10.Table")

	"""
	UNKNOWN
	"""

	table = read_table(f)

	if debug:
		print_table(table)

	for item in table["entries"]:
		ints = unpack("<" + ("I" * (table["entry_size"]//4)), item)

		if debug:
			print([ hex2(v, 8) for v in ints ])

	if debug:
		print("11.Table")

	"""
	UNKNOWN
	"""

	table = read_table(f)

	if debug:
		print_table(table)

	for item in table["entries"]:
		ints = unpack("<" + ("I" * (table["entry_size"]//4)), item)

		if debug:
			print([ hex2(v, 8) for v in ints ])

	if debug:
		print("position", hex2(f.tell()))

	index = 0
	for model in models:
		model["nodes"] = []

		indexes = nodes_ranges[index]
		for i in range(indexes["from"], indexes["to"] + 1):
			node = []
			subindexes = nodes[i]
			for i2 in range(subindexes["from"], subindexes["to"] + 1):
				node.append(groups[i2])
			model["nodes"].append(node)

		index += 1

	if debug:
		import json
		with open("models.json", "w") as out:
			json.dump(models, out)

	return models
