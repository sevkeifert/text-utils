#!/usr/bin/env python

# Kevin Seifert - GPL v2 2015
#
# This script turns an ASCII tessellation into a maze.
#
# NOTES ON TEMPLATES:
#
# You should use a delimiter (or char change) at the edge of each wall segment.
# For example, in the template examples below, the '+' is the delimiter.
# Otherwise, the parser doesn't know where the wall segment ends or begins.
#
# Also, be careful on using _ (underscore) in your template.
# It looks like mostly whitespace, but it is a solid wall for the entire cell.
#
# Use the self.avoid char (~) to prevent scanner from traversing whitespace
# inside a region.  For example, to prevent the parser from puncturing a wall
# to room inside  a shape.
#
# COMMAND LINE USAGE:
#
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
#    (or import the mazify class and generate your tessellation on the fly)
#
# OPTIONS:
#
#    see -h for help
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
import optparse
import sys

class mazeify:

	def __init__(self):

		# logging
		self.debug = False # verbose debugging

		# data
		self.board = [[]] # char array for maze. note: 0,0 is top left

		self.deltas = [(0,-1),(0,1),(-1,0),(1,0)] # scan/fill directions: N S E W
		self.scan_diagonal = True # break diagonal wall patterns - experimental
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
		#self.curviness = 100 # percent of direction change. 0 - 100 (always)

		# cell flags
		self.space = ' ' # empty path (for display)
		self.unvisited = ' ' # any cell that is unvisited
		self.visited = '`' # flag cells where we have walked
		self.avoid = '~' # flag regions were parser should avoid

		# style tweaks
		self.dot_last_underscore = False  # transform "_ " -> "_."?
		self.close_implied_wall = False  # on remove vert, \_, |_, /_  to "__"?

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
					[ '+|+' ,  # use + to tighten up joins \| _| |
					  ' | ' ,
					  '+|+' ],

			'\\' :
					[ '\\  ' ,
					  ' \\ ' ,
					  '  \\' ],

			'_' :
					[ '   ' ,
					  ' _ ' , # center is id
					  '___' ],

			'-' :
					[ '   ' ,
					  '---' ,
					  '   ' ],

			#'+' :
			#      [ ' + ' , # use solid corner instead
			#       '+++' ,
			#       ' + ' ],

			# all others are solid blocks
		}


	# parse/import an ASCII tesellation to be used as basis of maze
	# creates maze by default (walks)
	def parseTemplate(self, template, create_maze=True):

		# apply transform for
		template = self.transform(template)
		if self.debug:
			print "transform:"
			print template

		self.board = []

		# normalize end of line
		template = template.replace("\r\n",self.eol) # dos
		if self.eol != "\r":
			template = template.replace("\r",self.eol) # mac
		if self.eol != "\n":
			template = template.replace("\n",self.eol) # nix

		lines = template.split(self.eol)

		max_len = 0
		for line in lines:
			tmp = len(line)
			if tmp > max_len:
				max_len = tmp

		for line in lines:
			cells = list(line)
			#cells = list(line) + ([' ']*(max_len-tmp))
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
			print e

		return '' # no char


	# macro char
	def getMacroCharTopLeftPos(self,x,y):
		# snap to first multiple of 3	
		(x0,y0) = ((x/3)*3,(y/3)*3)
		return (x0,y0)


	def getMacroCharIdPos(self,x,y):
		# snap to first multiple of 3	
		(x0,y0) = self.getMacroCharTopLeftPos(x,y)
		#print "macro cell" , (x,y),(x0,y0)
		return (x0+1,y0+1)


	# get value at board at x,y
	def getMacroCharValue(self,x,y):

		if not self.inBounds(x,y):
			return ''

		(x0,y0) = self.getMacroCharIdPos(x,y)
		return self.get(x0,y0)

		return c


#	# set value(s) at board at x,y, in macro/micro space
#	def setMacroChar(self,x,y,value):
#		
#		# set entire 9-grid, find upper left
#		x0 = x/3 * 3
#		y0 = y/3 * 3
#		chars = self.getMacroCharMap(value)
#		for i in range(3):
#			for j in range(3):
#				self.set(x0+j,y0+1,chars[i][j])

