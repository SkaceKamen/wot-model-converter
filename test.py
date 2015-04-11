import wot

reader = wot.ModelReader()

with open("bld401_chouse.primitives", "rb") as prim:
	with open("bld401_chouse.visual", "rb") as vis:
		print(reader.read(prim, vis).getObj())