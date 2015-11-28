#!/usr/bin/env python

import os
import sys
import subprocess

# This script indexes the java classes and java jars found under a directory.
# It lists out every single class, file path, and jar file (if any).
# This may be useful for resolving classpath issues (missing jar reference)
# duplicate clas names, or reverse engineering old code.
#
# Example use:
#
#	index_java_classes  YOUR_DIR  > classes.txt
#	index_java_classes  YOUR_DIR  | sort | uniq > classes.txt
#
# Example output (tab-delimited):
#
# 	class: PXLDecoder		file: pxl-2000-decoder/PXLDecoder.class		jar: 
# 	class: PXLDecoder		file: PXLDecoder.class		jar: pxl-2000-decoder/PXLDecoder.jar
# 	class: PXLDecoderGUI		file: pxl-2000-decoder/PXLDecoderGUI.class		jar: 
# 	class: PXLDecoderGUI		file: PXLDecoderGUI.class		jar: pxl-2000-decoder/PXLDecoder.jar
# 	class: WaveFile		file: pxl-2000-decoder/WaveFile.class		jar: 
# 	class: WaveFile		file: WaveFile.class		jar: pxl-2000-decoder/PXLDecoder.jar
#
# Requirements:
#
#	Python 2.7+
#	jar (command line tool included in jdk) 

# logger 
def log(s):
	print s

# strip out class name from file
# todo: parse file, jar
def get_classname(filename):
	classname = os.path.basename(filename)
	classname =  classname.replace('.class', '')
	return classname

# execute command line call
# accepts string or array
def cmd(command):
	try:
		if not isinstance(command, list):
			# cmd is just a string
			cmdargs = command.split()
		else:
			cmdargs = command

		p = subprocess.Popen(command,
							 stdout=subprocess.PIPE,
							 stderr=subprocess.STDOUT)
		return iter(p.stdout.readline, b'')

	except Exception as e:
		log("error: could not execute " + str(cmd))
		log(e)

	return []

# list contents of jar
def ls_jar(jar):
	filelist  = cmd(["jar", "tf", jar])
	return filelist

# printer
def print_class_info(data):
	s = 'class: '+data['class']+"\t\t"+'file: '+data['file']+"\t\t"+'jar: '+data['jar']
	log(s)

def analyze_java(startdir):
	# scan folder
	for dirname, dirnames, filenames in os.walk(startdir):

		if '.git' in dirnames:
			# don't go into any .git directories.
			dirnames.remove('.git')

		for filename in filenames:
			fullpath = os.path.join(dirname, filename)

			if fullpath.endswith('.class'):

				if '$' in fullpath:
					continue # ignore inner

				classname = get_classname(fullpath)
				data = { 
							'file':fullpath,
							'jar':'', # no jar
							'class':classname,
						}

				print_class_info(data)

			elif fullpath.endswith('.jar'):

				jarcontents = ls_jar(fullpath)
				for jarcontent in jarcontents:	

					if '$' in jarcontent:
						continue # ignore inner classes

					jarcontent = jarcontent.strip()
					if jarcontent.endswith('.class'):
						classname = get_classname(jarcontent)
						data = { 
									'file': jarcontent,
									'jar': fullpath,
									'class': classname,
								}	

						print_class_info(data)

if __name__ == '__main__':

	if len(sys.argv) < 2:
		print( "usage: " + sys.argv[0] + ' dirname [dirname dirname ...]') 
		exit(1)

	args = sys.argv[1:]
	for javadir in sys.argv:
		analyze_java(javadir)