# alt: find change in boundary
#		# 9 cell -> 1 cell conversion
#		(x0,y0) = self.getMacroCharTopLeftPos(x,y)
#
#		chars = self.getMacroCharMap(c)
#		for i in range(3):
#			for j in range(3):
#				c1 = chars[i][j] # should be
#				c2 = self.get(x0+j,y0+1) # is
#				if ( c1 != ' ' and c1 != c2 ):
#					# char has been changed, return diff
#					return c2
#

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
					#print "old charmap value", charmap_old,  c2
					if c2 != ' ':
						(x4,y4) = (x2+i,y2+j)
						self.board[y4][x4] = value
						changed.append((x4,y4))

		return changed # all points updated


	# preserve implied horizontal boundaries.
	# transform  vert  \_, |_, /_   to   __
	def getReplaceChar(self,x,y,dx,dy,char):

		#return self.unvisited # to disable

		if not self.close_implied_wall:
			# transform  walls  \_, |_, /_  to " _"
			# ignore implied horizonal walls
			return self.unvisited

		c1 = ''
		c2 = ''
		if self.use_microspace:
			# TODO: test this more
			# look at macro char primary value only	
			char = self.getMacroCharValue(x,y)
			c1 = self.getMacroCharValue(x+3,y)
			c2 = self.getMacroCharValue(x-3,y)
		else:
			c1 = self.get(x-1,y)
			c2 = self.get(x+1,y)

		if char in self.walls_vert:
			# check horizontal neighbors directly
			if '_' in [c1,c2]:
				return '_'

		# default		
		return self.unvisited


	# find all points matching a given character
	# return array of points
	def find(self,find):
		points = []

		# scan all cells
		for y,row in enumerate(self.board):
			for x,c in enumerate(row):
				if c == find:
				 	points.append((x,y))	

		return points


