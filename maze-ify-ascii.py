#!/usr/bin/env python

# TODO LIST:
#	[ ] improve whitespace frame around maze for microspace parsing.  currently no control on this
#	[x] improve implied horizonal wall break _/ |_ \_ -> __  
#	[ ] add ~ meta char to flag and  prefill "outside" of shapes on initial parse
#	[ ] add 'curviness' option
#	[ ] on wall fill, count macro chars replaced. test length check for microparsing
#	[ ] optimize for smaller use of recursion

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
# Use the self.visited char (`) to prevent scanner from traversing whitespace.
# For example, to prevent the parser from puncturing a wall to outside a shape.
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

from random import shuffle
import optparse
import sys

class mazeify:


	def __init__(self):

		self.board = [[]] # char array for maze. note: 0,0 is top left 

		self.deltas = [(0,-1),(0,1),(-1,0),(1,0)] # scan/fill directions: N S E W
		self.scan_diagonal = True # break diagonal wall patterns - experimental
		self.zdeltas = [(1,-1),(-1,-1),(1,1),(-1,1)] + self.deltas # NW NE SW SE 

		self.eol = '\n' # expected end-of-line in template
		self.eol2 = '\n' # rendered end-of-line in ouput

		# wall
		self.scan_wall_space = True # scan from space that was previously wall
		self.walls = ['/','\\','_','|','-','+','#'] # allowed wall boundaries
		self.walls_diagonal = ['/','\\'] # which walls are diagonal
		self.walls_vert = self.walls_diagonal + ['|'] # which walls are vertical
		self.corners = ['+'] # protect corner, prevent path from passing through
		self.thickness = 1 # max thickness of wall 
		self.length = -1 # max length of wall segment

		# style tweaks
		self.dot_last_underscore = False  # transform "_ " -> "_."?

		# cell flags
		self.space = ' ' # empty path (for display)
		self.unvisited = ' ' # any cell that is unvisited
		self.visited = '`' # flag cells where we have walked

# TODO: allow flag of "outside" of shapes
		#self.nether = '~' # flag outside of shape (for initial fill) 

		self.debug = False # verbose debugging


		# parse space inside cell for micro-templates.
		# all chars cells will be converted to 9 cells, where
		# center char is id.
		self.use_microspace = False # parse space within char cell?
		self.microspace_char_map = { 

			'/' :[ '  /' ,
				   ' / ' ,
				   '/  ' ],

			'|' :[ '~|~' ,  # use ~ to tighten up joins _\ _| _/ 
				   ' | ' ,
				   '~|~' ],


			'\\' :[ '\\  ' ,
					' \\ ' ,
					'  \\' ],

			'_' :[ '   ' ,
				   ' _ ' , # center is id
				   '___' ],

			'-' :[ '   ' ,
				   '---' ,
				   '   ' ],

			#'+' :[ ' + ' , # use solid corner instead
			#       '+++' ,
			#       ' + ' ],

			# all others are solid blocks
		}


	
	# parse/import an ASCII tesellation to be used as basis of maze
	# construct maze
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


		# TODO 
		## add a whitespace frame around template, for 'outside' detection
		## clean up right end
		##for i in range(self.pad):
		##	self.board.append([' ']*(max_len + 2))
		#for line in lines:
		#	tmp = len(line) 
		#	cells = list(line) + ([' ']*(max_len-tmp))
		#	#cells = ([' ']*self.pad) + list(line) + ([' ']*(self.pad + max_len - tmp))
		#	#cells = [' ']*self.pad + list(line) + [' '] 
		#	#cells = list( ' ' + line + ' '  ) 
		#	self.board.append(cells)
		##for i in range(self.pad):
		##	self.board.append([' ']*(max_len + 2))
	
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

		#if not self.use_microspace:
		#	return self.get(x,y) 

		(x0,y0) = self.getMacroCharIdPos(x,y)
		return self.get(x0,y0) 

