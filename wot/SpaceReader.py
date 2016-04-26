""" SkaceKamen (c) 2015-2016 """

#####################################################################
# Thanks Coffee_ for cooperative work on this format,
# he did most of the hard work



#####################################################################
# imports

from io import BytesIO
from wot.chunks import *
from struct import unpack



#####################################################################
# SpaceReader

class SpaceReader:
	debug = False

	def __init__(self, debug=False):
		self.debug = debug

	def get_row_section(self, section):
		return {
			'header': unpack('4s', section[0:4])[0].decode('UTF-8'),
			'int1': unpack('<I', section[4:8])[0],
			'position': unpack('<I', section[8:12])[0],
			'int3': unpack('<I', section[12:16])[0],
			'length': unpack('<I', section[16:20])[0],
			'count': unpack('<I', section[20:24])[0]
		}

	def load(self, filename):
		map = MapSpace()

		with open(filename, 'rb') as f:
			main = self.get_row_section(f.read(24))
			if self.debug:
				print(main)

			if main['header'] != 'BWTB':
				raise Exception('Uknown first chunk')

			for i in range(main['count']):
				row = self.get_row_section(f.read(24))
				if self.debug:
					print(row)
				f.seek(row['position'])
				map.setChunk(row['header'], f.read(row['length']))

		return map



#####################################################################
# MapSpace

class MapSpace:
	chunks = {}
	debug = False

	def __init__(self, debug=False):
		self.debug = debug

	def setChunk(self, ident, contents):
		self.chunks[ident.lower()] = contents

	def getChunk(self, ident):
		return BytesIO(
			self.chunks.get(ident.lower()))

	def getMatrices(self):
		return bsmi.get(
			self.getChunk('bsmi'),
			self.debug)

	def getModels(self, ignore_vertices=True):
		return bsmo.get(
			self.getChunk('bsmo'),
			self.getStrings(),
			self.getMaterials(),
			self.getStaticGeometries() if not ignore_vertices else {},
			self.getMatrices(),
			self.debug)

	def getStaticGeometries(self):
		return bwsg.get(
			self.getChunk('bwsg'))

	def getMaterials(self):
		return bsma.get(
			self.getChunk('bsma'),
			self.getStrings(),
			self.debug)

	def getTrees(self):
		return sptr.get(
			self.getChunk('sptr'),
			self.getStrings(),
			self.debug)

	def getWater(self):
		return bwwa.get(
			self.getChunk('bwwa'),
			self.debug)

	def getStrings(self):
		return bwst.get(
			self.getChunk('bwst'),
			self.debug)