#	# fill region with char, finding pattern and replacing.
#	# (like "fill region" in a paint program, finds boundaries)
#	def fill_old(self,x,y,find,replace,level=0,data=None):
#
#		if level == 0:
#			data = []
#			if len(find) != len(replace):
#				print 'Warn: lengths differ. "'+find+'" -> "'+replace+'"'
#			if find == replace:
#				print 'Warn: same find == replace: '+find
#				return data;
#		else:
#			if (x,y) in data:
#				#we've already checked this space
#				return data
#
#		if self.debug:
#			print 'fill pre', x, y, find, replace, level
#			print "macro id ", self.getMacroCharIdPos(x,y), self.getMacroCharValue(x,y)
#			print self.toString(True)
#
#		# what wall directions will be scanned in ASCII template?
#		# note: these are returned by reference
#		if self.scan_diagonal and find in self.walls_diagonal:
#			deltas = self.zdeltas # break diagonal wall patterns
#		else:
#			deltas = self.deltas # zdelta won't detect X whitespace boundaries
#
#		c = self.get(x,y)
#
#		if c == find: # hit
#			if self.use_microspace:
#				changed = self.setMacroChar(x,y,replace)
#				data += changed
#			else:	
#				self.set(x,y,replace)
#				data.append((x,y))
#
#			if self.length != -1 and len(data) >= self.length and c in self.walls:
#				# end. maxed out wall segment
#				return data	
#
#			else:
#				# recursively scan neighbors
#				for (dx,dy) in deltas:
#					x2 = x + dx
#					y2 = y + dy
#					if self.inBounds(x2,y2) and not ( (x2,y2) in data):
#						self.fill(x2,y2,find,replace,level+1,data)			
#
#		#elif c == '~': # in avoid space
#		#	data.append((x,y))
#		#	# ignore and scan up/down neighbors only
#		#	for (dx,dy) in deltas:
#		#		if dx==0:
#		#			x2 = x + dx
#		#			y2 = y + dy
#		#			self.fill(x2,y2,find,replace,level+1,data)			
#
#		if self.debug:
#			print 'fill post', x, y, find, replace, level
#			print self.toString(True)
#
#		return data


	# fill region with char, finding pattern and replacing.
	# (like "fill polygon" in a paint program, finds boundaries)
	# this is a replacement for self.fill_old(), where the old function was
	# converted from a simpler recusive function to standard function.
	# with recursion, it was sometimes hitting too many levels of recursion.
	# added suppoer for macro char replacements.
	def fill(self,x,y,find,replace,level=0,data=None):
		points = [(x,y)]
		return self.fillBlock(points, find, replace, level, data)


	# fill region with char, finding pattern and replacing.
	# like self.fill, but accepts mulitple points.
	def fillBlock(self, points, find, replace, level=0, data=None):

		if level == 0:
			data = []

		if len(find) != len(replace):
			print 'Warn: lengths differ. "'+find+'" -> "'+replace+'"'
		if find == replace:
			print 'Warn: same find == replace: '+find
			return data;

		next_scan = points # init loop
		walls = []

		while(len(next_scan) > 0):

			# process queued set of points
			points = next_scan # the current working set
			next_scan = []
			this_scan = []

			# what wall directions will be scanned in ASCII template?
			# note: these are returned by reference
			deltas = []

			if self.scan_diagonal and find in self.walls_diagonal:
				deltas = self.zdeltas # break diagonal wall patterns
			else:
				deltas = self.deltas # zdelta won't detect X whitespace bound
	
				
			for (x,y) in points:
	
				# process point
				if self.debug:
					print 'fill pre', x, y, find, replace, level
					print "macro id ", self.getMacroCharIdPos(x,y), self.getMacroCharValue(x,y)
					print self.toString(True)
		
				# scan in large straight paths when possible
				# (minimize recursion)
				for (dx,dy) in deltas:
					x2 = x
					y2 = y

					c = self.get(x2,y2)

					while c == find: # hit

						checked = [(x2,y2)]

						if not self.inBounds(x2,y2):
							#print "off the borad"
							break

						if (x2,y2) in data:
							#print "already checked"
							break

						# update
						if self.use_microspace:
							checked += self.setMacroChar(x2,y2,replace)
						else:	
							self.set(x2,y2,replace)

						# track changes
						for p in checked:
							if not ( p in data ):
								data.append(p)
								this_scan.append(p)

						# end for

						# count wall removed for implicit wall boundaries.
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

						x2 = x + dx
						y2 = y + dy
						c = self.get(x2,y2)

					# end while c == find
				# end for deltas
			# end for points

			if self.debug:
				print 'fill post', x, y, find, replace, level
				print self.toString(True)

			# save snapshot of all new neighboring points encountered
			for (x3,y3) in this_scan:
				for (dx,dy) in deltas:
					x4 = x3 + dx
					y4 = y3 + dy
					if self.inBounds(x4,y4) and not ((x4,y4) in next_scan) and not ((x4,y4) in data):
						next_scan.append((x4,y4))

		# end while next_scan

		return data		


	# fill "outside" region of shapes (anything containing with ~ avoid)
	def initOutside(self):
		data = []
		# flag "outside of shape"
		if self.pad > 0:
			self.fill(0,0,self.unvisited,self.visited)	

		points = self.find(self.avoid)
		if self.debug:
			print "find avoid", points
		for (x,y) in points:
			# block off any region containing ~
			self.fill(x,y,self.avoid,self.unvisited)	
			self.fill(x,y,self.unvisited,self.visited)	
	

	# scan the entire ASCII map, build the maze
 	def createMaze(self):

		self.initOutside()
		data = [] # track where we've checked

		# aim start in for middle.
		h = len(self.board)-1
		w = len(self.board[h/2])-1
		for y in xrange(h/2, h):
			for x in xrange(w/2,w):
				c = self.get(x,y)
				if c == self.unvisited:
					#print "start at " , (x,y)
				 	self.walk(x,y,0,data)	

		# scan all cells
		for y,row in enumerate(self.board):
			for x,c in enumerate(row):
				if c == self.unvisited:
				 	self.walk(x,y,0,data)	


	# walk around, knock down walls starting at x,y position
	def walk(self,x=-1,y=-1,level=0,data=[]):

		## optimize walk: only run one full scan on each space
		if (x,y) in data:
			return data
		else:
			data.append((x,y))

		c = self.get(x,y) # current char

		# scan pattern
		deltas = list(self.deltas) # make copy

		#if randint( 0, 100 ) < self.curviness:
		shuffle(deltas)

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
			#implied_whitespace = False

			while not finished:
				x2 += dx # walk in a direction
				y2 += dy
				scan = self.get(x2,y2) # look ahead char

				path.append((x2,y2))
				if scan ==  '':
					finished = True   # dead end
				#elif scan == self.avoid:
				#	if dx != 0:
				#		finished = True  # don't scan left/right in avoid row
				elif scan in self.corners:
					finished = True # knicked a corner. ignore.

				#elif foundwall and self.isImpliedWhitespace(x2,y2,dx,dy,wall,scan):
				#	finished = True
				#	implied_whitespace = True
				#	x2 -= dx
				#	y2 -= dy

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
				changed = []
				#shuffle(path)

				# knock down wall.  note: must use a delimiter/change
				# or parser won't know where the wall segment boundary ends
				walls_changed=[]
				for point in walls:
					(x3,y3) = point
					c = self.get(x3,y3)

					# FIXME update `replace` for macrospace
					replace = self.getReplaceChar(x3,y3,dx,dy,c)
					changed = self.fill(x3,y3,c,replace) # hulk smash!
					#if replace == self.visited:
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


	# basic ASCII tessellations
	def tessellate(self, w, h, type='square'):

		#all patterns
		patterns = {}
		
		# produce wxh standard square grid
		tile = ''
		tile += "+---" * w + '+' + self.eol
		tile += "|   " * w + '|'+ self.eol
		tile = tile * h
		tile += "+---" * w + '+' + self.eol
		patterns['square'] = tile

		# produce wxh micro square grid
		head = '_' + '_' * 2*w + self.eol
		foot = ''
		tile = '|_' * w +  '|'+ self.eol
		pattern = head + tile * h + foot
		patterns['micro'] = pattern

		# produce wxh block grid
		head = '#`' * (2*w+1) + self.eol
		foot = head
		tile = '#   ' * w +  '#'+ self.eol
		pattern = (head + tile) * h + foot
		patterns['block'] = pattern

		#print pattern

		# add more tile patterns here ...

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
	def transform(self, template):

		lines = template.split(self.eol)

		max_len = 0
		for line in lines: # find maximum line lenght
			tmp = len(line.rstrip())
			if tmp > max_len:
				max_len = tmp

		# add whitespace frame, clean up right end
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
	
		if not self.use_microspace:
			return template2

		# optional: convert 1-cell -> 9-cell
		lines = template2.split(self.eol)
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


		#tighted edges in 9-cell rendering (ignore some microspace)
		tighten = [
					('/  _', '/++_'),    # /_
					('_  \\', '_++\\')   # _\
				]

		for (find,replace) in tighten:
			template2 = template2.replace(find,replace)

		return template2


	# parse macrospace into microspace
	# 9-cell -> - cell for entire string
	def inverse_transform(self, transform):

		if self.use_microspace:
			t2 = ''
			lines = transform.split(self.eol2)
			for y,row in enumerate(lines):
				if(y%3) == 1: # center of row
					for x, c in enumerate(row):
						if (x%3) == 1: # center of cells
							t2 += c
					t2 += self.eol2
			transform = t2

		lines = transform.split(self.eol2)

		#slice off top, bottom
		lines = lines[self.pad : -self.pad]
		t2 = ''
		for line in lines:
			#slice off left, right
			t2 += line[self.pad : -self.pad] + self.eol2
		
		return t2


	# a temporary method for random testing
	def kevtest(self):
		self.use_microspace = True
		t ='\ / | _ +'
		self.parseTemplate(t,create_maze=False)
		for i in range(9*3):
			print "test",i	
			print self.toString(raw=True)
			self.setMacroChar(i,0,'|');
			print self.toString(raw=True)
			print "--"


