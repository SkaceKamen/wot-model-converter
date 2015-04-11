import subprocess
import xml.etree.ElementTree as ET
import sys
import argparse
import os
import zlib
import ctypes
import wot
from struct import unpack

def unpackNormal(packed):
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
	
	return {
		'x': float(x) / 0xFF,
		'y': float(y) / 0xFF,
		'z': float(z) / 0xFF
	}
			
class vertice:
	bn = None
	bnx = None
	bny = None
	bnz = None
	index_1 = 0
	index_2 = 0
	index_3 = 0
	n = None
	t = None
	tx = None
	ty = None
	tz = None
	u = None
	u2 = None
	v = None
	v2 = None
	weight_1 = 0
	weight_2 = 0
	x = None
	y = None
	z = None
	
parser = argparse.ArgumentParser(description='Converts BigWorld primitives file to obj.')
parser.add_argument('input', help='primitives file path')
parser.add_argument('-v','--visual', dest='visual', help='visual file path')
parser.add_argument('-o','--obj', dest='obj', help='result obj path')
parser.add_argument('-m','--mtl', dest='mtl', help='result mtl path')
parser.add_argument('-t','-t', dest='textures', help='path to textures')
parser.add_argument('-sx','--scalex', dest='scalex', help='X scale')
parser.add_argument('-sy','--scaley', dest='scaley', help='Y scale')
parser.add_argument('-sz','--scalez', dest='scalez', help='Z scale')
parser.add_argument('-tx','--transx', dest='transx', help='X transform')
parser.add_argument('-ty','--transy', dest='transy', help='Y transform')
parser.add_argument('-tz','--transz', dest='transz', help='Z transform')
parser.add_argument('-c','--compress', dest='compress', action='store_true', help='Compress output using zlib')
parser.add_argument('-nm','--nomtl', dest='no_mtl', help='don\'t output material', action='store_true')
parser.add_argument('-nvt','--novt', dest='no_vt', help='don\'t output UV coordinates', action='store_true')
parser.add_argument('-nvn','--novn', dest='no_vn', help='don\'t output normals', action='store_true')

args = parser.parse_args()
	
filename_primitive = args.input
filename_visual = filename_primitive.replace(".primitives", ".visual")
filename_obj = filename_primitive.replace(".primitives", ".obj")
filename_mtl = filename_obj.replace(".obj", ".mtl")

scale_x = 1
scale_y = 1
scale_z = 1

transform_x = 0
transform_y = 0
transform_z = 0

compress = False

output_material = True
output_vt = True
output_vn = True

textures_path = ''  #'../../../../../'

if args.visual != None:
	filename_visual = args.visual
if args.obj != None:
	filename_obj = args.obj
	filename_mtl = filename_obj.replace(".obj", ".mtl")
if args.mtl != None:
	filename_mtl = args.mtl
if args.textures != None:
	textures_path = args.textures
	
if args.scalex != None:
	scale_x = float(args.scalex)
if args.scaley != None:
	scale_y = float(args.scaley)
if args.scalez != None:
	scale_z = float(args.scalez)

if args.transx != None:
	transform_x = float(args.transx)
if args.transy != None:
	transform_y = float(args.transy)
if args.transz != None:
	transform_z = float(args.transz)
	
if args.compress:
	compress = True
if args.no_mtl:
	output_material = False
if args.no_vt:
	output_vt = False
if args.no_vn:
	output_vn = False
	
for fpath in (filename_primitive, filename_visual):
	if not os.path.exists(fpath):
		print "Failed to find %s" % fpath
		sys.exit(1)


#Unpack XML file
#subprocess.call(["php", "xml-convert.php", filename_visual, filename_visual.replace('.visual', '.xml2')])
wot.unpackXml(filename_visual, filename_visual.replace('.visual', '.xml'))

filename_visual = filename_visual.replace('.visual', '.xml')

tree = ET.parse(filename_visual)
root = tree.getroot()

geometry = root.find("renderSet").find("geometry")

