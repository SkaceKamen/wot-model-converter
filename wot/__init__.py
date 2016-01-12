from wot.XmlUnpacker import XmlUnpacker
from xml.etree import ElementTree as ET
def unpackXml(input_file, output_file):
	with open(input_file, 'rb') as f:
		xmlr = XmlUnpacker()
		with open(output_file, 'wb') as o:
			o.write(ET.tostring(xmlr.read(f), 'utf-8'))

def readXml(input_file):
	with open(input_file, 'rb') as f:
		xmlr = XmlUnpacker()
		return xmlr.read(f)