# end class

	
if __name__ == '__main__':

	# process cli options, regression testing

	# pass along cli options to maze
	def apply_options(maze, options):
		maze.scan_diagonal = options.zigzag
		maze.debug = options.debug	
		maze.thickness = int(options.thickness)
		maze.length = int(options.length)
		maze.scan_wall_space = not options.no_wall_scan
		maze.dot_last_underscore = options.dot_last_underscore
		maze.use_microspace = options.use_microspace
		maze.close_implied_wall = options.close_implied_wall
		#maze.curviness = options.curviness


	#  simple template parsing demos / regression tests
	def demo(options):

		parsers = [] # custom parsing options
		templates = [] # test templates
	
		template = r'''
    Example: a basic grid

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
		parsers.append(None) # default parser

#### test

		template = r'''
    Example: irregular cells, holes
                                                              
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
		parsers.append(None) # default parser


#### test

		template = r'''
    Example: oblique

                  +---+---+---+---+---+---+---+---+---+---+---+ 
                 /   /   /   /   /   /   /   /   /   /   /   / 
                +---+---+---+---+---+---+---+---+---+---+---+ 
               /   /   /   /   /   /   /   /   /   /   /   / 
              +---+---+---+---+---+---+---+---+---+---+---+ 
             /   /   /   /   /   /   /   /   /   /   /   / 
            +---+---+---+---+---+---+---+---+---+---+---+ 
           /   /   /   /   /   /   /   /   /   /   /   / 
          +---+---+---+---+---+---+---+---+---+---+---+ 
         /   /   /   /   /   /   /   /   /   /   /   / 
        +---+---+---+---+---+---+---+---+---+---+---+ 
       /   /   /   /   /   /   /   /   /   /   /   / 
      +---+---+---+---+---+---+---+---+---+---+---+ 
     /   /   /   /   /   /   /   /   /   /   /   / 
    +---+---+---+---+---+---+---+---+---+---+---+ 
   /   /   /   /   /   /   /   /   /   /   /   / 
  +---+---+---+---+---+---+---+---+---+---+---+ 
 /   /   /   /   /   /   /   /   /   /   /   / 
+---+---+---+---+---+---+---+---+---+---+---+ 

		'''

		templates.append(template)
		parsers.append(None) # default parser

