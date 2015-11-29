#!/usr/bin/env python

# Kevin Seifert - GPL v2 2015
# 
# This script turns an ASCII tessellation into a maze.
# 
# NOTES: 
# 
# You must use a delimiter (or char change) at the edge of each wall segment.
# For example, in the templates below, '+' is the delimiter.
# Otherwise, the parser doesn't know where the wall segment ends or begins.
# 
# Also, be careful on using _ (underscore) in your template.  
# It looks like mostly whitespace, but it is a solid wall for the entire cell.
# 
# USAGE:
#
#	maze-ify-ascii.py -f YOUR_TEMPLATE	
# 
# EXAMPLES:
#
# example input (ascii template)
# 
#	+---+---+---+---+---+---+---+---+---+---+---+---+---+
#	|   |   |   |   |   |   |   |   |   |   |   |   |   |
#	+---+---+---+---+---+---+---+---+---+---+---+---+---+
#	|   |   |   |   |   |   |   |   |   |   |   |   |   |
#	+---+---+---+---+---+---+---+---+---+---+---+---+---+
#	|   |   |   |   |   |   |   |   |   |   |   |   |   |
#	+---+---+---+---+---+---+---+---+---+---+---+---+---+
#	|   |   |   |   |   |   |   |   |   |   |   |   |   |
#	+---+---+---+---+---+---+---+---+---+---+---+---+---+
#
# example output (maze-ified!)
#
#	+---+---+---+---+---+---+---+---+---+---+---+---+---+
#	|               |               |           |       |
#	+---+---+---+   +---+---+   +   +---+---+   +   +   +
#	|       |           |       |               |   |   |
#	+   +   +---+---+   +---+   +---+---+---+   +   +---+
#	|   |   |                   |       |       |       |
#	+   +   +---+---+---+---+---+   +   +   +---+---+   +
#	|   |                           |                   |
#	+---+---+---+---+---+---+---+---+---+---+---+---+---+
#
#
# You can also use irregularly shaped rooms 
# (which may have more than one solution)
#
# example input
#
#	+---+---+---+---+---+---+---+---+---+---+---+---+---+
#	|               |   |   |   |   |   |   |   |   |   |
#	|               |---+---+---+---+---+---+---+---+---+
#	|               |   |   |   |   |   |   |   |   |   |
#	+---+---+---+---+---+---+---+---+---+---+---+---+---+
#	|   |   |   |   |   |   |   |   |   |   |   |   |   |
#	+---+---+---+---+---+---+---+---+---+---+---+---+---+
#
# example ouput 
#
#	+---+---+---+---+---+---+---+---+---+---+---+---+---+
#	|               |               |                   |
#	|               |   +---+---+   +   +---+---+---+   +
#	|               |       |       |   |           |   |
#	+   +---+---+---+---+   +---+   +   +   +   +---+   +
#	|                       |           |   |           |
#	+---+---+---+---+---+---+---+---+---+---+---+---+---+
#

from random import shuffle
import optparse

