""" SkaceKamen (c) 2015-2016 """



#####################################################################
# imports

import zlib
from wot.ModelWriter import ModelWriter



#####################################################################
# ColladaModelWriter

class ColladaModelWriter(ModelWriter):
	ext = '.dae'
	material = False
	normals = False
	uv = False
	scale = None
	textureBase = ''
	textureCallback = None
	compress = False
	textureCounter = 0

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

	def createTexture(self, path):
		import collada

		img = collada.material.CImage('img_%d' % self.textureCounter, path)
		surface = collada.material.Surface('surface_%d' % self.textureCounter, img)
		sampler = collada.material.Sampler2D('sampler_%d' % self.textureCounter, surface)
		self.textureCounter += 1
		return img, surface, sampler, collada.material.Map(sampler, 'UV')

	def write(self, primitive, filename, filename_material=None):
		# Load required libs now, instead of requiring them for entire library
		import collada
		import numpy

		# Load basic options and use default values if required
		textureCallback = self.textureCallback
		scale = self.scale

		if textureCallback is None:
			textureCallback = self.baseTextureCallback
		if scale is None:
			scale = (1, 1, 1)


		# Create result mesh
		mesh = collada.Collada()
		node_children = []

		# Export all render sets as separate obejcts
		for rindex, render_set in enumerate(primitive.renderSets):
			for gindex, group in enumerate(render_set.groups):
				material = group.material

				name = 'set_%d_group_%d' % (rindex, gindex)
				material_name = material.identifier if material.identifier is not None else name
				material_ref = '%s_ref' % material_name
				effect_name = '%s_effect' % material_name
				matnode = None

				# Create material if requested
				if self.material:
					effect = collada.material.Effect(
						effect_name, [], 'phong', diffuse=(0.5,0.5,0.0), specular=(0,0,0))
					mat = collada.material.Material(
						material_name, material_name, effect)
					matnode = collada.scene.MaterialNode(
						material_ref, mat, inputs=[])

					mesh.effects.append(effect)
					mesh.materials.append(mat)

					if material.diffuseMap:
						img, surface, sampler, effect.diffuse = self.createTexture(
							textureCallback(material.diffuseMap, 'diffuseMap'))
						mesh.images.append(img)
						effect.params.append(surface)
						effect.params.append(sampler)
					if material.specularMap:
						img, surface, sampler, effect.specual = self.createTexture(
							textureCallback(material.specularMap, 'specularMap'))
						mesh.images.append(img)
						effect.params.append(surface)
						effect.params.append(sampler)

					"""
					# How to assign normal map?
					if material.normalMap:
						effect.normal = textureCallback(material.normalMap, "normalMap")
					"""

				vert_values = []
				normal_values = []
				uv_values = []
				indices = []

				for value in group.indices:
					indices.append(value)
					indices.append(value)
					indices.append(value)

				# Add group vertices
				for vertex in group.vertices:
					vert_values.extend(self.multiply(vertex.position, scale))
					normal_values.extend(self.multiply(vertex.normal, scale))
					uv_values.extend(vertex.uv)

				vert_src = collada.source.FloatSource(
					'%s_verts' % name,
					numpy.array(vert_values),
					('X', 'Y', 'Z'))
				normal_src = collada.source.FloatSource(
					'%s_normals' % name,
					numpy.array(normal_values),
					('X', 'Y', 'Z'))
				uv_src = collada.source.FloatSource(
					'%s_uv' % name,
					numpy.array(uv_values),
					('S', 'T'))

				input_list = collada.source.InputList()
				input_list.addInput(0, 'VERTEX', '#%s_verts' % name)
				input_list.addInput(1, 'NORMAL', '#%s_normals' % name)
				input_list.addInput(2, 'TEXCOORD', '#%s_uv' % name)

				geom = collada.geometry.Geometry(
					mesh,
					name,
					name,
					[vert_src, normal_src, uv_src])
				triset = geom.createTriangleSet(
					numpy.array(indices),
					input_list,
					material_ref)
				geom.primitives.append(triset)
				mesh.geometries.append(geom)

				if matnode is not None:
					geomnode = collada.scene.GeometryNode(geom, [matnode])
				else:
					geomnode = collada.scene.GeometryNode(geom, [])

				node_children.append(geomnode)

		node = collada.scene.Node('node0', children=node_children)
		myscene = collada.scene.Scene('myscene', [node])
		mesh.scenes.append(myscene)
		mesh.scene = myscene

		mesh.write(filename)

		return filename
