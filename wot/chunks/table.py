""" SkaceKamen (c) 2015-2016 """



#####################################################################
# imports

from struct import unpack
from wot.chunks.utility import hex2

class Table:
	handle = None
	position = None
	end = None
	size = None
	itemSize = None
	itemCount = None
	debug = False
	name = None

	def __init__(self, f, debug=False, name=""):
		self.handle = f
		self.debug = debug
		self.name = name

		self.position = f.tell()
		self.itemSize = unpack("<I", f.read(4))[0]
		self.itemCount = unpack("<I", f.read(4))[0]
		self.size = 8 + self.itemSize * self.itemCount
		self.end = self.position + self.size

		if self.debug:
			print("=== TABLE %s ===" % self.name)
			print("position", self.position)
			print("size", self.itemSize)
			print("count", self.itemCount)

	def __iter__(self):
		return TableIterator(self)

	def get(self, index):
		position = self.position + 8 + index * self.itemSize
		if self.handle.tell() != position:
			self.handle.seek(position, 0)
		contents = self.handle.read(self.itemSize)

		if self.debug != True and self.debug == 2:
			print([hex2(v, 8) for v in unpack("<" + "I" * (self.itemSize//4), contents[0:(self.itemSize//4)*4])])

		return contents

class TableIterator:
	current = 0
	table = None

	def __init__(self, table):
		self.table = table

	def next(self):
		if self.current < self.table.itemCount:
			self.current += 1
			return self.table.get(self.current - 1)
		raise StopIteration
