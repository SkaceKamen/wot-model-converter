"""
Thanks Coffee_ for providing usefull informations about ctree format
"""

from struct import unpack

def unp(arg, value):
	return unpack(arg, value)[0];

SINGLE_FORMAT = "normal"
TRIPLE_FORMAT = "triple"
	
class TreesReader:
	""" Reads .ctree files """
	
	def read(self, f):
		f.seek(36)
		
		# Prepare for objects
		objects = []
		
		# Each object has different properties
		names = ["stock", "branches", "leaves", "billboard"]
		vertices_sizes = [52,52,88,68]
		formats = [SINGLE_FORMAT, SINGLE_FORMAT, TRIPLE_FORMAT, TRIPLE_FORMAT]
		
		# Read each object
		for _m in range(4):
			
			# First is vertice count
			vertices_count = unp("<I", f.read(4))
			vertices = []

			# Then read each vertex
			for i in range(vertices_count):
				
				"""
				Vertice
				
				float32 x
				float32 y
				float32 z
				float32 nx
				float32 ny
				float32 nz
				float32 u
				float32 v
				float32 ...
				"""
				
				data = f.read(vertices_sizes[_m])

				vert = Vertice()
				vert.position = unpack("<3f", data[0:12])
				vert.normal = unpack("<3f", data[12:24])
				vert.uv = unpack("<2f", data[24:32])
				vert.uv = (vert.uv[0], -vert.uv[1])
				
				if _m == 3:
					vert.uv = unpack("<2f", data[9*4:11*4])
					vert.uv = (vert.uv[0], -vert.uv[1])

				if _m == 2:
					width = unp("<f", data[4*12:4*13])
					height = unp("<f", data[4*13:4*14])
					vn = int(unp("<f", data[4*15:4*16]))
					
					vert.width = width
					vert.height = height
					vert.vn = vn
					
				vertices.append(vert)
			
			# Now, read number of lods for this object
			indices_lods = unp("<I", f.read(4))

			# Load indices for each lod
			lods = []
			for lod in range(indices_lods):
				
				# Count
				indices_count = unp("<I", f.read(4))
				indices = []

				# Then indices
				for i in range(indices_count):
					indices.append(unp("<I", f.read(4)))
				
				lods.append(indices)
				
			# Now load textures
			texture = f.read(unp("<I", f.read(4)))
			texture2 = f.read(unp("<I", f.read(4)))
			
			# Save to result, if there is anything to save
			if len(vertices) > 0:
				objects.append(TreeObject(names[_m], vertices, lods, [texture, texture2], formats[_m]))
		
		return Tree(objects)
		
class Vertice:
	position = None
	normal = None
	uv = None
	
	width = None
	height = None
	index = None
		
class Tree:	
	objects = None
	
	def __init__(self, objects):
		self.objects = objects
	
class TreeObject:
	name = None
	vertices = None
	indices = None
	indicesFormat = None
	textures = None
	lods = 0
	
	def __init__(self, name, vertices, indices, textures, indicesFormat):
		self.name = name
		self.indices = indices
		self.vertices = vertices
		self.textures = textures
		self.lods = len(indices)
		self.indicesFormat = indicesFormat