#
#		# 9 cell -> 1 cell conversion
#		(x0,y0) = self.getMacroCharTopLeftPos(x,y)
#
#		chars = self.getMacroCharMap(c)
##		print "chars", chars
#		for i in range(3):
#			for j in range(3):
#				c1 = chars[i][j] # should be
#
##				print "should be" , c1
#
#				c2 = self.get(x0+j,y0+1) # is
##				print "is " , c2
###				print c2,
#
#				if ( c1 != ' ' and c1 != c2 ):
#					#print "compare", c1, c2
#					# char has been changed, return diff
#					return c2  
#
##			print "\n"					
#
		return c

	# set value at board at x,y
	def set(self, x, y, value):
		if not self.inBounds(x,y,raise_exception=True):
			return False

		self.board[y][x] = value

		return True

	# update a 9-cell macro character
	# return changed points
	def setMacroChar(self, x, y, value):

		#print "setMacroChar", x, y, value

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
			#print "direct patch"
			self.board[y][x] = value
			changed.append((x,y))
			return changed

		# does new value differ from old macro value id? 
		# find start of macro char
		(x2,y2) = self.getMacroCharTopLeftPos(x,y) 
		(x3,y3) = (x2+1, y2+1) # id pos at center
		old_id = self.get(x3,y3) 
		if old_id == value:
			#print "no change"
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


	# preserve implied horizontal boundaries.
	# transform  vert  \_, |_, /_   to   __
	def getReplaceChar(self,x,y,dx,dy,char):

		c1 = '' 
		c2 = ''
		if self.use_microspace:
			# TODO: test this more
			#return self.unvisited
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


	# fill region with char, finding pattern and replacing.
	# (like "fill region" in a paint program, finds boundaries)
	def fill(self,x,y,find,replace,level=0,data=None):

		if level == 0:
			data = []
			if len(find) != len(replace):
				print 'Warn: lengths differ. "'+find+'" -> "'+replace+'"'
			if find == replace:
				print 'Warn: same find == replace: '+find
				return data; 
		else:
			if (x,y) in data:
				#we've already checked this space
				return data

		if self.debug:
			print 'fill pre', x, y, find, replace, level
			print "macro id ", self.getMacroCharIdPos(x,y), self.getMacroCharValue(x,y)
			print self.toString(True) 

		# what wall directions will be scanned in ASCII template?
		# note: these are returned by reference
		if self.scan_diagonal and find in self.walls_diagonal:
			deltas = self.zdeltas # break diagonal wall patterns
		else:
			deltas = self.deltas # zdelta won't detect X whitespace boundaries


		c = self.get(x,y)

		if c == find: # hit
			if self.use_microspace:
				changed = self.setMacroChar(x,y,replace)
				data += changed
			else:	
				self.set(x,y,replace)
				data.append((x,y))

			if self.length != -1 and len(data) >= self.length and c in self.walls:
				# end. maxed out wall segment
				return data	

			else:
				# recursively scan neighbors
				for (dx,dy) in deltas:
					x2 = x + dx 
					y2 = y + dy 
					if self.inBounds(x2,y2) and not ( (x2,y2) in data):
						self.fill(x2,y2,find,replace,level+1,data)			

		#elif c == '~': # in nether space 
		#	data.append((x,y))
		#	# ignore and scan up/down neighbors only
		#	for (dx,dy) in deltas:
		#		if dx==0:
		#			x2 = x + dx 
		#			y2 = y + dy 
		#			self.fill(x2,y2,find,replace,level+1,data)			


		if self.debug:
			print 'fill post', x, y, find, replace, level
			print self.toString(True) 

		return data


	# scan the entire ASCII map, build the maze
 	def createMaze(self):

		data = [] # track where we've checked
		
		h = len(self.board)-1
		w = len(self.board[h/2])-1

		# aim for middle.
		for y in xrange(h/2, h):
			for x in xrange(w/2,w):
				c = self.get(x,y)
				if c == self.unvisited: 
					#print "start at " , (x,y)
				 	self.walk(x,y,0,data)	

		# scan all cells 
		for y in xrange(len(self.board)-1):
			for x in xrange(len(self.board[y])-1):
				c = self.get(x,y)
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
				#elif scan == self.nether: 
				#	if dx != 0:
				#		finished = True  # don't scan left/right in nether row
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
				shuffle(path)

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
			
				## flag values as changed	
				#if self.use_microspace:
				#	for (x4,y4) in walls_changed:
				#		self.setMacroChar(x4,y4,self.unvisited)

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


	# basic ASCII templates for standard mazes below...
		
	def tessellate(self, w, h, type='square'):

		#all patterns
		patterns = {}
		
		# produce wxh square grid
		tile  = "+---" * w + '+' + self.eol
		tile += "|   " * w + '|'+ self.eol
		tile = tile * h 
		tile += "+---" * w + '+' + self.eol
		patterns['square'] = tile

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


	# get macrospace char value at x,y 
	def getMicroChar(self, x, y):

		c = self.get(x,y)

 
	# parse char microspace into macrospace
	def transform(self, template):
		if not self.use_microspace:
			return template

		template2 = ''

		lines = template.split(self.eol)
		for line in lines:
			# sub lines
			temp = ['','','']	
			for c in line:
				chars = self.getMacroCharMap(c)
				for i in range(3):
					temp[i] += chars[i]	

			for i in range(3):
				template2 += temp[i] + self.eol

		return template2


	# parse macrospace into microspace
	# 9 cell -> 1 cell for entire string
	def inverse_transform(self, transform):
		#print "original:"
		#print  transform
		#print ""

		if not self.use_microspace:
			return transform # no change

		t2 = ''

		lines = transform.split(self.eol2)
		for y,row in enumerate(lines):
			if(y%3) == 1: # center of row
				for x, c in enumerate(row):
					if (x%3) == 1: # center of cells

						t2 += c 
						pass
				t2 += self.eol2
		return t2





