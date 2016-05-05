""" SkaceKamen (c) 2015-2016 """



#####################################################################
# imports

import argparse
import os
import sys
import wot
from glob import glob



#####################################################################
# Import Tkinter

py3k = sys.version_info >= (3, 0, 0)
can_use_tkinter = True

try:
	if py3k:
		from tkinter import *
		from tkinter import filedialog, ttk
	else:
		from Tkinter import *
		import ttk, tkFileDialog
except:
	can_use_tkinter = False



#####################################################################
# Add libs to path

wd = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(wd, 'lib'))



#####################################################################
# Supported formats and their classes

supported_formats = {
	'obj': wot.OBJModelWriter,
	'collada': wot.ColladaModelWriter
}



#####################################################################
# Initialize command line arguments

show_gui = (len(sys.argv) > 1) and (sys.argv[1] == '-gui') and can_use_tkinter

if not show_gui:
	parser = argparse.ArgumentParser(description='Converts BigWorld primitives file to obj.')
	parser.add_argument('input', help='primitives file path')
	parser.add_argument('-v', '--visual', dest='visual', help='visual file path')
	parser.add_argument('-o', '--output', dest='obj', help='result file path')
	parser.add_argument('-m', '--mtl', dest='mtl', help='result mtl path (only for obj format)')
	parser.add_argument('-t', '-t', dest='textures', help='path to textures')
	parser.add_argument('-sx', '--scalex', dest='scalex', help='X scale')
	parser.add_argument('-sy', '--scaley', dest='scaley', help='Y scale')
	parser.add_argument('-sz', '--scalez', dest='scalez', help='Z scale')
	parser.add_argument('-tx', '--transx', dest='transx', help='X transform')
	parser.add_argument('-ty', '--transy', dest='transy', help='Y transform')
	parser.add_argument('-tz', '--transz', dest='transz', help='Z transform')
	parser.add_argument('-c', '--compress', dest='compress', action='store_true', help='Compress output using zlib')
	parser.add_argument('-nm', '--nomtl', dest='no_mtl', help='don\'t output material', action='store_true')
	parser.add_argument('-nvt', '--novt', dest='no_vt', help='don\'t output UV coordinates', action='store_true')
	parser.add_argument('-nvn', '--novn', dest='no_vn', help='don\'t output normals', action='store_true')
	parser.add_argument('-s', '--silent', dest='silent', help='don\'t print anything', action='store_true')
	parser.add_argument('-f', '--format', dest='format', help='output format, obj or collada', choices=list(supported_formats))



	#####################################################################
	# Load default options

	scale = [1, 1, 1]
	transform = [1, 1, 1]
	compress = False
	output_material = True
	output_vt = True
	output_vn = True
	textures_path = ''
	silent = False
	writer_class = wot.OBJModelWriter



	#####################################################################
	# Load arguments

	args = parser.parse_args()

	if args.textures is not None:
		textures_path = args.textures

	if args.scalex is not None:
		scale[0] = float(args.scalex)
	if args.scaley is not None:
		scale[1] = float(args.scaley)
	if args.scalez is not None:
		scale[2] = float(args.scalez)

	if args.transx is not None:
		transform[0] = float(args.transx)
	if args.transy is not None:
		transform[1] = float(args.transy)
	if args.transz is not None:
		transform[2] = float(args.transz)

	if args.compress:
		compress = True
	if args.no_mtl:
		output_material = False
	if args.no_vt:
		output_vt = False
	if args.no_vn:
		output_vn = False

	if args.silent:
		silent = True

	if args.format:
		writer_class = supported_formats[args.format]


	#####################################################################
	# Load each input file

	for filename_primitive in glob(args.input):
		# Print progress if allowed
		if not silent:
			print('\nprocessing %s' % filename_primitive)

		# Guess correct names
		filename = os.path.splitext(filename_primitive)[0]
		filename_visual = '%s.visual' % filename
		if filename_primitive.endswith('_processed'):
			filename_visual += '_processed'
		filename_obj = '%s%s' % (filename, writer_class.ext)
		filename_mtl = '%s.mtl' % filename

		# Load names from params if specified
		if args.visual is not None:
			filename_visual = args.visual
		if args.obj is not None:
			filename_obj = args.obj
			filename_mtl = filename_obj.replace('.obj', '.mtl')
		if args.mtl is not None:
			filename_mtl = args.mtl

		# Check for existence
		for fpath in (filename_primitive, filename_visual):
			if not os.path.exists(fpath):
				print('Failed to find %s' % fpath)
				sys.exit(1)

		# Intialize readers and writers
		model_reader = wot.ModelReader()
		model_writer = writer_class(
			compress=compress,
			normals=output_vn,
			uv=output_vt,
			material=output_material,
			scale=scale,
			textureBase=textures_path
		)

		# Read and write at same time
		with open(filename_primitive, 'rb') as primitives_f:
			with open(filename_visual, 'rb') as visual_f:
				model_writer.write(model_reader.read(primitives_f, visual_f), filename_obj, filename_mtl)