#### test

		template = r"""
    Example: mixed tessellations are also possible

    Salvidor Dali Melting Maze:
	
              ``````````````     ```````````````````````````````
              `+---+---+---+-----+---+------+---+-----+---+```````
             `/   /   /   /     /   /      /   /     /   /````````
            `+---+---+---+-----+---+------+---+-----+---+------+`
           `/   /   /   /     /   /      /   /     /   /      /```
          `+---+---+---+-----+---+------+---+-----+---+------+````
         `/   /   /   /     /   /      /   /     /   /      /`````
        `+---+---+---+-----+---+------+---+-----+---+------+---+`
       `/   /   /   /     /   /      /   /     /   /      /   /`
      `+---+---+---+-----+---+------+---+-----+---+------+---+`
     `/   /   /   /     /   /      /   /     /   /      /   /`
    `+---+---+---+-----+---+------+---+-----+---+------+---+`
   `/   /   /   /     /   /      /   /     /   /      /   /`
  `+---+---+---+-----+---+------+---+-----+---+------+---+`
 `/   /   /   /     /   /      /   /     /   /      /   /`
`+---+---+---+-----+---+------+---+-----+---+------+---+`
````/   /   /     /   /      /   /     /   /      /   /`
```+---+---+-----+----+-----+---+-----+---+------+---+`
    ``/     \    /     \    /    \    /    \    /     \`
    `+       +--+       +--+     +---+      +---+      +`
    ``\     /    \     /    \    /    \     /    \    /`
    ```+---+      +---+      +--+      +---+      +--+`
    ``/     \    /     \    /    \    /     \    /    \`
    `+       +--+       +--+      +---+      +--+      +`
    ``\     /    \     /    \    /     \     /    \    /`
    ```+---+      +---+      +--+       +---+      +--+`
    ``/     \    /     \    /    \     /     \    /    \`
    `+       +--+       +--+      +---+      +--+      +`
    ``\     /    \     /    \    /     \     /    \    /`
    ```+---+      +---+      +--+       +---+      +--+`
    ``/     \    /     \    /    \     /     \    /``````
    `+       +--+       +--+      +---+       +--+```
    ``\     /````\     /    \    /     \     /```````
    ```+---+ ````+---+       +---+      +---+```
    ``````````````````\     /     \    /``````
      `````````````````+---+       +--+``
       `````````````````````\     |```
"""	
		templates.append(template)
		parsers.append(None) # default parser

