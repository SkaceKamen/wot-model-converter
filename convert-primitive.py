import pdb

import subprocess
import xml.etree.ElementTree as ET
import sys
import argparse
import os
import zlib
from ctypes import c_long
import wot
from struct import unpack
from glob import glob


MIRROR_ENABLED = True		#mirror v and vn 

class Vertice:
	def __init__(self):
		self.bn = None
		self.bnx = None
		self.bny = None
		self.bnz = None
		self.index_1 = 0
		self.index_2 = 0
		self.index_3 = 0
		self.indexB_1 = 0
		self.indexB_2 = 0
		self.indexB_3 = 0
		self.n = None
		self.t = None
		self.tx = None
		self.ty = None
		self.tz = None
		self.u = None
		self.u2 = None
		self.v = None
		self.v2 = None
		self.weight_1 = 0
		self.weight_2 = 0
		self.x = None
		self.y = None
		self.z = None


#old format VN, 10bit+11bit+11bit as z+y+x
def unpackNormal(packed):
#	pdb.set_trace()
	pkz = (c_long(packed).value >> 22) & 0x3FF
	pky = (c_long(packed).value >> 11) & 0x7FF
	pkx = (c_long(packed).value) & 0x7FF
	
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
	return {
		'x': x,
		'y': y,
		'z': z
	}

#new format VN, 0x00 + 8bitZ + 8bitY + 8bitX
#with inverted VN and f sequence (check reference of flgNewFormat for detail)
def unpackNormal_tag3(packed):
#	pdb.set_trace()
	pkz = (c_long(packed).value >> 16) & 0xFF ^0xFF
	pky = (c_long(packed).value >> 8) & 0xFF ^0xFF
	pkx = (c_long(packed).value   ) & 0xFF ^0xFF
	
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
	return {
		'x': x,
		'y': y,
		'z': z
	}


			
	
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

def main(filename_primitive):
	flgSkinned = False
#	pdb.set_trace()
	filename = os.path.splitext(filename_primitive)[0]
	filename_visual	= '%s.visual' % filename
	if filename_primitive.endswith('_processed'):
		filename_visual	+= '_processed'
	filename_obj = '%s.obj' % filename
	filename_mtl = '%s.mtl' % filename
	
	flgNewFormat = False
	
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
			print("Failed to find %s" % fpath)
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
		
	with open(filename_primitive, 'rb') as mainFP:
		mainFP.seek(-4, 2)
		table_start = unpack('i', mainFP.read(4))[0]
		mainFP.seek(- 4 - table_start, 2)
		sections = {}
		
		has_color = False
		has_uv2 = False
		position = 4
		sub_groups = 0
		uv2_section = ""

#	pdb.set_trace()
	
		while True:
			data = mainFP.read(4)
			if data == None or len(data) != 4:
				break
			
			section_size = unpack('I', data)[0]
			
			#Skip dummy bytes
			data = mainFP.read(16)
			
			data = mainFP.read(4)
			if data == None or len(data) != 4:
				break
			
			section_name_length = unpack('I', data)[0]
			section_name = mainFP.read(section_name_length).decode('UTF-8')
		
			print("Section [ %s ]" % section_name)
		
			if 'vertices' in section_name:
				sub_groups += 1
	#			print 'sub_groups = '+str(sub_groups)
		
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
				mainFP.read(4 - section_name_length % 4)
			
			sections[section_name] = section
			
		sg = sub_groups - 1
		pl_flag = False
		
		subgroups = []
		
		while sub_groups > 0:
			sub_groups -= 1
			
			groups = []
			subgroups.append(groups)
		
			name_vertices = visual_name_list[(sg - sub_groups)][0].strip()
			name_indicies = visual_name_list[(sg - sub_groups)][1].strip()

			ind_scale = 2
			stride = 32
		
#		pdb.set_trace()
			if sub_groups > 0:
				pl_flag = True