class mazeify:

	def __init__(self, allow_diagonal=False):

		self.board = [[]] # char array for maze
		self.deltas = [(1,0),(0,1),(-1,0),(0,-1)] # possible moves

		if allow_diagonal:
			# scan for diagonal patterns - experimental and not tested much :)
			self.deltas = [(1,1),(-1,1),(1,-1),(-1,-1)] + self.deltas

		self.walls = ['/','\\','_','|','-','+','#'] # allowed wall boundaries
		self.corners = ['+'] # protect corner, prevent path from passing through
		self.space = ' ' # empty path (for display)
		self.unvisited = ' ' # any cell that is unvisited
		self.visited = "'" # flag where we have walked.
		self.thickness = '`' # max thickness of wall 
		self.debug = False # verbose debugging
	
	# parse an ASCII tesellation to be used as basis of maze
	def parseTemplate(self,template,x=-1,y=-1):
		self.board = []
		lines = template.split('\n')
		for line in lines:
			cells = list(line)
			self.board.append(cells)
		self.walk(x,y)

	# same as parseTemplate but takes a filename
	def parseTemplateFile(self,filename,x=-1,y=-1):
		with open (filename, "r") as myfile:
			template=myfile.read()	 
		self.parseTemplate(template,x,y)

	#render maze.  use raw=True to see walk data
	def toString(self,raw=False):
		s = ''
		for line in self.board:
			for cell in line:
				s += cell
			s +=  '\n' 
		if not raw:
			s = s.replace(self.visited,self.space)
		return s

	# get value at board at x,y
	def get(self,x,y):
		try:
			#print self.board[y]
			if y >= 0 and y < len(self.board)  \
				and x >= 0 and x < len(self.board[y]):
				return self.board[y][x]
		except Exception as e:
			print e
		return '' # no char

	# set value at board at x,y
	def set(self,x,y,value):
		if y >= 0 and y < len(self.board)  \
			and x >= 0 and x < len(self.board[y]):
			self.board[y][x] = value

	# fill region with char, finding pattern and replacing.
	# (like "fill region" in a paint program, finds boundaries)
	def fill(self,x,y,find,replace,level=0,data=None):
		if self.debug:
			print 'fill pre', x, y, find, replace, level
			print self.toString(True) 

		deltas = self.deltas
		if level == 0:
			data = []
			if len(find) != len(replace):
				print 'Warn: lengths differ. "'+find+'" -> "'+replace+'"'
			if find == replace:
				print 'Warn: same find == replace: '+find
				return data; 

		c = self.get(x,y)
		if c == find: # hit
			data.append((x,y))
			self.set(x,y,replace)
			# scan neighbors
			for delta in deltas:
				x2 = x + delta[0]
				y2 = y + delta[1]
				self.fill(x2,y2,find,replace,level+1,data)			

		if self.debug:
			print 'fill post', x, y, find, replace, level
			print self.toString(True) 

		return data

	# find a random starting place for a walk
 	def findStartPoint(self):
		# aim for middle.
		for y in xrange(len(self.board)/2, len(self.board)-1):
			for x in xrange(len(self.board[y])/2,len(self.board[y])-1):
				c = self.get(x,y)
				if c == self.unvisited: 
					return (x,y)

		# bugger that... just pick the first.
		for y in xrange(len(self.board)-1):
			for x in xrange(len(self.board[y])-1):
				c = self.get(x,y)
				if c == self.unvisited: 
					return (x,y)

	# walk around, knock down walls
	def walk(self,x=-1,y=-1,level=0):

		deltas = list(self.deltas)
		shuffle(deltas)

		if level == 0:
			if x == -1:
				(x,y) = self.findStartPoint()
	
		c = self.get(x,y)

		for delta in deltas:
			(dx,dy) = delta
			x2 = x
			y2 = y
			foundwall = False	
			finished = False	
			scan = ''

			# look past walls for unvisited rooms 		
			path = []
			walls = []
			wall = ''
			wallsize = 0
			while not finished:
				x2 += dx # walk in a direction
				y2 += dy
				scan = self.get(x2,y2)
				path.append((x2,y2))
				if scan ==  '':
					finished = True # dead end
				elif scan in self.corners: 
					finished = True # knicked a corner. ignore.
				elif scan in self.walls: 
					if foundwall and wall != scan:
						finished = True	# hit another wall
					if wallsize > self.thickness:
						finished = True # gone through too many walls 
					foundwall = True # inside a wall
					wall = scan
					walls.append((x2,y2))
					wallsize += 1
				elif foundwall:
					finished = True # looking through wall

			if scan == self.unvisited:
				# hit paydirt, inside a new room
				changed = []
				shuffle(path)

				# knock down wall.  note: must use a delimiter/change
				# or parser won't know where the wall segment boundary ends
				for point in walls:
					(x3,y3) = point
					c = self.get(x3,y3)
					self.fill(x3,y3,c,self.unvisited) # hulk smash!

				# claim empty room
				changed = self.fill(x2,y2,self.unvisited,self.visited)
				for point in changed:
					(x2,y2) = point
					self.walk(x2,y2,level+1)


					