#### test

		# irregular, with diagonal walls, text, protected whitespace
		# be careful with trailing whitespace
		# can use with the -z diagonal wall flag
		template = r"""
```````Help`Mr.`Food`Travel`Through`the`Intestines`;-)
````````````````````````````````````````````````````````````````
```start````````````````````````````````````````````````````````
``````````\`````````````````````````````````````````````````````
```\```````\```````____````````____`````````````````````````````
````\       \____/      \____/      \____```````````````````````
`````\      /    \      /    \      /    \``````````````````````
``````\____/      \____/      \____/      \____`````````````````
``````/    \      /    \      /    \      /    \````````````````
`````/      \____/      \____/      \____/      \```````````````
`````\      /    \      /    \      /    \      /```````````````
``````\____/      \____/      \____/      \____/````````````````
``````/    \      /    \      /    \      /    \````````````````
`````/      \____/      \____/      \____/      \____```````````
`````\      /    \      /    \      /    \      /    \``````````
``````\____/      \____/      \____/      \____/      \____`````
``````/    \      /    \      /    \      /    \      /    \````
`````/      \____/      \____/      \____/      \____/      \```
`````\      /    \      /    \      /    \      /    \      /```
``````\____/      \____/      \____/      \____/      \____/````
``````/    \      /    \      /    \      /    \      /    \````
`````/      \____/      \____/      \____/      \____/      \```
`````\      /    \      /    \      /    \      /    \      /```
``````\____/      \____/      \____/      \____/      \____/````
``````/    \      /    \      /    \      /    \      /    \````
`````/      \____/      \____/      \____/      \____/      \```
`````\      /    \      /    \      /    \      /    \      /```
``````\____/      \____/      \____/      \____/      \____/````
```````````\`     /    \      /    \      /    \      /    \````
````````````\____/      \____/      \____/      \____/      \```
`````````````````\`     /````\      /````\      /````\       \``
``````````````````\____/``````\____/``````\____/``````\  end  \`
```````````````````````````````````````````````````````\       \
````````````````````````````````````````````````````````````````
"""	
		templates.append(template)

		# tune parser: explode diagonal walls
		maze = mazeify()
		apply_options(maze,options)
		maze.scan_diagonal = True
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

