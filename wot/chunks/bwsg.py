""" SkaceKamen (c) 2015-2016 """



#####################################################################
# imports

from wot.chunks.utility import *
from io import BytesIO



#####################################################################
# get

def get(f, debug=False):
	strings_table = read_table(f)

	if debug:
		print_table(strings_table)

	strings_size = unp('<I', f.read(4))

	strings = {}
	used = {}
	strings_start = f.tell()
	strings_end = 8 + strings_table['entry_size'] * strings_table['entry_count'] + 4 + strings_size
	for item in strings_table['entries']:
		key = unp('<I', item[0:4])
		f.seek(strings_start  + unp('<I', item[4:8]))
		strings[str(key)] = f.read(unp('<I', item[8:12])).decode('utf-8')
		# print(hex2(key), strings[str(key)])

	f.seek(strings_end)

	vertices_table = read_table(f)

	models = []

	index = 0
	for item in vertices_table['entries']:
		key1 = str(unp('<I', item[0:4]))
		key2 = str(unp('<I', item[16:20]))

		for key in [key1, key2]:
			if strings[key] in used:
				used[strings[key]] += 1
			else:
				used[strings[key]] = 1

		model = {
			'name': strings[key1],
			'type': strings[key2],
			'position_from': unp('<I', item[4:8]),
			'position_to': unp('<I', item[8:12]),
			'vertex_count': unp('<I', item[12:16])
		}

		# print(index, model['name'], model['type'], '(', model['position_from'], ' ... ', model['position_to'], ')', model['int4'])

		models.append(model)
		index += 1

	positions_table = read_table(f)

	positions = []

	for item in positions_table['entries']:
		ints = unpack('<5I', item)
		positions.append({
			'type': ints[0],
			'stride': ints[1],
			'size': ints[2],
			'chunk': ints[3],
			'position': ints[4]
		})

	unknown_table = read_table(f)

	chunks = []

	for item in unknown_table['entries']:
		entry = []
		position = 0
		if len(chunks) > 0:
			position = chunks[-1]['position'] + chunks[-1]['size']

		for i in range(unknown_table['entry_size'] // 4):
			entry.append(unp('<I', item[i*4:i*4 + 4]))

		chunks.append({
			'position': position,
			'size': unp('<I', item)
		})

	raw_position = f.tell()

	results = {}
	for model in models:
		blocks = []
		for i in range(model['position_from'], model['position_to']):
			position = positions[i]

			f.seek(raw_position + chunks[position['chunk']]['position'] + position['position'])
			block = {
				'type': position['type'],
				'stride': position['stride'],
				'data': f.read(position['size'])
			}

			if block['type'] == 0:
				vertices = []
				main = BytesIO(block['data'])
				stride = block['stride']

				for i in range(model['vertex_count']):
					vert = vertice()

					(vert.x, vert.y, vert.z) = unpack('<3f', main.read(12))
					vert.n = unpack('<I', main.read(4))[0]
					(vert.u, vert.v) = unpack('<2f', main.read(8))

					if stride == 32:
						(vert.t, vert.bn) = unpack('<2I', main.read(8))
					elif stride == 37:
						# old format skinned
						vert.index_1 = ord(main.read(1))	# bone id for weight1/255.0
						vert.index_2 = ord(main.read(1))	# bone id for weight2/255.0
						vert.index_3 = ord(main.read(1))	# bone id for 1 - weight1/255.0 - weight2/255.0
						vert.weight_1 = ord(main.read(1))
						vert.weight_2 = ord(main.read(1))
						vert.t = unpack('I', main.read(4))[0]
						vert.bn = unpack('I', main.read(4))[0]
					elif stride == 40:
						# new format skinned. Data structure is guess work
						vert.index_1 = ord(main.read(1))	# bone id for weight1/255.0
						vert.index_2 = ord(main.read(1))	# bone id for weight2/255.0
						vert.index_3 = ord(main.read(1))	# bone id for 1 - weight1/255.0 - weight2/255.0
						vert.indexB_1 = ord(main.read(1))	# bone id for weight1 in another primitives
						vert.indexB_2 = ord(main.read(1))	# bone id for weight2 in another primitives
						vert.indexB_3 = ord(main.read(1))	# bone id for remaing weight in another primitives
						vert.weight_1 = ord(main.read(1))
						vert.weight_2 = ord(main.read(1))
						vert.t = unpack('I', main.read(4))[0]
						vert.bn = unpack('I', main.read(4))[0]

					vertices.append(vert)

				block['data'] = vertices

			blocks.append(block)

		info = {
			'name': model['name'],
			'type': model['type'],
			'vertex_count': model['vertex_count'],
			'blocks': blocks
		}
		results[model['name']] = info

		if debug:
			dir = os.path.dirname('vertices/%s' % model['name'])
			if not os.path.exists(dir):
				os.makedirs(dir)
			with open('vertices/%s' % model['name'], 'wb') as out:
				for i in range(model['position_from'], model['position_to']):
					position = positions[i]
					f.seek(raw_position + chunks[position['chunk']]['position'] + position['position'])
					out.write(f.read(position['size']))

	return results


class vertice:
	bn = None
	bnx = None
	bny = None
	bnz = None
	index_1 = 0
	index_2 = 0
	index_3 = 0
	indexB_1 = 0
	indexB_2 = 0
	indexB_3 = 0
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

	def toJSON(self):
		return {
			'x': self.x, 'y': self.y, 'z': self.z,
			'u': self.u, 'v': self.v, 'n': self.n,
			't': self.t, 'bn': self.bn
		}