#		pdb.set_trace()
			section_vertices = sections[name_vertices]
			section_indicies = sections[name_indicies]
		
			mainFP.seek(section_indicies['position'])
		
		#warning: tailing bytes after indicies_subname not parsed (just padding junks)
			indicies_subname = ''
			i = 0
			while i < 64:
				ch = mainFP.read(1)
				if ord(ch) == 0:
					break
				indicies_subname += ch.decode('UTF-8', errors='ignore')
				i += 1
			
			mainFP.seek(section_indicies['position'] + 64)
		
			#todo: is this the flag for oversize primitives? 65535+ polygons
			if "list32" in indicies_subname:
				ind_scale = 4
			
			indicies_count = unpack("I", mainFP.read(4))[0]
			indicies_groups = unpack("H", mainFP.read(2))[0]
			
			#print "subname", indicies_subname, "count", indicies_count, "groups", indicies_groups
			
			offset = indicies_count * ind_scale + 72
			mainFP.seek(section_indicies['position'] + offset)
		
			pGroups = []
			i = 0
			while i < indicies_groups:
				pGroups.append({
					'id': i,
					'startIndex': unpack("I", mainFP.read(4))[0],
					'nPrimitives': unpack("I", mainFP.read(4))[0],
					'startVertex': unpack("I", mainFP.read(4))[0],
					'nVertices': unpack("I", mainFP.read(4))[0]
				})
		
				i += 1
			
			mainFP.seek(section_vertices['position'])
		
			vertices_subname = ''
			format_string = ''
			vertices_subname = mainFP.read(64).split(b'\x00')[0].decode('UTF-8')
	#set 0.10.0 new format flag			
			if "BPVT" in vertices_subname:
				flgNewFormat = True
				mainFP.read(4)	#null dword used to be vertex length
				format_string = mainFP.read(64).split(b'\x00')[0].decode('UTF-8')
				print('format_string=%s' % format_string)
	#			pdb.set_trace()
	
			vertices_count = unpack("I", mainFP.read(4))[0]
			
			total_vertices = 0
			for group in pGroups:
				total_vertices += group['nVertices']
				
			total_polygons = 0
			for group in pGroups:
				total_polygons += group['nPrimitives']
			
			print( "subname = %s\ncount = %s\npolys = %s" % (vertices_subname, vertices_count, total_polygons) )
			if "xyznuviiiwwtb" in vertices_subname:
				stride = 37
			if 'iiiww' in format_string:
				flgSkinned = True
			if format_string == 'set3/xyznuviiiwwtbpc':
				stride = 40
				
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
#					pdb.set_trace()
					vert.x = unpack('f', mainFP.read(4))[0] * scale_x + transform_x
					vert.y = unpack('f', mainFP.read(4))[0] * scale_y + transform_y
					vert.z = unpack('f', mainFP.read(4))[0] * scale_z + transform_z
					vert.n = unpack('I', mainFP.read(4))[0]
					vert.u = unpack('f', mainFP.read(4))[0]
					vert.v = unpack('f', mainFP.read(4))[0]
					if MIRROR_ENABLED and not flgSkinned:
						vert.x = - vert.x
				
					if stride == 32:
						vert.t = unpack('I', mainFP.read(4))[0]
						vert.bn = unpack('I', mainFP.read(4))[0]
					elif stride == 37:	#old format skinned
						vert.index_1 = ord(mainFP.read(1))	#bone id for weight1
						vert.index_2 = ord(mainFP.read(1))	#bone id for weight2
						vert.index_3 = ord(mainFP.read(1))	#bone id for remaing weight??
						vert.weight_1 = ord(mainFP.read(1))
						vert.weight_2 = ord(mainFP.read(1))
						vert.t = unpack('I', mainFP.read(4))[0]
						vert.bn = unpack('I', mainFP.read(4))[0]
					elif stride == 40:	#new format skinned. Data structure is guess work 
						vert.index_1 = ord(mainFP.read(1))	#bone id for weight1
						vert.index_2 = ord(mainFP.read(1))	#bone id for weight2
						vert.index_3 = ord(mainFP.read(1))	#bone id for remaing weight??
						vert.indexB_1 = ord(mainFP.read(1))	#bone id for weight1 in another primitives?
						vert.indexB_2 = ord(mainFP.read(1))	#bone id for weight2 in another primitives?
						vert.indexB_3 = ord(mainFP.read(1))	#bone id for remaing weight in another primitives?
						vert.weight_1 = ord(mainFP.read(1))
						vert.weight_2 = ord(mainFP.read(1))
						vert.t = unpack('I', mainFP.read(4))[0]
						vert.bn = unpack('I', mainFP.read(4))[0]
						
	#					if vert.indexB_1 + vert.indexB_2 + vert.indexB_3:
	#						print 'mark'
	#						pdb.set_trace()
				
					groups[k]['vertices'].append(vert)
				
					v += 1
					i += 1
			
				k += 1
			
			for group in groups:
				mainFP.seek(section_indicies['position'] + group['startIndex'] * ind_scale + 72)
	
				group['indicies'] = []
				
				i = 0
				cnt = group['nPrimitives']
				while i < cnt:			
					p1 = None
					p2 = None
					p3 = None
				
					if ind_scale != 2:
						p2 = unpack('I', mainFP.read(4))[0]
						p1 = unpack('I', mainFP.read(4))[0]
						p3 = unpack('I', mainFP.read(4))[0]
					else:
						p2 = unpack('H', mainFP.read(2))[0]
						p1 = unpack('H', mainFP.read(2))[0]
						p3 = unpack('H', mainFP.read(2))[0]
				
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
					
				object_name_print = object_name
				if textures != None and textures['ident'] != None:
					object_name_print = textures['ident']
				
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
				
	#			objc += "o %s\n" % object_name
				objc += "g %s|%s\n" % (object_name_print,object_name)
				
				for vertice in group['vertices']:
					objc += "v %f %f %f\n" % (vertice.x,vertice.y,vertice.z)
					
				if output_vn:
					x_cnt = 1
					for vertice in group['vertices']:		
	#					pdb.set_trace()
						if flgNewFormat: 
							n = unpackNormal_tag3(vertice.n)
						else:				
							n = unpackNormal(vertice.n)
						if MIRROR_ENABLED and not flgSkinned:
							n['x'] = -n['x']
						objc += "vn %f %f %f\n" % (n['x'],n['y'],n['z'])
						x_cnt += 1
				
				if output_vt:
					for vertice in group['vertices']:
						objc += "vt %f %f 0.0\n" % (vertice.u, 1-vertice.v)
					
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
					
					if flgSkinned: #skinned primitives need to invert face vertex sequence
						lx = l1
						l1 = l3
						l3 = lx
					else:
						if MIRROR_ENABLED:		#if mirror is introduced, non-skinned model also need to invert vertex sequence.
							lx = l1
							l1 = l3
							l3 = lx
	
					if format == 0:
						objc += "f %d/%d/%d %d/%d/%d %d/%d/%d\n" % (l3,l3,l3,l2,l2,l2,l1,l1,l1)
					elif format == 1:
						objc += "f %d %d %d\n" % (l3,l2,l1)
					elif format == 2:
						objc += "f %d//%d %d//%d %d//%d\n" % (l3,l3,l2,l2,l1,l1)
					elif format == 3:
						objc += "f %d/%d %d/%d %d/%d\n" % (l3,l3,l2,l2,l1,l1)
					
				total_vertices += group['nVertices']
			sub_index += 1
		
		
		if compress:
			objc = zlib.compress(objc)
			mtlc = zlib.compress(mtlc)
		
		with open(filename_obj, 'w') as fobj:
			fobj.write(objc)
			
		if output_material:
			with open(filename_mtl, 'w') as fmtl:
				fmtl.write(mtlc)
				
				
args = parser.parse_args()
for fname in glob(args.input):
	print('\nprocessing %s' % fname)
	main(fname)

