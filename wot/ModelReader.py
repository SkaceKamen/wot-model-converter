"""
Thanks Coffee_ for discovering the primitives format
and writing original script that did the unpacking. This is
just rewritten script to python.
"""

from wot.XmlUnpacker import XmlUnpacker
import xml.etree.ElementTree as ET
from struct import unpack
from io import BytesIO

def unp(format, data):
	return unpack(format, data)[0]

class ModelReader:
	debug=False
	
	def __init__(self,debug=False):
		self.debug = debug
	
	def out(self, text):
		if self.debug:
			print(text)
	
	def read(self, primitives_fh, visual_fh):
		# Read visual file
		xmlr = XmlUnpacker()
		visual = xmlr.read(visual_fh)

		# Makes core short
		f = primitives_fh
		
		# Load sections table
		# Starts from back
		f.seek(-4,2)
		table_start = unp("i", f.read(4))
		f.seek(-4-table_start, 2)
		
		# Position of section starts from 4
		position = 4
		
		self.out("== SECTIONS")
		
		# Read sections
		sections = {}
		while True:
			
			# Read section size
			data = f.read(4)
			
			if data == None or len(data) != 4:
				break
			
			section_size = unp("I", data)
			
			# Skip bytes with unknown purpose
			if len(f.read(16)) != 16:
				break
			
			# Read section name
			section_name_length = unp("I", f.read(4))
			section_name = f.read(section_name_length).decode("UTF-8")
			
			# Section informations
			section = {
				'position': position,
				'size': section_size,
				'name': section_name,
				'data': None
			}
			
			self.out("%s position %X size %X" % (section_name, section["position"], section["size"]))
			
			sections[section_name] = section

			# Round to 4
			position += section_size
			if section_size % 4 > 0:
				position += 4 - section_size % 4
			
			if section_name_length % 4 > 0:
				f.read(4 - section_name_length % 4)
		
		# Read sections data
		for name, section in sections.items():
			f.seek(section["position"])
			section['data'] = BytesIO(f.read(section["size"]))
		
		# Read visual data
		nodes = {}
		nodes["Scene Root"] = self.readNode(visual.find("node"))
		boundingBox = [
			[ float(v) for v in visual.find("boundingBox").find("min").text.split(' ') ],
			[ float(v) for v in visual.find("boundingBox").find("max").text.split(' ') ]
		]
		
		# Load render sets
		sets = []
		for render_set in visual.findall("renderSet"):
			
			# Nodes - purpose unknown
			set_nodes = [ v.text for v in render_set.findall("node") ]
		
			# Names of sections used in this render set
			vertices_name = render_set.find("geometry").find("vertices").text.strip()
			indices_name = render_set.find("geometry").find("primitive").text.strip()
			stream_name = None
			if render_set.find("geometry").find("stream") is not None:
				stream_name = render_set.find("geometry").find("stream").text.strip()
			
			# Load render set data
			indices, groups = self.readIndices(sections[indices_name]["data"])
			vertices = self.readVertices(sections[vertices_name]["data"])
			
			# Load stream data
			# For some reason this section can be missing
			uv2 = None
			colour = None
			if stream_name and stream_name in sections:
				data, type = self.readStream(sections[stream_name]["data"])
				if type == "colour":
					colour = data
				elif "uv2" in type:
					uv2 = data
				
			
			# Apply stream data
			if uv2 or colour:
				for index, vertex in enumerate(vertices):
					if uv2:
						vertex.uv2 = uv2[index]
					if colour:
						vertex.colour = colour[index]
				
			# Split data into groups
			primitive_groups = []
			for group in render_set.find("geometry").findall("primitiveGroup"):
				material = self.readMaterial(group.find("material"))
				origin = [ float(v) for v in group.find("groupOrigin").text.split(' ') ]
				index = int(group.text.strip())
				
				i_from = groups[index]["startIndex"]
				i_to = i_from + groups[index]["primitivesCount"]*3
				v_from = groups[index]["startVertex"]
				v_to = v_from + groups[index]["verticesCount"]
				
				self.out("group indices %d / %d (%d - %d)" % ((i_to - i_from), len(indices), i_from, i_to))
				self.out("group vertices %d / %d (%d - %d)" % ((v_to - v_from), len(vertices), v_from, v_to))

				primitive_groups.append(PrimitiveGroup(
					origin = origin,
					material = material,
					vertices = vertices[v_from:v_to],
					indices = [ v - groups[index]["startVertex"] for v in indices[i_from:i_to] ]
				))
			
			# Save render set
			sets.append(RenderSet(
				nodes = set_nodes,
				groups = primitive_groups
			))
		
		return Primitive(
			renderSets = sets,
			nodes = nodes,
			boundingBox = boundingBox
		)
	
	def readMaterial(self, element):
		material = Material()
		
		# @TODO: Material has more properties ...
		for item in element:
			if item.tag == "fx":
				material.fx = item.text.strip()
			elif item.tag == "collisionFlags":
				material.collisionFlags = item.text.strip()
			elif item.tag == "materialKind":
				material.materialKind = item.text.strip()
			elif item.tag == "identifier":
				material.ident = item.text.strip()
			elif item.tag == "property":
				if item.text.strip() == "diffuseMap":
					material.diffuseMap = item.find("Texture").text.strip().replace(".tga", ".dds")
				elif item.text.strip() == "diffuseMap2":
					material.diffuseMap2 = item.find("Texture").text.strip().replace(".tga", ".dds")
				elif item.text.strip() == "specularMap":
					material.specularMap = item.find("Texture").text.strip().replace(".tga", ".dds")
				elif item.text.strip() == "normalMap":
					material.normalMap = item.find("Texture").text.strip().replace(".tga", ".dds")
				elif item.text.strip() == "doubleSided":
					material.doubleSided = int(item.find("Bool").text.strip())
				elif item.text.strip() == "alphaReference":
					material.alphaReference = int(item.find("Int").text.strip())
		
		return material
	
	def readVertices(self, data):
		self.out("== VERTICES")
		
		vertices = []

		type = data.read(64).decode("UTF-8").split('\x00')[0]
		subtype = None
		count = unp("I", data.read(4))
		
		if "BPVT" in type:
			subtype = data.read(64).decode("UTF-8").split('\x00')[0]
			count = unp("I", data.read(4))
		
		self.out("type %s subtype %s count %d stride %d" % (type, subtype, count, self.getStride(type, subtype)))
	
		for i in range(count):
			vertices.append(self.readVertice(data, type, subtype)) 
		
		return vertices
	
	def getStride(self, type, subtype):
		stride = 24
		
		if subtype == "set3/xyznuviiiwwtbpc":
			stride = 40
		elif "xyznuviiiwwtb" in type:
			stride = 37
		elif "xyznuvpc" in type or "xyznuvtb" in type:
			stride = 32
		
		return stride
	
	def readVertice(self, data, type, subtype):
		vert = Vertice()
		
		# Load basic info
		vert.position = unpack("3f", data.read(12))
		vert.normal = self.readNormal(data, type, subtype)
		vert.uv = unpack("2f", data.read(8))
		
		# Decide correct type
		stride = self.getStride(type, subtype)
		
		"""
		if ("xyznuvpc" in type and "set3" not in type) or "xyznuvtb" in type:
			stride = 32
		if "xyznuviiiwwtb" in type:
			stride = 37
		if type == 'set3/xyznuviiiwwtbpc':
			stride = 40
		"""
		
		# Unpack remaining values
		if stride == 32:
			vert.t = unp("I", data.read(4))
			vert.bn = unp("I", data.read(4))
		elif stride == 37:
			vert.index = unpack("3B", data.read(3))
			vert.weight = unpack("2B", data.read(2))
			vert.t = unp("I", data.read(4))
			vert.bn = unp("I", data.read(4))
		elif stride == 40:
			vert.index = unpack("3B", data.read(3))
			vert.index2 = unpack("3B", data.read(3))
			vert.weight = unpack("2B", data.read(2))
			vert.t = unp("I", data.read(4))
			vert.bn = unp("I", data.read(4))
		
		return vert
	
	def readNormal(self, data, type, subtype):
		packed = unp("I", data.read(4))
		if "set3" in subtype:
			pkz = (int(packed) >> 16) & 0xFF ^0xFF
			pky = (int(packed) >> 8) & 0xFF ^0xFF
			pkx = (int(packed)   ) & 0xFF ^0xFF
			
			if pkx > 0x7f:
				x = - float(pkx & 0x7f )/0x7f
			else:
				x =   float(pkx ^ 0x7f)/0x7f
			if pky > 0x7f:
				y = - float(pky & 0x7f)/0x7f 
			else:
				y =   float(pky ^ 0x7f)/0x7f
			if pkz >0x7f:
				z = - float(pkz & 0x7f)/0x7f
			else:
				z =   float(pkz ^ 0x7f)/0x7f
			return (x,y,z)
		else:
			pkz = (int(packed) >> 22) & 0x3FF
			pky = (int(packed) >> 11) & 0x7FF
			pkx = (int(packed)) & 0x7FF
			
			if pkx > 0x3ff:
				x = - float((pkx & 0x3ff ^ 0x3ff)+1)/0x3ff
			else:
				x = float(pkx)/0x3ff
			if pky > 0x3ff:
				y = - float((pky & 0x3ff ^ 0x3ff) +1)/0x3ff 
			else:
				y = float(pky)/0x3ff
			if pkz >0x1ff:
				z = - float((pkz & 0x1ff ^ 0x1ff) +1)/0x1ff
			else:
				z = float(pkz) / 0x1ff
			return (x,y,z)
	
	def readIndices(self, data):
		self.out("== INDICES")
		
		# Prepare informations
		indices = []
		groups = []
		
		# Read type (ended by 0)
		type = data.read(64).decode("UTF-8", "ignore").split('\x00')[0]
		
		# One indice length
		stride = 2
		format = "H"
		
		if type == "list32":
			stride = 4
			format = "I"
		
		# Read totals
		count = unp("I", data.read(4))
		groups_count = unp("I", data.read(4))
		
		self.out("groups %d indices %d stride %d type %s" % (groups_count, count, stride, type))
		
		# Read indices
		for i in range(count):
			indices.append(unp(format, data.read(stride)))
		
		# Change to correct order
		for i in range(0, count - 2, 3):
			l1 = indices[i]
			l2 = indices[i + 1]
			l3 = indices[i + 2]
			indices[i + 2] = l1
			indices[i] = l3
		
		# Read groups
		for i in range(groups_count):
			ints = unpack("4I", data.read(16))
			groups.append({
				"id": i,
				"startIndex": ints[0],
				"primitivesCount": ints[1],
				"startVertex": ints[2],
				"verticesCount": ints[3]
			})
		
		return (indices, groups)
	
	def readStream(self, data):
		self.out("== STREAM")
		result = []
		
		# Read type (ended by 0)
		type = data.read(64).decode("UTF-8").split('\x00')[0]
		subtype = None
		count = unp("I", data.read(4))
		
		if "BPV" in type:
			subtype = data.read(64).decode("UTF-8").split('\x00')[0]
			count = unp("I", data.read(4))
		
		self.out("stream type (%s %s) count %d" % (type, subtype, count))
		
		for i in range(count):
			if subtype == "colour":
				result.append(unpack("4B", data.read(4)))
			elif "uv2" in subtype:
				result.append(unpack("2f", data.read(8)))

		return result, subtype if subtype is not None else type
	
	def readNode(self, element):
		node = {
			"transform": [ float(v) for v in element.find("transform").text.strip().split(' ') ],
			"children": {}
		}
		
		for child in element.findall("node"):
			node["children"][child.find("identifier").text.strip()] = self.readNode(child)

		return node

class Primitive:
	renderSets = None
	nodes = None
	boundingBox = None
	
	def __init__(self, renderSets, nodes, boundingBox):
		self.renderSets = renderSets
		self.nodes = nodes
		self.boundingBox = boundingBox

class RenderSet:
	nodes = None
	groups = None
	
	def __init__(self, nodes, groups):
		self.nodes = nodes
		self.groups = groups
	
class PrimitiveGroup:
	origin = None
	material = None
	vertices = None
	indices = None
	
	def __init__(self, origin, material, vertices, indices):
		self.origin = origin
		self.material = material
		self.vertices = vertices
		self.indices = indices
		
class Material:
	shader = None
	collisionFlags = None
	materialKind = None
	identifier = None
	
	diffuseMap = None
	diffuseMap2 = None
	doubleSided = None
	specularMap = None
	alphaReference = None
	normalMap = None

class Vertice:
	position = None
	normal = None
	uv = None
	uv2 = None
	colour = None
	index = None
	index2 = None
	weight = None
	t = None
	bn = None
