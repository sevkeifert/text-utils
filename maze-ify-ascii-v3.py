#!/usr/bin/env python
#
# Kevin Seifert - GPL v2 2015
#
# This script turns an ASCII tessellation into a maze.
#
# NOTES ON TEMPLATES:
#
# You should use a delimiter (or char change) at the edge of each
# wall segment.  For example, in the template examples below, the
# '+' is the delimiter.  Otherwise, the parser doesn't know where
# the wall segment ends or begins.
#
# Use the self.visited char (`) to create a line as that the parser will not
# cross.
#
# Use the self.avoid char (~) to prevent scanner from traversing any whitespace
# inside a region.  For example, to prevent the parser from puncturing a wall
# to room inside  a shape.
#
# COMMAND LINE USAGE:
#
#    # create a maze from an ASCII template file
#    maze.py -f YOUR_TEMPLATE
#
#    # generate a simple square maze (no template)
#    maze.py -m square -W 10 -H 10
#
#    # run demo/regression test
#    maze.py
#
#    (or import the mazify class and generate your tessellation on
#    the fly)
#
# OPTIONS:
#
#    see -h for help and options.  You can give the parser hints about how to
#    parse the template file (for example, restricting wall lengths)
#
#
# TEMPLATE EXAMPLES:
#
# example input (ascii template)
#
#   +---+---+---+---+---+---+---+---+---+---+---+---+---+
#   |   |   |   |   |   |   |   |   |   |   |   |   |   |
#   +---+---+---+---+---+---+---+---+---+---+---+---+---+
#   |   |   |   |   |   |   |   |   |   |   |   |   |   |
#   +---+---+---+---+---+---+---+---+---+---+---+---+---+
#   |   |   |   |   |   |   |   |   |   |   |   |   |   |
#   +---+---+---+---+---+---+---+---+---+---+---+---+---+
#   |   |   |   |   |   |   |   |   |   |   |   |   |   |
#   +---+---+---+---+---+---+---+---+---+---+---+---+---+
#
# example output (maze-ified!)
#
#   +---+---+---+---+---+---+---+---+---+---+---+---+---+
#   |               |               |           |       |
#   +---+---+---+   +---+---+   +   +---+---+   +   +   +
#   |       |           |       |               |   |   |
#   +   +   +---+---+   +---+   +---+---+---+   +   +---+
#   |   |   |                   |       |       |       |
#   +   +   +---+---+---+---+---+   +   +   +---+---+   +
#   |   |                           |                   |
#   +---+---+---+---+---+---+---+---+---+---+---+---+---+
#
#
# You can also use irregularly shaped rooms, including holes.
#
# example input
#
#   +---+---+---+---+---+---+---+---+---+---+---+---+---+
#   |               |   |   |   |   |   |   |   |   |   |
#   |               |---+---+---+---+---+---+---+---+---+
#   |               |   |   |   |   |   |   |   |   |   |
#   +---+---+---+---+---+---+---+---+---+---+---+---+---+
#   |   |   |   |   |   |   |   |   |   |   |   |   |   |
#   +---+---+---+---+---+---+---+---+---+---+---+---+---+
#
# example ouput
#
#   +---+---+---+---+---+---+---+---+---+---+---+---+---+
#   |               |               |                   |
#   |               |   +---+---+   +   +---+---+---+   +
#   |               |       |       |   |           |   |
#   +   +---+---+---+---+   +---+   +   +   +   +---+   +
#   |                       |           |   |           |
#   +---+---+---+---+---+---+---+---+---+---+---+---+---+
#

from random import shuffle, randrange, randint
#from sets import Set
import optparse
import sys

