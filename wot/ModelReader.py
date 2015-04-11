from XmlUnpacker import XmlUnpacker
import xml.etree.ElementTree as ET
from struct import unpack

class ModelReader:
	def __init__(self):
		pass
	def read(self, primitives_fh, visual_fh):
		
		#Read visual file
		xmlr = XmlUnpacker()
		root = xmlr.read(visual_fh)

		visual_name_list = []
		visual_materials = []
		
		for set in root.findall("renderSet"):
			geometry = set.find("geometry")
		
			visual_name_list.append([
				geometry.find("vertices").text,
				geometry.find("primitive").text
			])
			
			group_materials = {}
			for item in geometry.findall("primitiveGroup"):
				material = Material()
				
				for prop in item.find("material").findall("property"):
					if prop.text.strip() == "diffuseMap":
						material.diffuseMap = prop.find("Texture").text.strip()
					elif prop.text.strip() == "diffuseMap2":
						material.diffuseMap2 = prop.find("Texture").text.strip()
					elif prop.text.strip() == "specularMap":
						material.specularMap = prop.find("Texture").text.strip()
					elif prop.text.strip() == "normalMap":
						material.normalMap = prop.find("Texture").text.strip()
					elif prop.text.strip() == "doubleSided":
						material.doubleSided = int(prop.find("Bool").text.strip())
					elif prop.text.strip() == "alphaReference":
						material.alphaReference = int(prop.find("Int").text.strip())
						
				group_materials[item.text.strip()] = material
			visual_materials.append(group_materials)
	
		#Dispose of visual file
		xmlr = None
		root = None
		
		#Start reading primitives
		main = primitives_fh
		
		main.seek(-4, 2)
		table_start = unpack('i', main.read(4))[0]
		main.seek(- 4 - table_start, 2)
		
		sections = {}
		
		has_color = False
		has_uv2 = False
		position = 4
		sub_groups = 0
		uv2_section = ""
		
		while True:
			data = main.read(4)
			if data == None or len(data) != 4:
				break
			
			section_size = unpack('I', data)[0]
			
			#Skip dummy bytes
			main.read(16)
			
			data = main.read(4)
			if data == None or len(data) != 4:
				break
			
			section_name_length = unpack('I', data)[0]
			section_name = main.read(section_name_length)
		
			#print "Section", "[" + section_name + "]"
		
			if 'vertices' in section_name:
				sub_groups += 1
		
			if 'colour' in section_name:
				has_color = True
				
			if 'uv2' in section_name:
				has_uv2 = True
				u2_section = section_name
		
			section = {
				'position': position,
				'size': section_size,
				'name': section_name
			}
			
			position += section_size
			if section_size % 4 > 0:
				position += 4 - section_size % 4
			
			if section_name_length % 4 > 0:
				main.read(4 - section_name_length % 4)
			
			sections[section_name] = section
			
		sg = sub_groups - 1
		pl_flag = False
		
		subgroups = []
		
		while sub_groups > 0:
			sub_groups -= 1
			
			groups = []
			subgroups.append(groups)
			
			name_vertices = visual_name_list[(sg - sub_groups)][0]
			name_indicies = visual_name_list[(sg - sub_groups)][1]
			ind_scale = 2
			stride = 32
			
			if sub_groups > 0:
				pl_flag = True
			
			section_vertices = sections[name_vertices]
			section_indicies = sections[name_indicies]
			
			main.seek(section_indicies['position'])
			
			indicies_subname = ''
			i = 0
			while i < 64:
				ch = main.read(1)
				if ord(ch) == 0:
					break
				indicies_subname += ch
				i += 1
			
			main.seek(section_indicies['position'] + 64)
			
			if "list32" in indicies_subname:
				ind_scale = 4
				
			indicies_count = unpack("I", main.read(4))[0]
			indicies_groups = unpack("H", main.read(2))[0]
			
			#print "subname", indicies_subname, "count", indicies_count, "groups", indicies_groups
			
			offset = indicies_count * ind_scale + 72
			main.seek(section_indicies['position'] + offset)
			
			pGroups = []
			i = 0
			while i < indicies_groups:
				pGroups.append({
					'id': i,
					'startIndex': unpack("I", main.read(4))[0],
					'nPrimitives': unpack("I", main.read(4))[0],
					'startVertex': unpack("I", main.read(4))[0],
					'nVertices': unpack("I", main.read(4))[0]
				})
			
				i += 1
				
			main.seek(section_vertices['position'])
			
			vertices_subname = ''
			i = 0
			while i < 64:
				ch = main.read(1)
				if ord(ch) == 0:
					break
				vertices_subname += ch
				i += 1
				
			main.seek(section_vertices['position'] + 64)

			vertices_count = unpack("I", main.read(4))[0]
			
			total_vertices = 0
			for group in pGroups:
				total_vertices += group['nVertices']
				
			total_polygons = 0
			for group in pGroups:
				total_polygons += group['nPrimitives']
			
			#print "subname", vertices_subname, "count", vertices_count, "polys", total_polygons
			
			if "xyznuviiiwwtb" in vertices_subname:
				stride = 37
				
			"""
			@TODO:
			if has_uv2:
				get_u2(vertices_count, uv2_section)
			"""
			
			big_l = indicies_groups
			k = 0
			i = 0
			
			while k < big_l:
				index = 0
				if not pl_flag:
					index = k
				
				groups.append(pGroups[index])
				groups[k]['vertices'] = []
				
				pos = groups[k]['nVertices']
				v = 0
				while v < pos:
					vert = Vertice()
					vert.x = unpack('f', main.read(4))[0]
					vert.y = unpack('f', main.read(4))[0]
					vert.z = unpack('f', main.read(4))[0]
					vert.normal = Normal(unpack('I', main.read(4))[0])
					vert.u = unpack('f', main.read(4))[0]
					vert.v = unpack('f', main.read(4))[0]
				
					if stride == 32:
						vert.t = unpack('I', main.read(4))[0]
						vert.bn = unpack('I', main.read(4))[0]
					else:
						vert.index_1 = ord(main.read(1))
						vert.index_2 = ord(main.read(1))
						vert.index_3 = ord(main.read(1))
						vert.weight_1 = ord(main.read(1))
						vert.weight_2 = ord(main.read(1))
						vert.t = unpack('I', main.read(4))[0]
						vert.bn = unpack('I', main.read(4))[0]
				
					groups[k]['vertices'].append(vert)
				
					v += 1
					i += 1
			
				k += 1
			
		
		root = Model()
		for subgroup in subgroups:
			materials = visual_materials[len(root.models)]
			
			model = Model()
			root.models.append(model)
			
			for group in groups:
				main.seek(section_indicies['position'] + group['startIndex'] * ind_scale + 72)

				group['indicies'] = []
				
				i = 0
				cnt = group['nPrimitives']
				while i < cnt:			
					p1 = None
					p2 = None
					p3 = None
				
					if ind_scale != 2:
						p2 = unpack('I', main.read(4))[0]
						p1 = unpack('I', main.read(4))[0]
						p3 = unpack('I', main.read(4))[0]
					else:
						p2 = unpack('H', main.read(2))[0]
						p1 = unpack('H', main.read(2))[0]
						p3 = unpack('H', main.read(2))[0]
				
					group['indicies'].append({
						'v1': p1,
						'v2': p2,
						'v3': p3
					});
					
					i += 1
				
				grp = ModelGroup()
				grp.id = group['id']
				grp.vertices = group['vertices']
				for indicie in group['indicies']:
					grp.indicies.append(Indicie(
						indicie['v1'] + 1 - group['startVertex'],
						indicie['v2'] + 1 - group['startVertex'],
						indicie['v3'] + 1 - group['startVertex'],
					))
				
				if str(grp.id) in materials:
					grp.material = materials[str(grp.id)]
				
				model.groups.append(grp)

		return root

		
