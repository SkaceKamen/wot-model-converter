""" SkaceKamen (c) 2015-2016 """



#####################################################################
# imports

import os
from struct import unpack
from struct import pack
from sys import version_info



if version_info < (3, 0, 0):
	range = xrange



def hex2(arg, size=0, reverse=False):
	exec("value = '%%0%dX' %% arg" % size)
	if reverse:
		result = ''
		for i in range(0, len(value), 2):
			result = value[i:i+2] + result
		return result
	return value

def unp(arg, value):
	return unpack(arg, value)[0];

def read_table(f):
	entry_size = unp('<I', f.read(4))
	entry_count = unp('<I', f.read(4))
	items = []
	for i in range(entry_count):
		items.append(f.read(entry_size))
	return {
		'entry_size': entry_size,
		'entry_count': entry_count,
		'entries': items
	}

def print_table(t):
	print('size ', t['entry_size'])
	print('count', t['entry_count'])

def get_bwst():
	strings = {}
	with open('temps/BWST.chunk', 'rb') as f:
		table = read_table(f)

		# print_table(table)

		strings_size = unp('<I', f.read(4))
		strings_start = f.tell()

		for item in table['entries']:
			key = unp('<I', item[0:4])
			f.seek(strings_start + unp('<I', item[4:8]))
			strings[key] = f.read(unp('<I', item[8:12]))

			# print(hex2(key, 8), strings[key])

	return strings
