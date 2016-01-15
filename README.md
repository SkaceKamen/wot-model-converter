# World of Tanks Model Converter
Converts World of Tanks models to wavefront obj format.

## Notes
* script only parse diffuse textures
* all primitive groups are packed into one single obj file at this time
* skinned weight can be extracted but not supported by wavefront obj. Another branch for FBX/DAE exporter would be necessary.
* support new primitives variant used in WoT v0.9.12+ HD models. 
* model mirroring is adapt to standard WG models. Results for models built by other parties are not guaranteed.

## Usage
Script requires .primitives and .visual files (or .primitives_processed and .visual_processed in case of WoT 0.9.10+) of model to create obj (and mtl) file. You can either specify only primitives file and script will assume visual file is in same folder with same name, but different extension, or you can specify path to visual file separatedly.
Script can compress result obj and mtl files using zlib.
```
usage: convert-primitive.py [-h] [-v VISUAL] [-o OBJ] [-m MTL] [-t TEXTURES]
                            [-sx SCALEX] [-sy SCALEY] [-sz SCALEZ]
                            [-tx TRANSX] [-ty TRANSY] [-tz TRANSZ] [-c] [-nm]
                            [-nvt] [-nvn]
                            input

Converts BigWorld primitives file to obj.

positional arguments:
  input                 primitives file path (wildcard accepted)

optional arguments:
  -h, --help            show this help message and exit
  -v VISUAL, --visual VISUAL
                        visual file path
  -o OBJ, --obj OBJ     result obj path
  -m MTL, --mtl MTL     result mtl path
  -t TEXTURES, -t TEXTURES
                        path to textures
  -sx SCALEX, --scalex SCALEX
                        X scale
  -sy SCALEY, --scaley SCALEY
                        Y scale
  -sz SCALEZ, --scalez SCALEZ
                        Z scale
  -tx TRANSX, --transx TRANSX
                        X transform
  -ty TRANSY, --transy TRANSY
                        Y transform
  -tz TRANSZ, --transz TRANSZ
                        Z transform
  -c, --compress        Compress output using zlib
  -nm, --nomtl          don't output material
  -nvt, --novt          don't output UV coordinates
  -nvn, --novn          don't output normals
```

## Example
```convert-primitive.py -o Hull.obj Hull.primitives```
will output 'Hull.obj' with all model data and 'Hull.mtl' with materials

```convert-primitive.py *.primitives_processed```
will process all primitives_processed files and output .obj under current folder.

## Requirements
Python 2.7 - 3.5
