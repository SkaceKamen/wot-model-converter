""" SkaceKamen (c) 2015-2016 """



#####################################################################
# imports

from wot.chunks.utility import *

def get(f, debug=False):
	table = read_table(f)
	water = []

	for item in table["entries"]:
		water.append({
			"position": unpack("<3f", item[0:12]),
			"width": unp("<f", item[12:16]),
			"height": unp("<f", item[16:20]),
			"orientation": unp("<f", item[20:24])
		})

	return water