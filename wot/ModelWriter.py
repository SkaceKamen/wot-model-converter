""" SkaceKamen (c) 2015-2016 """



#####################################################################
# imports

import zlib
from sys import version_info

py3k = version_info >= (3, 0, 0)



#####################################################################
# ModelWriter

class ModelWriter(object):
	ext = ''

	def write(self, primitive, filename):
		pass



#####################################################################
# OBJModelWriter

class OBJModelWriter(ModelWriter):
	ext = '.obj'
	material = False
	normals = False
	uv = False
	scale = None
	textureBase = ''
	textureCallback = None
	compress = False

	def __init__(
			self,
			material=False,
			normals=False,
			uv=False,
			textureBase='',
			textureCallback=None,
			compress=False,
			scale=None):
		self.material = material
		self.normals = normals
		self.uv = uv
		self.textureBase = textureBase
		self.textureCallback = textureCallback
		self.compress = compress
		self.scale = scale

	def baseTextureCallback(self, texture, type):
		return self.textureBase + texture

	def multiply(self, vec1, vec2):
		tpl = False
		if isinstance(vec1, tuple):
			vec1 = list(vec1)
			tpl = True

		for i in range(len(vec1)):
			vec1[i] *= vec2[i]

		if tpl:
			vec1 = tuple(vec1)

		return vec1

	def write(self, primitive, filename, filename_material=None):
		objc = '# Exported by wot-python-lib 2.0.0\n\n'
		mtlc = objc

		# Load basic options and use default values if required
		textureCallback = self.textureCallback
		scale = self.scale

		if textureCallback is None:
			textureCallback = self.baseTextureCallback
		if scale is None:
			scale = (1, 1, 1)

		# Guess mtl name if needed
		if filename_material is None:
			filename_material = filename.replace('.obj', '.mtl')

		# Add reference to material
		if self.material:
			objc += 'mtllib %s\n' % filename_material

		# Vertices offset kept for obejcts
		offset = 0

		# Export all render sets as separate obejcts
		for rindex, render_set in enumerate(primitive.renderSets):
			for gindex, group in enumerate(render_set.groups):
				material = group.material

				name = 'set_%d_group_%d' % (rindex, gindex)
				material_name = material.identifier if material.identifier is not None else name

				objc += 'o %s\n' % name

				# Create material if requested
				if self.material:
					objc += 'usemtl %s\n' % material_name
					mtlc += 'newmtl %s\n' % material_name

					if material.diffuseMap:
						mtlc += 'map_Kd %s\n' % textureCallback(material.diffuseMap, 'diffuseMap')
					if material.specularMap:
						mtlc += 'map_Ks %s\n' % textureCallback(material.specularMap, 'specularMap')
					if material.normalMap:
						mtlc += 'map_norm %s\n' % textureCallback(material.normalMap, 'normalMap')

				# Add group vertices
				for vertex in group.vertices:
					objc += 'v %f %f %f\n' % self.multiply(vertex.position, scale)
					if self.normals:
						objc += 'vn %f %f %f\n' % self.multiply(vertex.normal, scale)
					if self.uv:
						objc += 'vt %f %f\n' % vertex.uv

				# Decide faces format
				format = 0
				if not self.normals and not self.uv:
					format = 1
				elif self.normals and not self.uv:
					format = 2
				elif not self.normals and self.uv:
					format = 3

				# Write indices
				for i in range(0, len(group.indices) - 2, 3):
					l1 = offset + group.indices[i] + 1
					l2 = offset + group.indices[i + 1] + 1
					l3 = offset + group.indices[i + 2] + 1

					'''
					if group.indices[i] > len(group.vertices):
						print('indice #%d is wrong (%d / %d)' % (i, group.indices[i], len(group.vertices)))
					if group.indices[i + 1] > len(group.vertices):
						print('indice #%d is wrong (%d / %d)' % (i + 1, group.indices[i + 1], len(group.vertices)))
					if group.indices[i + 2] > len(group.vertices):
						print('indice #%d is wrong (%d / %d)' % (i + 2, group.indices[i + 2], len(group.vertices)))
					'''

					if format == 0:
						objc += 'f %d/%d/%d %d/%d/%d %d/%d/%d\n' % (l1, l1, l1, l2, l2, l2, l3, l3, l3)
					elif format == 1:
						objc += 'f %d %d %d\n' % (l1, l2, l3)
					elif format == 2:
						objc += 'f %d//%d %d//%d %d//%d\n' % (l1, l1, l2, l2, l3, l3)
					elif format == 3:
						objc += 'f %d/%d %d/%d %d/%d\n' % (l1, l1, l2, l2, l3, l3)

				offset += len(group.vertices)

		# Compress if needed
		if self.compress:
			if py3k:
				objc = bytes(objc, encoding='UTF-8')
				mtlc = bytes(mtlc, encoding='UTF-8')
			objc = zlib.compress(objc)
			mtlc = zlib.compress(mtlc)

		# Save to result filename
		with open(filename, 'wb' if self.compress else 'w') as f:
			f.write(objc)

		if self.material:
			with open(filename_material, 'wb' if self.compress else 'w') as f:
				f.write(mtlc)

		return filename, filename_material
