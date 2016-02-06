from PackageReader import PackageReader
from XmlUnpacker import XmlUnpacker
from ModelReader import ModelReader
from ModelWriter import OBJModelWriter
from SpaceReader import SpaceReader
from TreesReader import TreesReader

import xml.etree.ElementTree as ET

def unpackXml(input_file, output_file):
	with open(input_file,"rb") as f:
		xmlr = XmlUnpacker()
		with open(output_file, "wb") as o:
			o.write(ET.tostring(xmlr.read(f), "utf-8"))
			
def readXml(input_file):
	with open(input_file,"rb") as f:
		xmlr = XmlUnpacker()
		return xmlr.read(f)
	
def readTree(filename):
	reader = TreesReader()
	with open(filename, "rb") as f:
		return reader.read(f)