class Model:
	groups = None
	models = None
	
	def __init__(self):
		self.groups = []
		self.models = []
		
	def getObj(self, name_prefix="", v_index_start=0, normals=True, uv=True, materials=False):
		file = ""
		
		for group in self.groups:
			if materials:
				file += group.getObj(name_prefix, v_index_start, normals, uv, group.getMtlName(name_prefix))
			else:
				file += group.getObj(name_prefix, v_index_start, normals, uv)
			v_index_start += len(group.vertices)
		
		index = 0
		for model in self.models:
			file += model.getObj(name_prefix + "sub_" + str(index) + "_", v_index_start, normals, uv, materials)
			v_index_start += model.getVericesCount()
			index += 1
		
		return file
		
	def getObjMtl(self, name_prefix="", normals=True, uv=True):
		obj = self.getObj(name_prefix, 0, normals, uv, True)
		mtl = self.getMtl(name_prefix)
		
		return {
			'obj': obj,
			'mtl': mtl
		}
		
	def getMtl(self, name_prefix=""):
		file = ""
		for group in self.groups:
			file += group.getMtl(name_prefix)
		
		index = 0
		for model in self.models:
			file += model.getMtl(name_prefix + "sub_" + str(index) + "_")
			index += 1
	
		return file
		
	def getVericesCount(self):
		count = 0
		for group in self.groups:
			count += len(group.vertices)
		for model in self.models:
			count += model.getVericesCount()
		return count
	
