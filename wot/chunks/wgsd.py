""" SkaceKamen (c) 2015-2016 """



#####################################################################
# imports

from wot.chunks.utility import *

def get(f, bwst, debug=False):
	table = read_table(f)
	decals = []

	for item in table["entries"]:
		ints = unpack("<" + ("I" * (table["entry_size"]//4)), item)

		matrix = []
		for i in range(16):
			matrix.append(unp("<f", item[4 + i*4:4 + i*4+4]))

		info = {
			"matrix": matrix,
			"diffuse": strings[ints[17]],
			"normal": strings[ints[18]],
			"extra": strings[ints[19]],
			"int0": ints[0],
			"int20+": ints[20:]
		}

		if debug:
			print(info["diffuse"])
			print(hex2(info["int0"], 8), [ hex2(v, 8) for v in info["int20+"]])

		decals.append(info);

	table = read_table(f)

	for item in table["entries"]:
		ints = unpack("<" + ("I" * (table["entry_size"]//4)), item)
		if debug:
			print([ hex2(v, 8) for v in ints ])

	return decals
