""" SkaceKamen (c) 2015-2016 """



#####################################################################
# imports

import os
import zipfile
import re
import json
import shutil



#####################################################################
# PackageReader

class PackageReader:
	index = None
	packages = None
	cache = None
	wot = None

	def __init__(self, wot_path = None, cache_path = None):
		self.setWotPath(wot_path)
		self.setCachePath(cache_path)

	def setCachePath(self, dir):
		"""Set path where index cache can be stored."""
		self.cache = dir

	def setWotPath(self, dir):
		"""Set path to World of Tanks root folder."""
		self.wot = dir

	def isIndexCache(self):
		"""Returns if index cache exists."""
		return self.cache is not None and os.path.exists(self.indexCachePath())

	def indexCachePath(self):
		"""Returns path to index cache."""
		return self.cache + "/index.cache"

	def loadIndexCache(self):
		"""Loads json encoded cache file."""
		index = None
		try:
			with open(self.indexCachePath(), 'r') as f:
					index = json.load(f)
		finally:
			return index

	def saveIndexCache(self):
		with open(self.indexCachePath(), 'w') as f:
			json.dump(self.index, f)

	def loadIndex(self):
		"""Preloads paths to all files in all packages."""

		# Load package list if neccessary
		if self.packages == None:
			self.loadPackageList()

		# Reset index
		self.index = {}

		# Check for cache
		if self.isIndexCache():
			self.index = self.loadIndexCache()
			if self.index != None:
				return

		# Walk all packages
		for name, pack in self.packages.items():
			# In case some unusual symbols are present in name
			try:
				pack = unicode(pack)
			except UnicodeDecodeError:
				self.warn("Can't decode package name " + pack)
				continue

			# Load package info
			zfile = zipfile.ZipFile(pack)

			# Package name
			name = name[:-4]

			for file in zfile.infolist():
				# Get path and file
				(dirname, filename) = os.path.split(file.filename)

				# Split path to parts
				dirpath = dirname.split('/')

				# Last node is path node
				node = self.index

				# Walk nodes
				for part in dirpath:
					if not part.lower() in node:
						node[part.lower()] = {}
					node = node[part.lower()]

				# Add file to result node
				if filename in node:
					self.warn(file.filename + " is in multiple packages")
				else:
					node[filename.lower()] = pack

		if self.cache != None:
			self.saveIndexCache()

	def warn(self, text):
		"""Prints some kind of warning."""
		print("Warning: %s" % str(text))

	def loadPackageList(self):
		"""Loads paths to all avaible packages"""

		# Identify packages
		pck_re = r".*\.pkg"

		# List containing paths to all packages
		self.packages = {}

		# Location of packages
		base = self.wot + "/res/packages/"
		for pack in os.listdir(base):
			if os.path.isfile(base + pack) and re.match(pck_re, pack):
				self.packages[pack] = base + pack;

	def findFile(self, path):
		"""Returns package containing specified file."""

		# If indexes aren't preloaded yet
		if self.index == None:
			self.loadIndex()

		(dirname, filename) = os.path.split(path)

		# Split path to parts
		dirpath = dirname.split('/')

		# Last node is path node
		node = self.index

		# Walk nodes
		for part in dirpath:
			#Check path part existence
			if part.lower() not in node:
				# print(part.lower(), "not found")
				return None

			node = node[part.lower()]

		# Check existence
		if filename.lower() not in node:
			return None

		return node[filename.lower()]

	def findFileHandle(self, zfile, package_file):
		for file in zfile.infolist():
			if file.filename.lower() == package_file.lower():
				return file
		return None

	def extractFile(self, package_file, result_file):
		return self.extract(package_file, result_file)

	def extract(self, package_file, result_file):
		"""Extracts specified file from wot package."""

		# If file is unpacked, no need to search packages
		if os.path.exists(self.wot + "/res/" + package_file):
			shutil.copyfile(self.wot + "/res/" + package_file, result_file)

		package = self.findFile(package_file)
		(result_dirname, result_filename) = os.path.split(result_file)

		if package == None:
			raise Exception("Failed to find file '" + package_file + "'")

		zfile = zipfile.ZipFile(package)
		file = self.findFileHandle(zfile, package_file)

		if file == None:
			raise Exception("Failed to extract file '" + package_file + "'")

		file.filename = result_filename
		zfile.extract(file, result_dirname)

		return True

	def open(self, package_file, mode):
		"""
			Opens specified file from wot package.
			This handler only supports reading.
		"""

		# If file is unpacked, no need to search packages
		if os.path.exists(self.wot + "/res/" + package_file):
			return open(self.wot + "/res/" + package_file, mode)

		package = self.findFile(package_file)

		if package == None:
			raise Exception("Failed to find file '" + package_file + "'")

		# Open package
		zfile = zipfile.ZipFile(package)

		# We need to find zfile handle to open it
		file = self.findFileHandle(zfile, package_file)

		if file == None:
			raise Exception("Failed to find open '" + package_file + "'")

		return zfile.open(file, mode)

	def walk(self, path, recursive = True):
		"""
			Iterates specified path and returns
			all files found in path. Currently
			works only on packed paths.
		"""

		# @TODO: Combine both packed and unpacked paths
		# so you can walk contents of both at the same
		# time

		# You can specify already found path to speed up process
		if not isinstance(path, list):
			package = self.findFile(path)
		else:
			package = path

		# Path is nonexistent
		if package == None:
			raise Exception("Failed to find path '" + path + "'")

		# Path is actually a file
		if not isinstance(package, list):
			yield "/".join(package)

		# Iter path now
		for key,item in package.items():
			if not isinstance(item, list):
				# Return file path
				yield "/".join(package) + "/" + key
			elif recursive:
				# Iterate folder, if requested
				for p in self.walk(item, recursive):
					yield p
