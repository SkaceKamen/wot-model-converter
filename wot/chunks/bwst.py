""" SkaceKamen (c) 2015-2016 """



#####################################################################
# imports

from wot.chunks.utility import *

def get(f, debug=False):
	strings = {}
	table = read_table(f)

	if debug:
		print_table(table)

	strings_size = unp("<I", f.read(4))
	strings_start = f.tell()

	for item in table["entries"]:
		key = unp("<I", item[0:4])
		f.seek(strings_start + unp("<I", item[4:8]))
		strings[key] = f.read(unp("<I", item[8:12])).decode("UTF-8")

		if debug:
			print(hex2(key, 8), strings[key])

	return strings
