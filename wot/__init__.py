""" SkaceKamen (c) 2015-2016 """



#####################################################################
# imports

from wot.PackageReader import PackageReader
from wot.XmlUnpacker import XmlUnpacker
from wot.ModelReader import ModelReader
from wot.ModelWriter import OBJModelWriter
from wot.ColladaModelWriter import ColladaModelWriter
from wot.SpaceReader import SpaceReader
from wot.TreesReader import TreesReader

import xml.etree.ElementTree as ET



#####################################################################
# functions

def unpackXml(input_file, output_file):
	with open(input_file,'rb') as f:
		xmlr = XmlUnpacker()
		with open(output_file, 'wb') as o:
			o.write(ET.tostring(xmlr.read(f), 'utf-8'))

def readXml(input_file):
	with open(input_file,'rb') as f:
		xmlr = XmlUnpacker()
		return xmlr.read(f)

def readTree(filename):
	reader = TreesReader()
	with open(filename, 'rb') as f:
		return reader.read(f)
