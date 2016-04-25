#!/usr/bin/env python2.7



#####################################################################
# imports

import argparse
import wot
import os
import sys
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
        import ttk
        import tkFileDialog
except:
    can_use_tkinter = False



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

    scale = [1,1,1]
    transform = [1,1,1]
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

    if args.textures != None:
        textures_path = args.textures

    if args.scalex != None:
        scale[0] = float(args.scalex)
    if args.scaley != None:
        scale[1] = float(args.scaley)
    if args.scalez != None:
        scale[2] = float(args.scalez)

    if args.transx != None:
        transform[0] = float(args.transx)
    if args.transy != None:
        transform[1] = float(args.transy)
    if args.transz != None:
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
        if args.visual != None:
            filename_visual = args.visual
        if args.obj != None:
            filename_obj = args.obj
            filename_mtl = filename_obj.replace('.obj', '.mtl')
        if args.mtl != None:
            filename_mtl = args.mtl

        # Check for existence
        for fpath in (filename_primitive, filename_visual):
            if not os.path.exists(fpath):
                print("Failed to find %s" % fpath)
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

        fn = os.path.splitext(filename_primitive)
        filename_obj = '%s%s' % (fn[0], writer_class.ext)
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

    btn_unpack = ttk.Button(root, text='Unpack', command=unpack_file)
    btn_unpack.pack()

    root.mainloop()