if __name__ == '__main__':


	#  simple template demos
	def demo():

		templates = []
	
		# basic grid
		template = '''
		+---+---+---+---+---+---+---+---+---+---+---+---+---+
		|   |   |   |   |   |   |   |   |   |   |   |   |   |
		+---+---+---+---+---+---+---+---+---+---+---+---+---+
		|   |   |   |   |   |   |   |   |   |   |   |   |   |
		+---+---+---+---+---+---+---+---+---+---+---+---+---+
		|   |   |   |   |   |   |   |   |   |   |   |   |   |
		+---+---+---+---+---+---+---+---+---+---+---+---+---+
		|   |   |   |   |   |   |   |   |   |   |   |   |   |
		+---+---+---+---+---+---+---+---+---+---+---+---+---+
		|   |   |   |   |   |   |   |   |   |   |   |   |   |
		+---+---+---+---+---+---+---+---+---+---+---+---+---+
		|   |   |   |   |   |   |   |   |   |   |   |   |   |
		+---+---+---+---+---+---+---+---+---+---+---+---+---+
		|   |   |   |   |   |   |   |   |   |   |   |   |   |
		+---+---+---+---+---+---+---+---+---+---+---+---+---+
		'''
		templates.append(template)

		# with holes
		template = '''

		+---+---+---+---+---+---+---+---+---+---+---+---+---+
		|               |   |   |   |   |   |   |   |   |   |
		|               +---+---+---+---+---+---+---+---+---+
		|               |   |   |   |   |   |   |   |   |   |
		+---+---+---+---+---+---+---+---+---+---+---+---+---+
		|   |   |   |   |   |   |   |   |   |               |
		+---+---+---+---+---+---+---+---+---+               +
		|   |   |   |   |   |   |   |   |   |               |
		+---+---+---+---+---+---+---+---+---+---+---+---+---+

		'''
		templates.append(template)

		# irregular shape
		template = '''

                                  +---+---+---+---+
                                  |   |   |   |   |
                          +---+---+---+---+---+---+---+---+
                          |   |   |   |   |   |   |   |   |
                      +---+---+---+---+---+---+---+---+---+---+
                      |   |   |   |   |   |   |   |   |   |   |
                  +---+---+---+---+---+---+---+---+---+---+---+---+
                  |   |   |   |   |           |   |   |   |   |   |
              +---+---+---+---+---+           +---+---+---+---+---+---+
              |   |   |   |   |   |           |   |   |   |   |   |   |
              +---+---+---+---+---+           +---+---+---+---+---+---+
                  |   |   |   |   |           |   |   |   |   |   |   |
                  +---+---+---+---+---+---+---+---+---+---+---+---+---+---+
                      |   |   |   |   |   |   |   |   |   |   |   |   |   |
+---+---+---+         +---+---+---+---+---+---+---+---+---+---+---+---+---+
|   |   |   |             |   |   |   |   |   |   |   |   |   |   |   |   |
+---+---+---+             +---+---+---+---+---+---+---+---+---+---+---+---+
|   |   |   |                 |   |   |   |   |   |   |   |   |   |   |   |
+---+---+---+                 +---+---+---+---+---+---+---+---+---+---+---+
|   |   |   |                 |   |   |   |   |   |   |   |   |   |   |   |
+---+---+---+             +---+---+---+---+---+---+---+---+---+---+---+---+
                          |   |   |   |   |   |   |   |   |   |   |   |   |
                      +---+---+---+---+---+---+---+---+---+---+---+---+---+
                      |   |   |   |   |   |   |   |   |   |   |   |   |   |
                  +---+---+---+---+---+---+---+---+---+---+---+---+---+---+
                  |   |   |   |   |   |   |   |   |   |   |   |   |   |
              +---+---+---+---+---+---+---+---+---+---+---+---+---+---+
              |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
              +---+---+---+---+---+---+---+---+---+---+---+---+---+---+
                  |   |   |   |   |   |   |   |   |   |   |   |   |
                  +---+---+---+---+---+---+---+---+---+---+---+---+
                      |   |   |   |   |   |   |   |   |   |   |
                      +---+---+---+---+---+---+---+---+---+---+
                              |   |   |   |   |   |   | 
                              +---+---+---+---+---+---+

		 '''
		templates.append(template)


		template = '''

                 '+---+---+---+---+---+---+---+---+---+---+---+'
                '/   /   /   /   /   /   /   /   /   /   /   /'
               '+---+---+---+---+---+---+---+---+---+---+---+'
              '/   /   /   /   /   /   /   /   /   /   /   /'
             '+---+---+---+---+---+---+---+---+---+---+---+'
            '/   /   /   /   /   /   /   /   /   /   /   /'
           '+---+---+---+---+---+---+---+---+---+---+---+'
          '/   /   /   /   /   /   /   /   /   /   /   /'
         '+---+---+---+---+---+---+---+---+---+---+---+'
        '/   /   /   /   /   /   /   /   /   /   /   /'
       '+---+---+---+---+---+---+---+---+---+---+---+'
      '/   /   /   /   /   /   /   /   /   /   /   /'
     '+---+---+---+---+---+---+---+---+---+---+---+'
    '/   /   /   /   /   /   /   /   /   /   /   /'
   '+---+---+---+---+---+---+---+---+---+---+---+'
  '/   /   /   /   /   /   /   /   /   /   /   /'
 '+---+---+---+---+---+---+---+---+---+---+---+'
'/   /   /   /   /   /   /   /   /   /   /   /'
+---+---+---+---+---+---+---+---+---+---+---+'

		'''

		templates.append(template)

		template = """

		'''+--+------+--+------+--+------+--+------+--+'
		''/    \    /    \    /    \    /    \    /    \\'
		'+      +--+      +--+      +--+      +--+      +'
		''\    /    \    /    \    /    \    /    \    /'
		'''+--+      +--+      +--+      +--+      +--+'
		''/    \    /    \    /    \    /    \    /    \\'
		'+      +--+      +--+      +--+      +--+      +'
		''\    /    \    /    \    /    \    /    \    /'
		'''+--+      +--+      +--+      +--+      +--+'
		''/    \    /    \    /    \    /    \    /    \\'
		'+      +--+      +--+      +--+      +--+      +'
		''\    /    \    /    \    /    \    /    \    /'
		'''+--+      +--+      +--+      +--+      +--+'
		''/    \    /    \    /    \    /    \    /    \\'
		'+      +--+      +--+      +--+      +--+      +'
		''\    /    \    /    \    /    \    /    \    /'
		'''+--+      +--+      +--+      +--+      +--+'
		''/    \    /    \    /    \    /    \    /    \\'
		'+      +--+      +--+      +--+      +--+      +'
		''\    /    \    /    \    /    \    /    \    /'
		'''+--+      +--+      +--+      +--+      +--+'
		''/    \    /    \    /    \    /    \    /    \\'
		'+      +--+      +--+      +--+      +--+      +'
		''\    /    \    /    \    /    \    /    \    /'
		'''+--+      +--+      +--+      +--+      +--+'
		''/    \    /    \    /    \    /    \    /    \\'
		'+      +--+      +--+      +--+      +--+      +'
		''\    /    \    /    \    /    \    /    \    /'
		'''+--+------+--+------+--+------+--+------+--+'

		"""

		templates.append(template)


		maze = mazeify()
		for template in templates:
			print "input template:"
			print ""
			print template
			maze.parseTemplate(template)
			out = maze.toString()
			print ""
			print "output:"
			print ""
			print out


	# parse a file and display
	def parse_file(options):
		maze = mazeify()
		maze.debug = options.debug	
		maze.thickness = int(options.thickness)
		maze.parseTemplateFile(options.filename)
		out = maze.toString()
		print out


	# parse cli options 
	parser = optparse.OptionParser()
	parser.add_option('-f', '--file', action='store', dest='filename', help='ASCII template file', default='') 
	parser.add_option('-d', '--debug', action='store_true', dest='debug', help='enable debug', default=False) 
	parser.add_option('-t', '--thickness', action='store', type="int", dest='thickness', help='wall thickness', default=1) 
	options, args = parser.parse_args()

	if options.filename != '':
		parse_file(options)
	else:
		demo()