```````````````````````````````````+---+---+---+---+````````````````````````
```````````````````````````````````|   |   |   |   |````````````````````````
```````````````````````````+---+---+---+---+---+---+---+---+````````````````
```````````````````````````|   |   |   |   |   |   |   |   |````````````````
```````````````````````+---+---+---+---+---+---+---+---+---+---+````````````
```````````````````````|   |   |   |   |   |   |   |   |   |   |````````````
```````````````````+---+---+---+---+---+---+---+---+---+---+---+---+````````
```````````````````|   |   |   |   |```````````|   |   |   |   |   |````````
```````````````+---+---+---+---+---+```````````+---+---+---+---+---+---+````
```````````````|   |   |   |   |   |```````````|   |   |   |   |   |   |````
```````````````+---+---+---+---+---+```````````+---+---+---+---+---+---+````
```````````````````|   |   |   |   |```````````|   |   |   |   |   |   |````
```````````````````+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
`````start`````````````|   |   |   |   |   |   |   |   |   |   |   |   |   |
`+---+---+---+`````````+---+---+---+---+---+---+---+---+---+---+---+---+---+
`    |   |   |`````````````|   |   |   |   |   |   |   |   |   |   |   |   |
 +---+---+---+`````````````+---+---+---+---+---+---+---+---+---+---+---+---+
`|   |   |   |````\`\`\````````|   |   |   |   |   |   |   |   |   |   |   |
`+---+---+---+````/`/`/````````+---+---+---+---+---+---+---+---+---+---+---+
`|   |   |    `````````````````    |   |   |   |   |   |   |   |   |   |   |
`+---+---+---+`````````````+---+---+---+---+---+---+---+---+---+---+---+---+
```````````````````````````|   |   |   |   |   |   |   |   |   |   |   |   |
```````````````````````+---+---+---+---+---+---+---+---+---+---+---+---+---+
```````````````````````|   |   |   |   |   |   |   |   |   |   |   |   |   |
```````````````````+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
```````````````````|   |   |   |   |   |   |   |   |   |   |   |   |   |````
```````````````+---+---+---+---+---+---+---+---+---+---+---+---+---+---+````
```````````````|   |   |   |   |   |   |   |   |   |   |   |   |   |   |````
```````````````+---+---+---+---+---+---+---+---+---+---+---+---+---+---+````
```````````````````|   |   |   |   |   |   |   |   |   |   |   |   |````````
```````````````````+---+---+---+---+---+---+---+---+---+---+---+   +````````
```````````````````````|   |   |   |   |   |   |   |   |   |   |````````end`
```````````````````````+---+---+---+---+---+---+---+---+---+---+```````\`\`\
```````````````````````````````|   |   |   |   |   |   |```````````````/`/`/
```````````````````````````````+---+---+---+---+---+---+````````````````````
'''

		templates.append(template)
		parsers.append(None) # default parser


#### test

		template = r"""

special handling for _ translate implied whitespace
  __    __    __    __    __    __  
 /  \__/  \__/  \__/  \__/  \__/  \ 
 \__/  \__/  \__/  \__/  \__/  \__/ 
 /  \__/  \__/  \__/  \__/  \__/  \ 
 \__/  \__/  \__/  \__/  \__/  \__/ 
 /  \__/  \__/  \__/  \__/  \__/  \ 
 \__/  \__/  \__/  \__/  \__/  \__/ 
 /  \__/  \__/  \__/  \__/  \__/  \ 
 \__/  \__/  \__/  \__/  \__/  \__/ 
 /  \__/  \__/  \__/  \__/  \__/  \ 
 \__/  \__/  \__/  \__/  \__/  \__/ 
 /  \__/  \__/  \__/  \__/  \__/  \ 
 \__/  \__/  \__/  \__/  \__/  \__/ 
 /  \__/  \__/  \__/  \__/  \__/  \ 
 \__/  \__/  \__/  \__/  \__/  \__/ 
                                    
"""	
	
		templates.append(template)
		# tune parser: set explicit wall length
		maze = mazeify()
		apply_options(maze,options)
		maze.use_microspace = True  
		#maze.dot_last_underscore = True   # sharpen corners _ -> _.
		parsers.append(maze)

#### test

		template = r"""

triangles - implied whitespace
    ____________________________
    \  /\  /\  /\  /\  /\  /\  / 
     \/__\/__\/__\/__\/__\/__\/  
     /\  /\  /\  /\  /\  /\  /\
    /__\/__\/__\/__\/__\/__\/__\ 
    \  /\  /\  /\  /\  /\  /\  / 
     \/__\/__\/__\/__\/__\/__\/  
     /\  /\  /\  /\  /\  /\  /\  
    /__\/__\/__\/__\/__\/__\/__\ 
    \  /\  /\  /\  /\  /\  /\  / 
     \/__\/__\/__\/__\/__\/__\/  
     /\  /\  /\  /\  /\  /\  /\
    /__\/__\/__\/__\/__\/__\/__\ 

     /\/\/\/\/\/\/\/\/\/\/\
    /\/\/\/\/\/\/\/\/\/\/\/
    \/\/\/\/\/\/\/\/\/\/\/\
    /\/\/\/\/\/\/\/\/\/\/\/
    \/\/\/\/\/\/\/\/\/\/\/\
    /\/\/\/\/\/\/\/\/\/\/\/
    \/\/\/\/\/\/\/\/\/\/\/\
    /\/\/\/\/\/\/\/\/\/\/\/
    \/\/\/\/\/\/\/\/\/\/\/\
    /\/\/\/\/\/\/\/\/\/\/\/
    \/\/\/\/\/\/\/\/\/\/\/\
    /\/\/\/\/\/\/\/\/\/\/\/
    \/\/\/\/\/\/\/\/\/\/\/


"""	
	
		maze = mazeify()
		apply_options(maze,options)
		maze.length = 1
		maze.scan_diagonal = True
		maze.use_microspace = True  
		maze.close_implied_wall = True

		#maze.dot_last_underscore = True   # sharpen corners _ -> _.

		parsers.append(maze)
		templates.append(template)
	

#### test

		# requires special handling for no-separator between wall segments
		template = r"""
micro template example

note: contains no actual 
      whitespace
 ___________________________ 
 |_|_|_|_|_|_|_|_|_|_|_|_|_| 
 |_|_|_|_|_|_|_|_|_|_|_|_|_| 
 |_|_|_|_|_|_|_|_|_|_|_|_|_| 
 |_|_|_|_|_|_|_|_|_|_|_|_|_| 
 |_|_|_|_|_|_|_|_|_|_|_|_|_| 
 |_|_|_|_|_|_|_|_|_|_|_|_|_| 
 |_|_|_|_|_|_|_|_|_|_|_|_|_| 
 |_|_|_|_|_|_|_|_|_|_|_|_|_| 
 |_|_|_|_|_|_|_|_|_|_|_|_|_| 
 |_|_|_|_|_|_|_|_|_|_|_|_|_| 
 |_|_|_|_|_|_|_|_|_|_|_|_|_| 
                             
"""	

# quicker render
		# requires special handling for no-separator between wall segments
		template_alt = r"""
_________________ 
|_|_|_|_|_|_|_|_| 
|_|_|_|_|_|_|_|_| 
|_|_|_|_|_|_|_|_| 
|_|_|_|_|_|_|_|_| 
|_|_|_|_|_|_|_|_| 

_________________ 
|_|_|_|_|_|_|_|_| 
|_|_|_|_|_|_|_|_| 
|_|_|_|   |_|_|_| 
|_|_|_| ~ |_|_|_| 
|_|_|_|___|_|_|_| 

"""	
	
	
		templates.append(template)

		# tune parser: set explicit wall length
		maze = mazeify()
		apply_options(maze,options)
		maze.length = 1
		maze.use_microspace = True  
		maze.close_implied_wall = True  
		#maze.dot_last_underscore = True   # sharpen corners _ -> _.
		parsers.append(maze)

#### end test


		# only parse one demo template
		if options.test > -1:
			templates = [ templates[options.test] ]	
			parsers = [ parsers[options.test] ]	

		print "Here's a quick demo using templates" 
		print ""

		default_parser = mazeify()
		apply_options(default_parser,options)

		for idx,template in enumerate(templates):
			parser = parsers[idx]

			print '-' * 79

			if parser == None:
				print "use default parser options"
				parser = default_parser
			else: 
				print "use custom parser options"

			print "input template ("+str(idx)+"):"
			print ""
			print template
			parser.parseTemplate(template)

			if parser.use_microspace:
				print "microspace parsing:" 
				print parser.toString(True).rstrip()

			out = parser.toString()
			print ""
			print "rendered output:"
			print ""
			print out


	# parse a template file and display maze
	def parse_file(options):
		maze = mazeify()
		apply_options(maze,options)
		maze.parseTemplateFile(options.filename)
		out = maze.toString()
		print out


	# create basis maze
	def create_maze(options):
		maze = mazeify()
		template = maze.tessellate(options.width, options.height, options.maze)
		apply_options(maze,options)

		# parsing hints
		hints = { 
			'micro': {
				'length': 1,
				'close_implied_wall': True,
				'use_microspace': True,
			},
			'block': {
				'length': 1,
			},
		}
		if options.maze in hints:
			hint = hints[options.maze]
			for k in hint:
				if options.debug:
					print k, hint[k]
				maze.__dict__[k] = hint[k]

		maze.parseTemplate(template)
		out = maze.toString()
		print out


	# main ...
	sys.setrecursionlimit(100000)
 	# parse cli options, parsing hints
	parser = optparse.OptionParser()

	parser.add_option('-f', '--file', action='store', dest='filename',
		help='ASCII template file', default='')
	parser.add_option('-d', '--debug', action='store_true', dest='debug',
		help='enable debug', default=False)
	parser.add_option('-t', '--thickness', action='store', type="int",
		dest='thickness', help='wall thickness', default=1)
	parser.add_option('-l','--length', action='store', dest='length', type="int",
		help="max wall segment length", default=-1)
	parser.add_option('-z', '--zigzag', action='store_true', dest='zigzag',
		help='allow diagonal scanning', default=False)
	parser.add_option('-W', '--width', action='store', dest='width', type="int",
		help='width', default=19)
	parser.add_option('-H', '--height', action='store', dest='height', type="int",
		help='height', default=20)
	parser.add_option('-m', '--maze', action='store', dest='maze',
		help='create a basic maze. options: square', default='')

	parser.add_option('-s', action='store_true', dest='use_microspace',
		help="parse the microspace within a single character (for example _)", default=False)

	parser.add_option('--no-wall-scan', action='store_true', dest='no_wall_scan',
		help="don't scan any space that was previously taken by a wall", default=False)
	parser.add_option('--test', action='store', dest='test', type='int',
		help='only parse one test template (for regression testing)', default=-1)

	parser.add_option('--dot-last-underscore', action='store_true', dest='dot_last_underscore',
		help='add a dot . decorator to last underscore in a segment.', default=False)

	parser.add_option('--close-implied-wall', action='store_true', dest='close_implied_wall',
		help='preserve implied horizontal walls _|_/_\\_  -> ______', default=False)

#	parser.add_option('-c', '--curviness', action='store', dest='curviness', type="int",
#		help='curviness [0,100]', default=100)


	parser.add_option('--kevtest', action='store_true', dest='kevtest',
		help='run a temporary test function', default=False)

	options, args = parser.parse_args()

	if options.kevtest:
	 	maze = mazeify()
		apply_options(maze,options)
		maze.kevtest()	

	elif options.filename != '':
		parse_file(options)
	elif options.maze != '':
		create_maze(options)
	else:
		demo(options)

