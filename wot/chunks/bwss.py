""" SkaceKamen (c) 2015-2016 """



#####################################################################
# imports

from wot.chunks.utility import *

def get(f, strings, debug=False):
	table = read_table(f)
	print_table(table)

	for item in table["entries"]:
		ints = unpack("<" + ("I" * (table["entry_size"]//4)), item)
		print([hex2(v, 8) for v in ints])

		index = 0
		for i in ints:
			if i in strings:
				print(index, strings[i])
			index += 1

	print("position", hex2(f.tell()))

	#data_size = unp("<I", f.read(4))
	# print("size", hex2(data_size))

	f.seek(0xE84)

	print("position", hex2(f.tell()))

	table = read_table(f)
	print_table(table)

	for item in table["entries"]:
		ints = unpack("<" + ("I" * (table["entry_size"]//4)), item)
		print([ hex2(v, 8) for v in ints ])

		index = 0
		for i in ints:
			if i in strings:
				print(index, strings[i])
			index += 1

	print("position", hex2(f.tell()))

	table = read_table(f)
	print_table(table)

	for item in table["entries"]:
		ints = unpack("<" + ("I" * (table["entry_size"]//4)), item)
		print([ hex2(v, 8) for v in ints ])

		index = 0
		for i in ints:
			if i in strings:
				print(index, strings[i])
			index += 1

	print("position", hex2(f.tell()))

	table = read_table(f)
	print_table(table)

	for item in table["entries"]:
		ints = unpack("<" + ("B" * (table["entry_size"])), item)
		print(" ".join([ hex2(v, 2) for v in ints ]))

		index = 0
		for i in ints:
			if i in strings:
				print(index, strings[i])
			index += 1

	print("position", hex2(f.tell()))

	table = read_table(f)
	print_table(table)

	for item in table["entries"]:
		ints = unpack("<" + ("B" * (table["entry_size"])), item)
		print(" ".join([ hex2(v, 2) for v in ints ]))

		index = 0
		for i in ints:
			if i in strings:
				print(index, strings[i])
			index += 1

	print("position", hex2(f.tell()))

	table = read_table(f)
	print_table(table)

	for item in table["entries"]:
		ints = unpack("<" + ("B" * (table["entry_size"])), item)
		print(" ".join([ hex2(v, 2) for v in ints ]))

		index = 0
		for i in ints:
			if i in strings:
				print(index, strings[i])
			index += 1

	print("position", hex2(f.tell()))

	table = read_table(f)
	print_table(table)

	for item in table["entries"]:
		ints = unpack("<" + ("I" * (table["entry_size"] // 4)), item)
		print(" ".join([ hex2(v, 8) for v in ints ]))

		index = 0
		for i in ints:
			if i in strings:
				print(index, strings[i])
			index += 1

	print("position", hex2(f.tell()))