# generalize:
#
#	# The character _ needs special handling. 
#	# for example:  _   
#	#              |_|   (contains visual space, but no space character)
#	# 
#	# It will be treated as wall/whitespace hybrid.
#	# so, transform the template to a topologically equivalent map of chars
#	# with clean wall/whitespace boundaries.  For example, an underscore _ is
#	# an unusual cell character in that it has visual properties of whitespace,
#	# but it takes up a full char cell (it is a wall).  To simplify parsing,
#	# transform _ into two cells to represent for both the whitespace and wall
#	# components.  The special character ~ represents non-space in between
#	# cells.
#	#
#	# example:
#	#                     a b 
#	#            a_b  ->  ~_~
#	# 
#	#
#	#                      |`| 
#	#            _        ~~_~~
#	#           |_|  ->    | |
#	#                     ~~_~~
#	#
#	# first white space is flagged as already claimed (to protect exterior wall)
#	#
#	# diagonal wall boundaries can be stretched if present, for example:
#	#                     
#	#                     
#	#           \_/  ->    \ /     
#	#                     ~\_/~     
#	#
#
#	def transform2(self, template):
#		#return template
#
#		s = ''
#		rowidx = 0
#		cellidx = 0
#		row1 = [''] 
#		row2 = ['']
#
#		for c in template:
#
#			#print c
#			if c == self.eol:
#				rowidx += 1
#				cellidx = 0
#				row1.append('')
#				row2.append('')
#
#			# split _ into clean whitespace and wall components
#			elif c == '_':
#
#				# special case: first whitespace in col is outside shape
#				if rowidx == 0: 
#					# treat first white space as claimed whitespace
#					row1[rowidx] += self.nether 
#				elif cellidx > len(row1[rowidx-1])-1:
#					# previous row doesn't contain data at this point
#					# treat as claimed whitespace
#					row1[rowidx] += self.nether 
#				elif  row1[rowidx-1][cellidx] == self.visited:
#					#row1[rowidx] += self.visited 
#					row1[rowidx] += self.nether # temporary flag, prevent loop
#				else:
#					# treat as new whitespace
#					row1[rowidx] += ' '
#
#				row2[rowidx] += '_'
#				cellidx += 1
#
#			# extend diagonal walls so they are still touching _
#			#elif c in self.walls:
#			elif c in self.walls_diagonal:
#				row1[rowidx] += c 
#				row2[rowidx] += c
#				cellidx += 1
#
#			else:
#				row1[rowidx] += c 
#				row2[rowidx] += self.nether # nether region
#				cellidx += 1
#
#		# combine rows
#		i = 0
#		while i <= rowidx: 
#			s += row1[i].replace(self.nether, self.visited) # flag space 
#			s += self.eol 
#			s += row2[i] # retain nether, strip out in inverse_transform()
#			s += self.eol 
#			i += 1
#
#		return s
#
#
#	# inverse transform, where:
#	#   t = transform(template)
#	#   template = inverse_transform(t)
#	#
#	# example
#	#          a b            
#	#          ~_~  ->  a_b 
#	# example
#	#          1 3            
#	#          ~2~  ->  123 
#	#
#	def inverse_transform2(self, transform):
#
#		#return transform
#
#		s = ''
#
#		# collapse odd/even rows
#		rows = transform.split(self.eol)
#		for i in xrange(0,len(rows)-1,2):
#			row1 = list(rows[i])
#			row2 = rows[i+1]
#			for j,c in enumerate(row2):
#				try:
#					if c == '_':
#						row1[j] = c	 
#				except Exception as e:
#					print "Warn: could not apply inverse transform"
#					print e
#
#			s += ''.join(row1)
#			s += self.eol 
#
#		return s
#

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


		# requires special handling for no-separator between wall segments
		template = r"""
#micro template 
#(note: there's no whitespace in this template)
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

# quick render
		# requires special handling for no-separator between wall segments
		template = r"""
 _________________ 
 |_|_|_|_|_|_|_|_| 
 |_|_|_|_|_|_|_|_| 
 |_|_|_|_|_|_|_|_| 
 |_|_|_|_|_|_|_|_| 
 |_|_|_|_|_|_|_|_| 

"""	
	
	
		templates.append(template)

		# tune parser: set explicit wall length
		maze = mazeify()
		apply_options(maze,options)
		#maze.length = 1
		maze.use_microspace = True  
		#maze.dot_last_underscore = True   # sharpen corners _ -> _.
		parsers.append(maze)


		#half implemented: triangles - implied whitespace
		template = r"""
                          
   _____________________
  /\  /\  /\  /\  /\  /\  
 /__\/__\/__\/__\/__\/__\ 
 \  /\  /\  /\  /\  /\  / 
  \/__\/__\/__\/__\/__\/  
  /\  /\  /\  /\  /\  /\  
 /__\/__\/__\/__\/__\/__\ 
 \  /\  /\  /\  /\  /\  / 
  \/__\/__\/__\/__\/__\/  
  /\  /\  /\  /\  /\  /\  
 /__\/__\/__\/__\/__\/__\ 
 \  /\  /\  /\  /\  /\  / 
  \/__\/__\/__\/__\/__\/  
                          
"""	
	
		maze = mazeify()
		apply_options(maze,options)
		maze.length = 1
		maze.use_microspace = True  
		#maze.dot_last_underscore = True   # sharpen corners _ -> _.

		# TODO 
		#parsers.append(maze)
		#templates.append(template)
	

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

			if maze.use_microspace:
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

