""" SkaceKamen (c) 2015-2016 """



#####################################################################
# imports

from struct import unpack
import xml.etree.ElementTree as ET
import base64



#####################################################################
# XmlUnpacker

class XmlUnpacker:
	PACKED_HEADER = 0x62a14e45
	stream = None
	dict = []
	debug = False

	def __init__(self):
		pass

	def read(self, stream):
		self.stream = stream
		if not self.isPacked():
			stream.seek(0);
			tree = ET.fromstring(stream.read())
			return tree

		self.dict = self.readDictionary()

		root = ET.Element('root')
		self.readElement(root)

		self.stream = None

		return root

	def readElement(self, base):
		children_count = unpack('<H', self.stream.read(2))[0]

		descriptor = self.readDataDescriptor()
		children = self.readElementDescriptors(children_count)

		offset = self.readData(base, 0, descriptor)

		for child in children:
			node = ET.SubElement(base, self.dict[child['name_index']])
			offset = self.readData(node, offset, child['descriptor'])

	def readDataDescriptor(self):
		data = self.stream.read(4)
		if data:
			end_type = unpack('<L', data)[0]
			return {
				'end': end_type & 0x0fffffff,
				'type': (end_type >> 28) + 0,
				'address': self.stream.tell()
			}

		raise Exception("Failed to read data descriptor")

	def readElementDescriptors(self, count):
		descriptors = []

		for i in range(0, count):
			data = self.stream.read(2)

			if data:
				name_index = unpack('<H', data)[0]
				descriptor = self.readDataDescriptor()
				descriptors.append({
					'name_index': name_index,
					'descriptor': descriptor
				})
			else:
				raise Exception('Failed to read element descriptors')

		return descriptors

	def readData(self, element, offset, descriptor):
		length = descriptor['end'] - offset

		if descriptor['type'] == 0:
			self.readElement(element)
		elif descriptor['type'] == 1:
			element.text = str(self.readString(length))
		elif descriptor['type'] == 2:
			element.text = str(self.readNumber(length))
		elif descriptor['type'] == 3:
			element.text = str(self.readFloat(length))
		elif descriptor['type'] == 4:
			element.text = str(self.readBoolean(length))
		elif descriptor['type'] == 5:
			element.text = str(self.readBase64(length))
		else:
			raise Exception('Unknown element type: ' + str(descriptor['type']))

		return descriptor['end']

	def readString(self,length):
		if length == 0:
			return ''

		return self.stream.read(length).decode("UTF-8")

	def readNumber(self, length):
		if length == 0:
			return 0

		data = self.stream.read(length)
		if length == 1:
			return unpack('b', data)[0]
		elif length == 2:
			return unpack('<H', data)[0]
		elif length == 4:
			return unpack('<L', data)[0]
		elif length == 8:
			return unpack('<Q', data)[0]
		else:
			raise Exception('Uknown number length')

	def readFloat(self, length):
		n = int(length / 4)
		res = ''
		for i in range(0, n):
			if i not in (0, n):
				res += ' '
			res += '%f' % unpack('f', self.stream.read(4))[0]
		return res

	def readBoolean(self, length):
		if length == 0:
			return 0

		if length == 1:
			b = unpack('B', self.stream.read(1))[0]
			if b == 1:
				return 1
			return 0
		else:
			raise Exception("Boolean with wrong length.")

	def readBase64(self, length):
		return base64.b64encode(self.stream.read(length)).decode("UTF-8")

	def readDictionary(self):
		self.stream.seek(5);

		dict = []
		entry = ''
		while True:
			entry = self.readASCIIZ()
			if not entry:
				break
			dict.append(entry)

		return dict;

	def readASCIIZ(self):
		str = ''
		while True:
			c = self.stream.read(1)
			if ord(c) == 0:
				break;
			str += c.decode("UTF-8")
		return str

	def isPacked(self):
		self.stream.seek(0)
		header = unpack('I', self.stream.read(4))[0]

		if header != self.PACKED_HEADER:
			return False
		return True
