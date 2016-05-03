""" SkaceKamen (c) 2015-2016 """



#####################################################################
# imports

from wot.chunks.utility import *

def get(f, bwst, debug=False):
	table = read_table(f)
	trees = {}

	for item in table["entries"]:
		matrix = unpack("<16f", item[0:64])
		key = unp("<I", item[64:68])
		if key in bwst:
			tree = bwst[key]
			if tree not in trees:
				trees[tree] = [matrix]
			else:
				trees[tree].append(matrix)

	return trees