class ModelGroup:
	id = None
	vertices = None
	indicies = None
	material = None
	
	def __init__(self):
		self.vertices = []
		self.indicies = []
		self.material = None
		
	def getFaces(self):
		faces = []
		for indicie in self.indicies:
			faces.append([indicie.l1, indicie.l2, indicie.l3])
		return faces
		
	def getObj(self, name_prefix="group_", v_index_start=0, normals=True, uv=True, material=None):
		obj = "o %s\n" % self.getGroupName(name_prefix)
		verts = ""
		norms = ""
		mat = ""
		uvs = ""
		faces = ""
		
		if material != None:
			mat += "usemtl %s\n" % material
			mat += "s 1\n"
		
		for vertice in self.vertices:
			verts += "v %f %f %f\n" % (vertice.x, vertice.y, vertice.z)
			if normals:
				norms += "vn %f %f %f\n" % (vertice.normal.x, vertice.normal.y, vertice.normal.z)
			if uv:
				uvs += "vt %f %f 0.0\n" % (vertice.u, vertice.v)
		
		for indicie in self.indicies:
			l1 = indicie.l1 + v_index_start
			l2 = indicie.l2 + v_index_start
			l3 = indicie.l3 + v_index_start
		
			if normals and uv:
				faces += "f %d/%d/%d %d/%d/%d %d/%d/%d\n" % (l1,l1,l1,l2,l2,l2,l3,l3,l3)
			elif not normals and not uv:
				faces += "f %d %d %d\n" % (l1,l2,l3)
			elif normals and not uv:
				faces += "f %d//%d %d//%d %d//%d\n" % (l1,l1,l2,l2,l3,l3)
			elif not normals and uv:
				faces += "f %d/%d %d/%d %d/%d\n" % (l1,l1,l2,l2,l3,l3)
				
		return obj + verts + norms + uvs + mat + faces
	
	def getGroupName(self, prefix="group_"):
		return prefix + str(self.id)
	
	def getMtlName(self, prefix="material_"):
		return prefix + str(self.id)
	
	def getMtl(self, name_prefix="material_"):
		mtlc = ""
		mtlc += "\r\nnewmtl %s\n" % self.getMtlName(name_prefix)
		mtlc += "\tNs 20.0\n"
		mtlc += "\tNi 1.0000\n"
		mtlc += "\td 1.0000\n"
		mtlc += "\tTr 1.0000\n"
		mtlc += "\tTf 1.0000 1.0000 1.0000\n"
		mtlc += "\tillum 1\n"
		mtlc += "\tKa 0.2 0.2 0.2\n"
		mtlc += "\tKd 0.3 0.3 0.3\n"
		mtlc += "\tKs 0.4 0.4 0.4\n"
		mtlc += "\tKe 0.0 0.0 0.0\n"
		if self.material.diffuseMap:
			mtlc += "\tmap_Kd %s\n" % self.material.diffuseMap
			
		return mtlc


class Material:
	diffuseMap = None
	diffuseMap2 = None
	doubleSided = None
	specularMap = None
	alphaReference = None
	normalMap = None
	ident = None
	
class Indicie:
	l1 = None
	l2 = None
	l3 = None
	
	def __init__(self,l1,l2,l3):
		self.l1 = l1
		self.l2 = l2
		self.l3 = l3
	
class Normal:
	packed = None
	x = None
	y = None
	z = None
	
	def __init__(self, packed = None):
		if packed != None:
			self.packed = packed
			pkz = (long(packed) >> 16) & 0xFF
			pky = (long(packed) >> 8) & 0xFF
			pkx = (long(packed)) & 0xFF
			
			"""z = pkz >> 16
			y = pky >> 8
			x = pkx"""
			
			x = pkx
			y = pky
			z = pkz
			
			if x > 0x7F:
				x = - (x - 0x7F)
			if y > 0x7F:
				y = - (y - 0x7F)
			if z > 0x7F:
				z = - (z - 0x7F)
			
			self.x = float(x) / 0xFF
			self.y = float(y) / 0xFF
			self.z = float(z) / 0xFF
	
class Vertice:
	normal = None
	bn = None
	t = None
	u = None
	u2 = None
	v = None
	v2 = None
	x = None
	y = None
	z = None
	index_1 = 0
	index_2 = 0
	index_3 = 0
	weight_1 = 0
	weight_2 = 0