visual_name_list = []
visual_textures = []
for set in root.findall("renderSet"):
	visual_name_list.append([
		set.find("geometry").find("vertices").text,
		set.find("geometry").find("primitive").text
	])

	group_textures = {}
	for item in geometry.findall("primitiveGroup"):
		textures = {
			"diffuse": None,
			"ident": item.find("material").find("identifier").text
		}
		for prop in item.find("material").findall("property"):
			if prop.text.strip() == "diffuseMap":
				textures['diffuse'] = prop.find("Texture").text.strip()
		group_textures[item.text.strip()] = textures
	visual_textures.append(group_textures)
	
tree = None
root = None

os.unlink(filename_visual)
	
with open(filename_primitive, 'rb') as main:
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
				vert = vertice()
				vert.x = unpack('f', main.read(4))[0] * scale_x + transform_x
				vert.y = unpack('f', main.read(4))[0] * scale_y + transform_y
				vert.z = unpack('f', main.read(4))[0] * scale_z + transform_z
				vert.n = unpack('I', main.read(4))[0]
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
		
		
	mtlc = ""
	objc = ""
		
	objc += "#Exported by Python script\n";
	objc += "#YOU SUCK\n\n"
	objc += "mtllib " + filename_mtl + "\n"
	
	mtlc += "#Exported by Python script\n";
	mtlc += "#YOU SUCK\n\n"

	total_vertices = 0

	sub_index = 0
	for subgroup in subgroups:
		groups_textures = visual_textures[sub_index]
	
		for group in subgroup:
			material_name = "Material_%d_%d" % (sub_index, group['id'])
			object_name = "Group_%d_%d" % (sub_index, group['id'])
		
			if str(group['id']) in groups_textures:
				textures = groups_textures[str(group['id'])]
			else:
				textures = None
				
			if textures != None and textures['ident'] != None:
				object_name = textures['ident']
			
			if output_material:
				mtlc += "\r\nnewmtl %s\n" % material_name
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
				if textures != None and textures['diffuse'] != None and len(textures['diffuse']) > 0:
					mtlc += "\tmap_Kd " + textures_path + textures['diffuse'] + "\n"
			
			objc += "o %s\n" % object_name
			
			for vertice in group['vertices']:
				objc += "v %f %f %f\n" % (vertice.x,vertice.y,vertice.z)
				
			if output_vn:
				for vertice in group['vertices']:						
					n = unpackNormal(vertice.n)
					objc += "vn %f %f %f\n" % (n['x'],n['y'],n['z'])
			
			if output_vt:
				for vertice in group['vertices']:
					objc += "vt %f %f 0.0\n" % (vertice.u, -vertice.v)
				
			if output_material:
				objc += "usemtl %s\n" % material_name
				objc += "s 1\n"
				
				
			format = 0
			if not output_vn and not output_vt:
				format = 1
			if output_vn and not output_vt:
				format = 2
			if not output_vn and output_vt:
				format = 3
			for indicie in group['indicies']:
				l1 = total_vertices + indicie['v1'] + 1 - group['startVertex']
				l2 = total_vertices + indicie['v2'] + 1 - group['startVertex']
				l3 = total_vertices + indicie['v3'] + 1 - group['startVertex']
				
				if format == 0:
					objc += "f %d/%d/%d %d/%d/%d %d/%d/%d\n" % (l1,l1,l1,l2,l2,l2,l3,l3,l3)
				elif format == 1:
					objc += "f %d %d %d\n" % (l1,l2,l3)
				elif format == 2:
					objc += "f %d//%d %d//%d %d//%d\n" % (l1,l1,l2,l2,l3,l3)
				elif format == 3:
					objc += "f %d/%d %d/%d %d/%d\n" % (l1,l1,l2,l2,l3,l3)
				
			total_vertices += group['nVertices']
		sub_index += 1
	
	
	if compress:
		objc = zlib.compress(objc)
		mtlc = zlib.compress(mtlc)
	
	with open(filename_obj, 'wb') as fobj:
		fobj.write(objc)
		
	if output_material:
		with open(filename_mtl, 'wb') as fmtl:
			fmtl.write(mtlc)