class mazeify:

	def __init__(self):

		# logging
		self.debug = False # verbose debugging

		# data
		self.board = [[]] # char array for maze. note: 0,0 is top left

		self.deltas = [(0,-1),(0,1),(-1,0),(1,0)] # scan/fill directions: N S E W
		self.scan_diagonal = True # break diagonal wall patterns
		self.zdeltas = [(1,-1),(-1,-1),(1,1),(-1,1)] + self.deltas # NW NE SW SE
		self.eol = '\n' # expected end-of-line in template
		self.eol2 = '\n' # rendered end-of-line in ouput
		self.pad = 1 # whitespace frame used in transform

		# wall
		self.scan_wall_space = True # scan from space that was previously wall
		self.walls = ['/','\\','_','|','-','+','#'] # allowed wall boundaries
		self.walls_diagonal = ['/','\\'] # which walls are diagonal
		self.walls_vert = self.walls_diagonal + ['|'] # which walls are vertical
		self.corners = ['+'] # protect corner, prevent path from passing through
		self.thickness = 1 # max thickness of wall
		self.length = -1 # max length of wall segment

		# cell flags
		self.space = ' ' # empty path (for display)
		self.unvisited = ' ' # any cell that is unvisited
		self.visited = '`' # flag cells where we have walked
		self.avoid = '~' # flag regions were parser should avoid

		# style tweaks
		self.dot_last_underscore = False  # transform "_ " -> "_."?
		self.close_implied_wall = True  # break wall \_, |_, /_  as "__"?
		self.bias = {} # track bias in walk pattern 

		# available pre-defined maze tessellations
		self.maze_types = [ 'square', 'micro','block','oblique','oblique2',
							'hex','hex2','triangle','diamond']

		# parse space inside cell for micro-templates.
		# all chars cells will be converted to 9 cells, where
		# center char is id.
		self.use_microspace = False # parse space within char cell?
		self.microspace_char_map = {

			'/' :
					[ '  /' ,
					  ' / ' ,
					  '/  ' ],

			'|' :
					[ ' | ' ,  # use + to tighten up joins \| _| |
					  ' | ' ,  # in self.imagePreProcess()
					  ' | ' ],

			'\\' :
					[ '\\  ' ,
					  ' \\ ' ,
					  '  \\' ],

			'_' :
					[ '   ' ,
					  '   ' , # exception: bottom center is id
					  '___' ],

			'-' :
					[ '   ' ,
					  '---' ,
					  '   ' ],

			#'+' :
			#      [ ' + ' , # use solid corner instead
			#        '+++' ,
			#        ' + ' ],

			# all others are solid blocks
		}


	# parse/import an ASCII tesellation to be used as basis of maze
	# creates maze by default (walks)
	def parseTemplate(self, template, create_maze=True):

		# apply transform for
		template = self.transform(template)
		if self.debug:
			print("transform:")
			print(template)

		self.board = []

		# normalize end of line
		template = template.replace("\r\n",self.eol) # dos
		if self.eol != "\r":
			template = template.replace("\r",self.eol) # mac
		if self.eol != "\n":
			template = template.replace("\n",self.eol) # nix

		lines = template.split(self.eol)

		for line in lines:
			cells = list(line)
			self.board.append(cells)

		if create_maze:
			self.createMaze()


	# same as parseTemplate but takes a filename
	def parseTemplateFile(self,filename,create_maze=True):
		with open (filename, "r") as myfile:
			template=myfile.read()	
		self.parseTemplate(template, create_maze)


	#render maze.  use raw=True to see raw walk/fill data
	def toString(self, raw=False):
		s = ''
		for line in self.board:
			for cell in line:
				s += cell
			s += self.eol2

		if not raw:
			s = s.replace(self.visited,self.space)
			# apply inverse transform
			s = self.inverse_transform(s)

		# sharpen underscore corners
		if self.dot_last_underscore:
			for (find,replace) in [('_ ','_.'),(' _','._')]:
				s = s.replace(find,replace)

		return s


	# are x,y in bounds?
	def inBounds(self, x, y, raise_exception=False):
		if y >= 0 and y < len(self.board) and x >= 0 and x < len(self.board[y]):
			return True

		if raise_exception:
			raise Exception('x,y not in bounds'+str(x)+','+str(y))
		return False


	# get value at board at x,y
	def get(self,x,y):

		if not self.inBounds(x,y):
			return ''

		try:
			return self.board[y][x]
		except Exception as e:
			print(e)

		return '' # no char


	# macro char (9-cell) start point
	def getMacroCharTopLeftPos(self,x,y):
		# snap to first multiple of 3	
		(x0,y0) = (self.pad + ((x-self.pad)//3)*3, self.pad+((y-self.pad)//3)*3)
		return (x0,y0)


	# macro char (9-cell) center point
	def getMacroCharIdPos(self,x,y):
		# snap to first multiple of 3	
		(x0,y0) = self.getMacroCharTopLeftPos(x,y)

		# check special case: _ (bottom center)
		(x1,y1) = (x0+1,y0+2)  
		c1 = self.get(x1,y1)
		if c1 == '_':
			return (x1,y1) 

		# default: else return middle center
		return (x0+1,y0+1)


	# get macro char value at board at x,y
	def getMacroCharValue(self,x,y):

		if not self.inBounds(x,y):
			return ''

		(x0,y0) = self.getMacroCharIdPos(x,y)

		# translate space flags
		c0 = self.get(x0,y0)
		if c0 in [self.visited,self.unvisited]:
			return self.space

		# return char at pos 
		return c0


	# set value at board at x,y
	def set(self, x, y, value):
		if not self.inBounds(x,y,raise_exception=True):
			return False

		self.board[y][x] = value

		return True


	# update a 9-cell macro character
	# return changed points
	def setMacroChar(self, x, y, value):

		changed = []
		if not self.inBounds(x,y,raise_exception=True):
			return changed

		# does new value differ from old value?
		c1 = self.get(x,y) # current
		if c1 == value:
			return changed
		
		# is this whitespace?
		if c1 in [self.visited,self.unvisited]:
			# safe to replace directly
			self.board[y][x] = value
			changed.append((x,y))
			return changed

		# does new value differ from old macro value id?
		# find start of macro char
		(x2,y2) = self.getMacroCharTopLeftPos(x,y)
		(x3,y3) = (x2+1, y2+1) # id pos at center
		old_id = self.get(x3,y3)
		if old_id == value:
			return changed # nothing to do

		# does new value collide with old value shape?
		charmap_old = self.getMacroCharMap(old_id)
		(dx,dy) = (x-x2, y-y2) # relative pos in char map
		if charmap_old[dy][dx] != ' ':
			# non-mask value was hit
			# overwrite old char, update all non-masked chars
			# change as little as possible
			for j in range(3):
				for i in range(3):
					c2 = charmap_old[j][i]
					if c2 != ' ':
						(x4,y4) = (x2+i,y2+j)
						self.board[y4][x4] = value
						changed.append((x4,y4))

		return changed # all points updated


	# find all points matching a given character
	# return array of points
	def findChar(self,find):
		points = []

		# scan all cells
		for y,row in enumerate(self.board):
			for x,c in enumerate(row):
				if c == find:
				 	points.append((x,y))	

		return points


	# check a 2d rectangular block at point (x,y) for a pattern.
	# return True if all chars in a 'find' pattern are set.  can
	# scan multiple rows.  
	# 'find' is an array of strings. for example:
	# 	['row1','row2']
	def hasPatternAt(self, find, x, y):

		h = len(find)
		w = len(find[0])
		(i, j) = (0,0) # relative to find pattern

		while True:
			c_is = self.get(x+i,y+j)
			c_should_be = find[j][i]

			if c_is == c_should_be:
				i += 1 # hit 
			else:
				return False

			if i >= w:
				j += 1 # wrapped, scan next row
				i = 0

			if j >= h: # hit end of rows. full match!
				return True	

		# end while

		return False


	# 2d pattern matching.	
	# like self.findChar(), but accepts a pattern that may span
	# multiple rows.  
	# For example to find:
	# 	hello
	# 	there
	# search for: 
	#	['hello','there']
	# patterns must be rectangular.
	# x,y is the start point for the scan.
	# this will return an array of top-left points matching the
	# pattern.  
	def findPattern(self, find, x=0, y=0):

		points = []

		h = len(self.board)
		w = len(self.board[0]) # rectangular

		h2 = len(find)
		if h2 == 0:
			return []

		w2 = len(find[0])
		if w2 == 0:
			return []

		(rowidx, colidx) = (0,0)

		# scan every cell starting at x,y and up
		for j in range(y,h):

			rowstart = x # skip first row of points 0,x-1
			if j != y:
				rowstart = 0

			for i in range(rowstart, w):
				if self.hasPatternAt(find,i,j):
					points.append((i,j))	

		return points


	# get a block of chars starting at top-left x,y, with width,height w,h 
	# returns an array of lines 
	def getBlockAt(self,x,y,w,h):
		lines = []	
		for j in range(y,y+h):
			line = ''
			for i in range(x,x+w):
				line += self.get(i,j)
			lines.append(line)
		return lines


	# 2d set: set a rectangular block pattern in the board at x,y.
	def setBlock(self, x, y, pattern):
		h = len(pattern)
		w = len(pattern[0])
		for j in range(h):
			for i in range(w):
				self.set(x+i, y+j, pattern[j][i])


	# 2d find/replace.
	# find all points matching a given character. replace with new
	# values.  the find/replace patterns are arrays of strings
	# that can span multiple rows.
	#
	# note on overlapping pattern matches: this replaces all found matches on
	# one scan (it does NOT rescan after each replace operation.)  This means
	# even if a replace operation alters the board, all initial matches
	# are still replaced.
	def replace(self, find, replace):

		if self.debug:
			print("before replace: " + str(find) + ' -> ' + str(replace))
			print(self.toString(raw=True))

		points = self.findPattern(find)
		for (x,y) in points:
			self.setBlock(x, y, replace)

		if self.debug:
			print("after replace: " + str(find) + ' -> ' + str(replace))
			print(self.toString(raw=True))


	# fill region with char, finding pattern and replacing.  (like
	# "fill polygon" in a paint program, finds boundaries) this is
	# a replacement for self.fillRecursive(), where the old function
	# was converted from a simpler recusive function to standard
	# function.  otherwise the old function was sometimes hitting
	# too many levels of recursion.  
	# added support for macro char replacements.
	def fill(self,x,y,find,replace,level=0,data=None,use_recursion=False):

		if use_recursion:
			return self.fillRecursive(x,y,find,replace,level,data)
		else:
			points = [(x,y)]
			return self.fillPoints(points, find, replace, level, data)


	# non-recursive function.
	# fill region with char, finding pattern and replacing.
	# like self.fill, but accepts mulitple points.
	def fillPoints(self, points, find, replace, level=0, data=None):

		if data == None:
			data = []

		if len(find) != len(replace):
			print('Warn: lengths differ. "'+find+'" -> "'+replace+'"')
		if find == replace:
			print('Warn: same find == replace: '+find)
			return data;

		next_scan = points # init loop
		walls = []

		# what wall directions will be scanned in ASCII template?
		# note: these are returned by reference
		deltas = []

		if self.scan_diagonal and find in self.walls_diagonal:
			deltas = self.zdeltas # break diagonal wall patterns
		else:
			deltas = self.deltas # zdelta won't detect X whitespace bound

		while(len(next_scan) > 0):

			# process queued set of points
			points = next_scan # the current working set
			next_scan = []
			this_scan = []

			# process point
			if self.debug:
				print("")
				print('fill pre', points, find, replace, level)
				#print 'fill pre', x, y, find, replace, level
				#print "macro id ", self.getMacroCharIdPos(x,y), self.getMacroCharValue(x,y)
				print(self.toString(True))

			# start scanning the set of points
			for (x,y) in points:
	
				x2 = x
				y2 = y
				# scan the point and all neighboring points in large straight
				# paths when possible (minimize recursion)
				# include current point
				for (dx,dy) in deltas: 

					finished = False
					while not finished: 

						c = self.get(x2,y2)

						if c != find:
							break #not a match

						# pattern was found!
						self.set(x2,y2,replace)

						# don't retest this cell	
						data.append((x2,y2))
						this_scan.append((x2,y2))

						# count removed wall segments to allow for implicit
						# wall boundaries.  set with -l flag
						# for example, (__)(__) = ____
						if self.length != -1 and c in self.walls:
							(xw,yw) = (x2,y2)
							if self.use_microspace:
								(xw,yw) = self.getMacroCharTopLeftPos(x2,y2)
							if not ( (xw,yw) in walls ):
								walls.append((xw,yw))
								if len(walls) >= self.length:
									# end. maxed out wall segment changes
									return data
						x2 += dx
						y2 += dy

					# end while
				# end for deltas

				if self.debug:
					print('fill post', x, y, find, replace, level)
					print(self.toString(True))

			# end for points

			# save snapshot of all new neighboring points encountered
			for (x3,y3) in this_scan:
				for (dx,dy) in deltas:
					x4 = x3 + dx
					y4 = y3 + dy
					if self.inBounds(x4,y4) and not ((x4,y4) in next_scan) and not ((x4,y4) in data):
						next_scan.append((x4,y4))

		# end while next_scan

		if self.debug:
			print('**** scan pass done ****')

		return data		


	# fill "outside" region of shapes (anything containing ~ avoid)
	def initOutside(self):
		data = []
		# flag "outside of shape"
		if self.pad > 0:
			self.fill(0,0,self.unvisited,self.visited)	

		points = self.findChar(self.avoid)
		if self.debug:
			print("find avoid", points)

		for (x,y) in points:
			# block off any region containing ~
			self.fill(x,y,self.avoid,self.unvisited)	
			self.fill(x,y,self.unvisited,self.visited)

		if self.debug:
			print("**** init complete ****")


	# rules to connect known edge patterns between 3x3 macrospace characters.
	# ignore some micro space between fonts, and tighten up graph prior to
	# walk().  
	def imagePreProcess(self):

		patterns = [

			# find/replace blocks
			# syntax:

			# [ ['find row 1','find row 2'], ['replace row1','replace row2'] ],


			# connect edges:
			# _
			# |  _|_  |_ and _|

			[ ['_','|'], ['+','|'] ],
			[ ['_ | _'], ['_+++_'] ],
			[ ['| _'], ['++_'] ],
			[ ['_ |'], ['_++'] ],

			
			# connect sloppy edges:
			# 
			#  -|  |-
			
			[ ['- |'], ['-++'] ],
			[ ['| -'], ['++-'] ],


			# connect very sloppy edges:
			# 
			# /_  and _\

			[ ['/  ___'], ['+++___'] ],
			[ ['___  \\'], ['___+++'] ],

			# sharpen edges (insert well-defined corner):
			#           \  /
			#  \/  /\   /  \
			
			[ ['\\/'], ['++'] ],
			[ ['/\\'], ['++'] ],
			
			[ ['\\','/'], ['+','+'] ],
			[ ['/','\\'], ['+','+'] ],

			# connect edges:
			# 
			#  \|  |/  /|  and |\ 

			[ ['\\ |'], ['\\++'] ],
			[ ['| /'], ['++/'] ],
			[ ['/ |'], ['/++'] ],
			[ ['| \\'], ['++\\'] ],


			# add more connector rules here ...

		]	

		for find,replace in patterns:
			self.replace(find,replace)


	# post image processing.  clean up implied horizontal/vertical wall
	# artifacts using rules. 
	# Note: self.board will still contain previous substitions along with `
	# markers and any changes made during walk().
	def imagePostProcess(self):

		patterns = [

			# find/replace blocks
			# syntax:

			# [ ['find row 1','find row 2'], ['replace row1','replace row2'] ],

			# example: simpify edges with _:
			#        _              __       _
			# change |  to  |, and  |   to  |

			#[ ['``_`', '`+++', '``|`'] , ['````', '`+++', '``|`'] ],
			#[ ['`_``', '+++`', '`|``'] , ['````', '+++`', '`|``'] ],


			# add more rules here ...

		]	

		# close implied horizonal walls in microtemplates
		if self.close_implied_wall:
			patterns.append([['`','+'] , ['_','+']])

		for find,replace in patterns:
			self.replace(find,replace)


	# scan the entire ASCII map, build the maze
	def createMaze(self):

		if self.use_microspace:
			self.imagePreProcess()
			if self.debug:
				print("**** imagePreProcess complete ****")

		self.initOutside()

		# aim start in for middle.
		h = len(self.board)-1
		w = len(self.board[h//2])-1

		ystart = randint(0,3* h//4)
		xstart = randint(0,3* w//4)

		data = [] # track where we've checked
		for y in range(ystart, h):
			for x in range(xstart,w):
				c = self.get(x,y)
				if c == self.unvisited:
				 	self.walk(x,y,0,data)	

		# scan all cells
		for y,row in enumerate(self.board):
			for x,c in enumerate(row):
				if c == self.unvisited:
				 	self.walk(x,y,0,data)	

		if self.use_microspace:
			self.imagePostProcess()
			if self.debug:
				print("**** imagePostProcess complete ****")


	# return a random set of deltas, corrected for bias.
	# put least used first, most used last.
	def getDeltas(self):
	
		deltas = list(self.deltas) # make a random copy
		shuffle(deltas)

		if len(self.bias) > 0:
			# help even the scales
			# put least used up front
			rare = min(self.bias, key=self.bias.get)
			deltas.remove(rare)
			deltas = [rare] + deltas

			# most used goes to end
			notrare = max(self.bias, key=self.bias.get)
			if notrare != rare:
				deltas.remove(notrare)
				deltas =  deltas + [notrare];
			deltas.remove(notrare)

		return deltas;


	# walk around, knock down walls starting at x,y position
	def walk(self,x=0,y=0,level=0,data=None):

		if level == 0:
			data = []
			self.bias = {} # reset walk biases

		## optimize walk: only run one full scan on each space
		if (x,y) in data:
			return data
		else:
			data.append((x,y))

		c = self.get(x,y) # current char

		# scan pattern
		deltas = self.getDeltas() 
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
				scan = self.get(x2,y2) # look ahead char

				path.append((x2,y2))
				if scan ==  '':
					finished = True   # dead end
				elif scan in self.corners:
					finished = True # knicked a corner. ignore.
				elif scan in self.walls:
					wallsize += 1
					if foundwall and wall != scan:
						finished = True	# hit another wall
					if wallsize > self.thickness:
						finished = True # gone through too many walls
					foundwall = True # inside a wall
					wall = scan
					walls.append((x2,y2))
				elif foundwall: # scan not in self.walls
					finished = True # scan moved past the wall

			if scan == self.unvisited:
				# hit paydirt, inside a new room

				# record walk pattern
				if not (delta in self.bias):
					self.bias[delta] = 1
				else:
					self.bias[delta] += 1

				changed = []

				# knock down wall.  note: must use a delimiter/change
				# or parser won't know where the wall segment boundary ends
				walls_changed=[]
				for point in walls:
					(x3,y3) = point
					c = self.get(x3,y3)
					
					#replace = self.getReplaceChar(x3,y3,dx,dy,c)
					replace = self.unvisited
					
					changed = self.fill(x3,y3,c,replace) # hulk smash!
					walls_changed += changed

				# claim empty room
				changed = self.fill(x2,y2,self.unvisited,self.visited)
				shuffle(changed)

				# rescan from every newly discovered space.
				# note: this is re-scanning from inside previous wall-space.
				# this is intentional (in case walls are staggered).
				if (x,y) in changed:
					changed.remove((x,y)) # don't rescan from the initial point

				if not self.scan_wall_space:
					for point in walls_changed:
						if point in walls_changed:
							walls_changed.remove(point) # don't scan wall space

				for point in changed:
					(x2,y2) = point
					self.walk(x2,y2,level+1,data)


	# generate basic ASCII tessellations
	def tessellate(self, w, h, type='square'):

		if not (type in self.maze_types):
			print('Error: maze_type not defined. ')
			print('The tessellation type must be one of the following:')
			print(self.maze_types)
			return ''	

		#all patterns
		patterns = {}
		
		# produce wxh standard square grid
		pattern = ''
		tile = ''
		tile += "+---" * w + '+' + self.eol
		tile += "|   " * w + '|'+ self.eol
		tile = tile * h
		tile += "+---" * w + '+' + self.eol
		patterns['square'] = tile

		# produce wxh micro square grid
		pattern = ''
		head = '_' + '_' * 2*w + self.eol
		foot = ''
		tile = '|_' * w +  '|'+ self.eol
		pattern = head + tile * h + foot
		patterns['micro'] = pattern

		# produce wxh block grid
		pattern = ''
		head = '#`' * (2*w+1) + self.eol
		foot = head
		tile = '#   ' * w +  '#'+ self.eol
		pattern = (head + tile) * h + foot
		patterns['block'] = pattern

		# produce wxh oblique grid (left slant)
		pattern = ''
		head = '+---' * (w) + '+' + self.eol
		foot = head
		tile = '\\   ' * w +  '\\'+ self.eol
		pattern = head
		for i in range(h):
			pattern += ' ' * (2*i+1) + tile
			pattern += ' ' * (2*i+2) + foot
		patterns['oblique'] = pattern

		# produce wxh oblique grid (right slant)
		pattern = ''
		head = '+---' * (w) + '+' + self.eol
		foot = head
		tile = '/   ' * w +  '/'+ self.eol
		pattern = ' ' * (2*h) + head
		for i in range(h):
			pattern += ' ' * (2*h-2*i-1) + tile
			pattern += ' ' * (2*h-2*i-2) + foot
		patterns['oblique2'] = pattern


		# produce wxh hex grid 
		pattern = ''
		head  = ' __   ' * w + self.eol
		tile  = '/  \__' * w + self.eol
		foot  = '\__/  ' * w + self.eol
		tile2 = '/  \__' * w + '/' + self.eol
		foot2 = '\__/  ' * w + '\\' + self.eol
		pattern = head
		for i in range(h):
			if i == 0:
				pattern += tile
			else:
				pattern += tile2
			if i == h-1:
				pattern += foot
			else:
				pattern += foot2

		patterns['hex'] = pattern


		# produce wxh large hex grid 
		pattern = ''
		head  = '  ____      ' * w + self.eol
		tile1 = ' /    \     ' * w + self.eol
		tile2 = '/      \____' * (w-1) + '/      \\' + self.eol
		tile3 = '\      /    ' * w + self.eol
		tile4 = ' \____/     ' * w + self.eol

		pattern = head
		for i in range(h):
			pattern += tile1
			pattern += tile2
			pattern += tile3
			pattern += tile4
		patterns['hex2'] = pattern

		# produce wxh triangle grid 
		tile0  = ' '*2 + '_' * (4*w -4) + self.eol
		tile1  = ' /\ '  * (w) + self.eol
		tile2  = '/__\\' * (w) + self.eol
		tile3  = '\  /'  * (w) + self.eol
		tile4  = ' \/_' + '_\/_' * (w-2) + '_\/ ' + self.eol
		pattern = ''
		pattern = tile0
		for i in range(h//2):
			pattern += tile1
			pattern += tile2
			pattern += tile3
			pattern += tile4
		patterns['triangle'] = pattern

		# produce wxh small diamond grid 
		pattern = ''
		tile1 = '/\\' * w + self.eol
		tile2 = '\\/' * w + self.eol
		for i in range(h):
			pattern += tile1
			pattern += tile2
		patterns['diamond'] = pattern


		# add more tile patterns here ...

		#print pattern
		return patterns[type]


	# parse microspace into microspace chars
	# convert 1 cell -> 9 cell
	# center char is primary id
	def getMacroCharMap(self,c):
		if c in self.microspace_char_map:
			return self.microspace_char_map[c]

		c2 = [c*3]*3 # else solid 3x3 block
		return c2


	# parse char microspace into macrospace
	# add a whitespace frame around template, for 'outside' detection
	# optional: convert 1-cell into 9-cell blocks (3x3)
	# this is all just string based manipulation, prior to converting the
	# template to a character array represented by self.board.
	def transform(self, template):

		if self.use_microspace:
			# optional: convert 1-cell -> 9-cell
			lines = template.split(self.eol)
			template2 = ''

			for line in lines:
				# sub lines
				temp = ['','','']	
				for c in line:
					chars = self.getMacroCharMap(c)
					for i in range(3):
						temp[i] += chars[i]	

				for i in range(3):
					template2 += temp[i] + self.eol

			template = template2
		
		# add whitespace frame, clean up right end
		# frame will allow detecting "outside" of shape with fill
		lines = template.split(self.eol)
		max_len = len(max(lines, key=len)) # longest string length
		template2 = ''
		top_bottom =  ' '*(max_len + 2*self.pad) + self.eol
		for i in range(self.pad):
			template2 += top_bottom

		for line in lines:
			line =line.rstrip()
			tmp = len(line)
			template2 += ' '*self.pad + line + ' '*(self.pad+max_len-tmp) + self.eol
		for i in range(self.pad):
			template2 += top_bottom


		return template2


	# parse macrospace into normal space.
	# 9-cell -> 1-cell for entire string.
	def inverse_transform(self, transform):

		# compress 9-cell -> 1-cell
		if self.use_microspace:
			t2 = ''
			lines = transform.split(self.eol2)
			for y,row in enumerate(lines):
				if(y%3) == 0: # top of row block
					for x, c in enumerate(row):
						if (x%3) == 0: # top of cell block
							cm = self.getMacroCharValue(x,y)
							#print x,y,c, '->',cm
							t2 += cm
					t2 += self.eol2
			transform = t2

		return transform


	# print board with all x,y indexes, for debugging
	def dump(self):
		for y,row in enumerate(self.board):
			for x,c in enumerate(row):
				print(str((x,y)).ljust(10), c)


	# a temporary method for random testing
	def unittest(self):
		self.use_microspace = False

		self.tessellate(10,10,'oblique')

		t =r'''

a test template

'''

		#self.parseTemplate(t,create_maze=False)

		#points = self.findChar('\\')
		#print points
		#block = self.getBlockAt(57,52,10,10)		
		#print block
		#self.dump()
		#print self.replace(['test','test'],['work','asdf'])
		#self.scan_diagonal = True
		#self.fill(x,y,'\\',' ')
		#self.dump()
		#print self.toString()

		#print self.findPattern(['est','est'])
		#print self.hasPatternAt(['test0','test1','test2'],2,1)

		#for i in range(9*3):
		#	print "test",i	
		#	print self.toString(raw=True)
		#	self.setMacroChar(i,0,'|');
		#	print self.toString(raw=True)
		#	print "--"



# end class

	
if __name__ == '__main__':

	# process cli options, regression testing

	# pass along cli options to maze
	def apply_options(maze, options):
		maze.debug = options.debug	
		maze.thickness = int(options.thickness)
		maze.length = int(options.length)
		maze.scan_wall_space = not options.no_wall_scan
		maze.dot_last_underscore = options.dot_last_underscore
		maze.use_microspace = options.use_microspace
		maze.close_implied_wall = not options.no_close_implied_wall
		maze.scan_diagonal = not options.no_zigzag


	#  simple template parsing demos / regression tests
	def demo(options):

		default_parser = mazeify()
		apply_options(default_parser,options)

		# run through predefined regular shapes
		if options.test == -1:
			print("predefined tessellations")
			types = default_parser.maze_types
			for maze_type in types: 
				print("type: " + maze_type)
				options.maze = maze_type	
				create_maze(options)
			print("--")	

		parsers = [] # custom parsing options
		templates = [] # test templates


		template = r"""
    Example: mixed tessellations are also possible

    Salvidor Dali Melting Maze:
	
                            
               +---+---+---+`````+---+------+---+-----+---+       
              /   /   /   /     /   /      /   /     /   /        
             +---+---+---+-----+---+------+---+-----+---+------+ 
            /   /   /   /     /   /      /   /     /   /      /   
           +---+---+---+-----+---+------+---+-----+---+------+    
          /   /   /   /     /   /      /   /     /   /      /     
         +---+---+---+-----+---+------+---+-----+---+------+---+ 
        /   /   /   /     /   /      /   /     /   /      /   / 
       +---+---+---+-----+---+------+---+-----+---+------+---+ 
      /   /   /   /     /   /      /   /     /   /      /   / 
     +---+---+---+-----+---+------+---+-----+---+------+---+ 
    /   /   /   /     /   /      /   /     /   /      /   / 
   +---+---+---+-----+---+------+---+-----+---+------+---+ 
  /   /   /   /     /   /      /   /     /   /      /   / 
 +---+---+---+-----+---+------+---+-----+---+------+---+ 
    /   /   /     /   /      /   /     /   /      /   / 
   +---+---+-----+----+-----+---+-----+---+------+---+ 
      /     \    /     \    /    \    /    \    /    \ 
      \     /    \     /    \    /    \    /    \    / 
       +---+------+---+------+--+------+--+-----+--+ 
      /     \    /     \    /    \    /    \   /    \ 
      \     /    \     /    \    /    \    /   \    / 
       +---+      +---+      +--+      ++++    +--+ 
      /     \    /     \    /    \    /    \  /    \ 
     +       +--+       +--+      +--++     ++      + 
      \     /    \     /    \    /     \   /  \    / 
       +---+      +---+      +--+       +-+    ++++ 
           \      /   \     /    \     /   \    /      
            \    /     \   /      \   /     \  /      
             +--+       +-+        +-+      +++   
                 \     /   \      /   \      /       
                  \   /     \    /     \    /       
                   +-+       +--+       +--+
                      \     /    \     /     
                       +---+      +---+  
                            \`````|   
"""	
		templates.append(template)
		parsers.append(None) # default parser

#### test

		# irregular, with diagonal walls, text, protected whitespace
		# be careful with trailing whitespace
		# can use with the -z diagonal wall flag
		template = r"""
       Help Mr. Food Travel Through the Intestines ;-)
                                                                
   start                                                        
          \                                                     
   \```````\      ______      ______                            
    \       \____/      \____/      \____                       
     \      /    \      /    \      /    \                      
      \____/      \____/      \____/      \____                 
      /    \      /    \      /    \      /    \                
     /      \____/      \____/      \____/      \               
     \      /    \      /    \      /    \      /               
      \____/      \____/      \____/      \____/                
      /    \      /    \      /    \      /    \                
     /      \____/      \____/      \____/      \____           
     \      /    \      /    \      /    \      /    \          
      \____/      \____/      \____/      \____/      \____     
      /    \      /    \      /    \      /    \      /    \    
     /      \____/      \____/      \____/      \____/      \   
     \      /    \      /    \      /    \      /    \      /   
      \____/      \____/      \____/      \____/      \____/    
      /    \      /    \      /    \      /    \      /    \    
     /      \____/      \____/      \____/      \____/      \   
     \      /    \      /    \      /    \      /    \      /   
      \____/      \____/      \____/      \____/      \____/    
      /    \      /    \      /    \      /    \      /    \    
     /      \____/      \____/      \____/      \____/      \   
     \      /    \      /    \      /    \      /    \      /   
      \____/      \____/      \____/      \____/      \____/    
           \      /    \      /    \      /    \      /    \    
            \____/      \____/      \____/      \____/      \   
                 \      /    \      /    \      /    \       \  
                  \____/      \____/      \____/      \  end  \ 
                                                       \```````\
                                                                
"""	
		templates.append(template)

		# tune parser: explode diagonal walls
		maze = mazeify()
		apply_options(maze,options)
		maze.scan_diagonal = True
		parsers.append(maze)


#### test 

		template = r"""

Mr Smiley
                    __    __    __    __                          
                 __/  \__/  \__/  \__/  \__                       
              __/  \__/  \__/  \__/  \__/  \__                    
           __/  \__/  \__/  \__/  \__/  \__/  \__                 
start   __/  \__/  \__/  \__/  \__/  \__/  \__/  \__              
     __/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \             
    `  \__/  \__/~ \__/  \__/  \__/  \__/~ \__/  \__/              
    \__/  \__/        \__/  \__/  \__/        \__/  \__   
  __/  \__/  \  *     /  \__/  \__/  \  *     /  \__/  \__ 
 /  \__/  \__/        \__/  \__/  \__/        \__/  \__/  \
 \__/  \__/  \__    __/  \__/  \__/  \__    __/  \__/  \__/
 /  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
 \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
 /  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
 \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
 /  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
 \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
 /  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
 \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
 /  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
 \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
 /  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  `  end
 \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__` 
 /  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
 \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
 /  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
 \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
 /  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
 \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
 /  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
 \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
 /  \__/        \__/  \__/        \__/  \__/        \__/  \
 \__/              \__/              \__/              \__/
 

"""	
	
		templates.append(template)

		# tune parser: set explicit wall length
		maze = mazeify()
		apply_options(maze,options)
		#maze.length = 1
		maze.use_microspace = True  
		#maze.dot_last_underscore = True   # sharpen corners _ -> _.
		parsers.append(maze)


#### test

		# Note: On concave shapes, the scanner will try to connect opposite
		# sides of the mouth. It just views the gap as another space it is
		# supposed to cross.  The easiest approach to giving the template the
		# correct "hints" to parse is (a) explicitly declare all external space
		# as 'visited' and (b) explicitily punch holes where you want the start
		# and end openings to be.
		template = r'''
    Example: irregular, multiple regions, text, holes, protected whitespace

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
                   |   |   |   |   |         ~ |   |   |   |   |   |   |    
                   +---+---+---+---+---+---+---+---+---+---+---+---+---+---+
     start             |   |   |   |   |   |   |   |   |   |   |   |   |   |
 +---+---+---+         +---+---+---+---+---+---+---+---+---+---+---+---+---+
 `   |   |   |             |   |   |   |   |   |   |   |   |   |   |   |   |
 +---+---+---+             +---+---+---+---+---+---+---+---+---+---+---+---+
 |   |   |   |    \ \ \        |   |   |   |   |   |   |   |   |   |   |   |
 +---+---+---+    / / /        +---+---+---+---+---+---+---+---+---+---+---+
 |   |   |   `                 `   |   |   |   |   |   |   |   |   |   |   |
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
                   +---+---+---+---+---+---+---+---+---+---+---+```+        
                       |   |   |   |   |   |   |   |   |   |   |        end 
                       +---+---+---+---+---+---+---+---+---+---+       \ \ \
                               |   |   |   |   |   |   |               / / /
                               +---+---+---+---+---+---+                    
'''

		templates.append(template)
		parsers.append(None) # default parser


#### end test


		# only parse one demo template
		if options.test > -1:
			templates = [ templates[options.test] ]	
			parsers = [ parsers[options.test] ]	

		print("Here's a quick demo using templates") 
		print("")


		for idx,template in enumerate(templates):
			parser = parsers[idx]

			print('-' * 79)

			if parser == None:
				print("use default parser options")
				parser = default_parser
			else: 
				print("use custom parser options")

			print("input template ("+str(idx)+"):")
			print("")
			print(template)
			parser.parseTemplate(template)

			if parser.use_microspace:
				print("microspace parsing:") 
				print(parser.toString(True).rstrip())

			out = parser.toString()
			parsers[idx] = None # garbage collect
			print("")
			print("rendered output:")
			print("")
			print(out)


	# parse a template file and display maze
	def parse_file(options):
		maze = mazeify()
		apply_options(maze,options)
		maze.parseTemplateFile(options.filename)
		out = maze.toString()
		print(out)


	# create basis maze
	def create_maze(options):
		maze = mazeify()
		template = maze.tessellate(options.width, options.height, options.maze)
		apply_options(maze,options)

		# parsing hints
		hints = { 
			'block': {
				'length': 1,
			},
			'diamond': {
				'use_microspace': True,
			},
			'hex': {
				'use_microspace': True,
			},
			'micro': {
				'use_microspace': True,
			},
			'triangle': {
				'use_microspace': True,
			},
		}
		if options.maze in hints:
			hint = hints[options.maze]
			for k in hint:
				if options.debug:
					print(k, hint[k])
				maze.__dict__[k] = hint[k]

		maze.parseTemplate(template)
		out = maze.toString()
		print(out)


	# what maze types are predefined?
	def list_maze_types():
		maze = mazeify()
		return str(sorted(maze.maze_types))


	# main ...
	sys.setrecursionlimit(100000)
	# parse cli options, parsing hints
	parser = optparse.OptionParser()

	parser.add_option('-f', '--file', action='store', dest='filename',
		help='ASCII template file', default='')
	parser.add_option('-d', '--debug', action='store_true', dest='debug',
		help='Enable debug', default=False)
	parser.add_option('-t', '--thickness', action='store', type="int", dest='thickness', 
		help='Wall thickness', default=1)
	parser.add_option('-l','--length', action='store', dest='length', type="int",
		help="Max wall segment length", default=-1)
	parser.add_option('-z', '--no-zigzag', action='store_true', dest='no_zigzag',
		help='Do not break diagonally joined walls', default=False)
	parser.add_option('-W', '--width', action='store', dest='width', type="int",
		help='Width', default=15)
	parser.add_option('-H', '--height', action='store', dest='height', type="int",
		help='Height', default=15)
	parser.add_option('-m', '--maze', action='store', dest='maze',
		help='Create a predefined maze. options: ' + list_maze_types(), default='')

	parser.add_option('-s', action='store_true', dest='use_microspace',
		help="Parse the microspace within a single character (for example _ is mostly visual whitespace).", default=False)

	parser.add_option('--no-wall-scan', action='store_true', dest='no_wall_scan',
		help="Don't scan any space that was previously taken by a wall.", default=False)
	parser.add_option('--test', action='store', dest='test', type='int',
		help='Only parse one test template (for regression testing).', default=-1)

	parser.add_option('--dot-last-underscore', action='store_true', dest='dot_last_underscore',
		help='Add a dot . decorator to last underscore in a segment.', default=False)

	parser.add_option('--no-close-implied-wall', action='store_true', dest='no_close_implied_wall',
		help='Do not preserve implied horizontal walls (such as _|_/_\\_  -> ______).  With this option, vertical walls are replaced with spaces only.', default=False)

	parser.add_option('--unittest', action='store_true', dest='unittest',
		help='Run a temporary test function maze.unittest()', default=False)

#	parser.add_option('-c', '--curviness', action='store', dest='curviness', type="int",
#		help='curviness [0,100]', default=100)

	options, args = parser.parse_args()

	if options.unittest:
		maze = mazeify()
		apply_options(maze,options)
		maze.unittest()	

	elif options.filename != '':
		parse_file(options)
	elif options.maze != '':
		create_maze(options)
	else:
		demo(options)