#####################################################################
# GUI

else:
	def unpack_file():
		if py3k:
			filename_primitive = filedialog.askopenfilename(filetypes=(('Primitives', '*.primitives*'), ('all files', '*.*')))
		else:
			filename_primitive = tkFileDialog.Open(root, filetypes=(('Primitives', '.primitives*'), ('all files', '*.*'))).show()

		if not filename_primitive:
			return

		scale = [1, 1, 1]
		try:
			scale[0] = float(root.text_scalex.get('1.0', END))
			scale[1] = float(root.text_scaley.get('1.0', END))
			scale[2] = float(root.text_scalez.get('1.0', END))
		except:pass

		compress = bool(root.compress.get())
		output_material = bool(root.output_material.get())
		output_vt = bool(root.output_vt.get())
		output_vn = bool(root.output_vn.get())
		textures_path = ''

		if root.writer_format.get() == 1:
			writer_class = wot.OBJModelWriter
		else:
			writer_class = wot.ColladaModelWriter

		fn = os.path.splitext(filename_primitive)
		filename_obj = fn[0] + writer_class.ext
		filename_mtl = '%s.mtl' % fn[0]

		# Intialize readers and writers
		model_reader = wot.ModelReader()
		model_writer = writer_class(
			compress=compress,
			normals=output_vn,
			uv=output_vt,
			material=output_material,
			scale=scale,
			textureBase=textures_path
		)

		filename_visual = filename_primitive.replace('.primitives', '.visual')
		with open(filename_primitive, 'rb') as primitives_f:
			with open(filename_visual, 'rb') as visual_f:
				model_writer.write(model_reader.read(primitives_f, visual_f), filename_obj, filename_mtl)

	root = Tk()
	root.title('Converts BigWorld primitives file')
	root.geometry('200x200')

	label_scalex = ttk.Label(root, text='X scale:')
	label_scalex.grid(row=1, column=0)
	root.text_scalex = Text(root, height=1, width=8)
	root.text_scalex.insert(1.0, '1.0')
	root.text_scalex.grid(row=1, column=1)

	label_scaley = ttk.Label(root, text='Y scale:')
	label_scaley.grid(row=2, column=0)
	root.text_scaley = Text(root, height=1, width=8)
	root.text_scaley.insert(1.0, '1.0')
	root.text_scaley.grid(row=2, column=1)

	label_scalez = ttk.Label(root, text='Z scale:')
	label_scalez.grid(row=3, column=0)
	root.text_scalez = Text(root, height=1, width=8)
	root.text_scalez.insert(1.0, '1.0')
	root.text_scalez.grid(row=3, column=1)

	root.compress = IntVar()
	check_compress = ttk.Checkbutton(root, text='compress', variable=root.compress, onvalue=1, offvalue=0)
	check_compress.grid(row=4, column=0)

	root.output_material = IntVar()
	root.output_material.set(1)
	check_output_material = ttk.Checkbutton(root, text='output material', variable=root.output_material, onvalue=1, offvalue=0)
	check_output_material.grid(row=4, column=1)

	root.output_vt = IntVar()
	root.output_vt.set(1)
	check_output_vt = ttk.Checkbutton(root, text='output vt', variable=root.output_vt, onvalue=1, offvalue=0)
	check_output_vt.grid(row=5, column=0)

	root.output_vn = IntVar()
	root.output_vn.set(1)
	check_output_vn = ttk.Checkbutton(root, text='output vn', variable=root.output_vn, onvalue=1, offvalue=0)
	check_output_vn.grid(row=5, column=1)

	root.writer_format = IntVar()
	root.writer_format.set(1)
	rbutton_obj = ttk.Radiobutton(root, text='obj', variable=root.writer_format, value=1)
	rbutton_collada = ttk.Radiobutton(root, text='collada', variable=root.writer_format, value=2)
	rbutton_obj.grid(row=6, column=0)
	rbutton_collada.grid(row=6, column=1)

	btn_unpack = ttk.Button(root, text='Unpack', command=unpack_file)
	btn_unpack.grid(row=7, column=0, columnspan = 2)

	root.mainloop()
