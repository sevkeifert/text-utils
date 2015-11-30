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
# Use the self.visited char (`) to prevent scanner from traversing whitespace.
# For example, to prevent the parser from puncturing a wall to outside a shape.
# 
# COMMAND LINE USAGE:
#
#
#    # create a maze from an ASCII template file
#    maze-ify-ascii.py -f YOUR_TEMPLATE
#
#    # generate a simple square maze (no template)
#    maze-ify-ascii.py -m -W 10 -H 10
#    (or import the mazify class and generate your tessellation on the fly)
# 
# OPTIONS:
#
#    -f    ASCII template file
#    -d    enable debug
#    -t    max wall thickness (hint for scanner)
#    -z    break diagonal wall patterns - experimental
#    -m	   Draw a simple square maze
#          -W    width 
#          -H    height
#
#    --start-x        start scan at x
#    --start-y        start scan at y
#    --no-wall-scan   don't scan any space that was previously taken by a wall 
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

class mazeify:

	def __init__(self):

		self.board = [[]] # char array for maze
		self.deltas = [(1,0),(0,1),(-1,0),(0,-1)] # scan/fill directions

		# wall
		self.scan_wall_space = True # scan from space that was previously wall
		self.walls = ['/','\\','_','|','-','+','#'] # allowed wall boundaries
		self.corners = ['+'] # protect corner, prevent path from passing through
		self.thickness = 1 # max thickness of wall 

		# break diagonal wall patterns - experimental! not tested very much :)
		self.scan_diagonal = False 
		self.zdeltas = [(1,1),(-1,1),(1,-1),(-1,-1)] + self.deltas

		# cell flags
		self.space = ' ' # empty path (for display)
		self.unvisited = ' ' # any cell that is unvisited
		self.visited = '`' # flag cells where we have walked

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

		# what wall directions will be scanned in ASCII template?
		# note: these are returned by reference
		if self.scan_diagonal and find in self.walls:
			deltas = self.zdeltas # break diagonal wall patterns
		else:
			deltas = self.deltas # zdelta won't detect X whitespace boundaries

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
		h = len(self.board)-1
		w = len(self.board[h/2])-1
		for y in xrange(h/2, h):
			for x in xrange(w/2,w):
				c = self.get(x,y)
				if c == self.unvisited: 
					#print "start at " , (x,y)
					return (x,y)

		# bugger that... just pick the first.
		for y in xrange(len(self.board)-1):
			for x in xrange(len(self.board[y])-1):
				c = self.get(x,y)
				if c == self.unvisited: 
					return (x,y)

	# walk around, knock down walls
	def walk(self,x=-1,y=-1,level=0):

		deltas = list(self.deltas) # make copy

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

			# TODO: _ needs special handling. 
			# treat as wall/whitespace hybrid.
			# for example:  _   
			#              |_|   (contains visual space, but no space char)
			# 
			# translate _ to space, with boundary *between* char cells

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
					changed = self.fill(x3,y3,c,self.unvisited) # hulk smash!
					walls_changed += changed

				# claim empty room
				changed = self.fill(x2,y2,self.unvisited,self.visited)

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
					self.walk(x2,y2,level+1)


	# basic ASCII templates for standard mazes below...

	# produce wxh square grid
	def tessellate_square(self,w,h):
		ver = "|   " * w + '|'
		hor = "+---" * w + '+' 
		s = ''
		for i in xrange(h):
			s += hor + '\n'
			s += ver + '\n'
		s += hor + '\n'
		return s


# end class

					
if __name__ == '__main__':


	#  simple template parsing demos / regression tests
	def demo(options):

		templates = []
	
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


		template = r"""
    Example: hexagonal maze, with protected whitespace

		```+--+------+--+------+--+------+--+------+--+`
		``/    \    /    \    /    \    /    \    /    \`
		`+      +--+      +--+      +--+      +--+      +`
		``\    /    \    /    \    /    \    /    \    /`
		```+--+      +--+      +--+      +--+      +--+`
		``/    \    /    \    /    \    /    \    /    \`
		`+      +--+      +--+      +--+      +--+      +`
		``\    /    \    /    \    /    \    /    \    /`
		```+--+      +--+      +--+      +--+      +--+`
		``/    \    /    \    /    \    /    \    /    \`
		`+      +--+      +--+      +--+      +--+      +`
		``\    /    \    /    \    /    \    /    \    /`
		```+--+      +--+      +--+      +--+      +--+`
		``/    \    /    \    /    \    /    \    /    \`
		`+      +--+      +--+      +--+      +--+      +`
		``\    /    \    /    \    /    \    /    \    /`
		```+--+      +--+      +--+      +--+      +--+`
		``/    \    /    \    /    \    /    \    /    \`
		`+      +--+      +--+      +--+      +--+      +`
		``\    /    \    /    \    /    \    /    \    /`
		```+--+      +--+      +--+      +--+      +--+`
		``/    \    /    \    /    \    /    \    /    \`
		`+      +--+      +--+      +--+      +--+      +`
		``\    /    \    /    \    /    \    /    \    /`
		```+--+      +--+      +--+      +--+      +--+`
		``/    \    /    \    /    \    /    \    /    \`
		`+      +--+      +--+      +--+      +--+      +`
		``\    /    \    /    \    /    \    /    \    /`
		```+--+------+--+------+--+------+--+------+--+`

		"""

		templates.append(template)

		template = r'''
    Example: oblique, with protected whitespace

                 `+---+---+---+---+---+---+---+---+---+---+---+`
                `/   /   /   /   /   /   /   /   /   /   /   /`
               `+---+---+---+---+---+---+---+---+---+---+---+`
              `/   /   /   /   /   /   /   /   /   /   /   /`
             `+---+---+---+---+---+---+---+---+---+---+---+`
            `/   /   /   /   /   /   /   /   /   /   /   /`
           `+---+---+---+---+---+---+---+---+---+---+---+`
          `/   /   /   /   /   /   /   /   /   /   /   /`
         `+---+---+---+---+---+---+---+---+---+---+---+`
        `/   /   /   /   /   /   /   /   /   /   /   /`
       `+---+---+---+---+---+---+---+---+---+---+---+`
      `/   /   /   /   /   /   /   /   /   /   /   /`
     `+---+---+---+---+---+---+---+---+---+---+---+`
    `/   /   /   /   /   /   /   /   /   /   /   /`
   `+---+---+---+---+---+---+---+---+---+---+---+`
  `/   /   /   /   /   /   /   /   /   /   /   /`
 `+---+---+---+---+---+---+---+---+---+---+---+`
`/   /   /   /   /   /   /   /   /   /   /   /`
+---+---+---+---+---+---+---+---+---+---+---+`

		'''

		templates.append(template)


		template = r"""
    Example: mixed tessellations are also possible

    Salvidor Dali Melting Maze:
	
              ``````````````     ```````````````````````````````
              `+---+---+---+-----+--+------+--+------+--+```````
             `/   /   /   /     /  /      /  /      /  /````````
            `+---+---+---+-----+--+------+--+------+--+------+`
           `/   /   /   /     /  /      /  /      /  /      /```
          `+---+---+---+-----+--+------+--+------+--+------+````
         `/   /   /   /     /  /      /  /      /  /      /`````
        `+---+---+---+-----+--+------+--+------+--+------+---+`
       `/   /   /   /     /  /      /  /      /  /      /   /`
      `+---+---+---+-----+--+------+--+------+--+------+---+`
     `/   /   /   /     /  /      /  /      /  /      /   /`
    `+---+---+---+-----+--+------+--+------+--+------+---+`
   `/   /   /   /     /  /      /  /      /  /      /   /`
  `+---+---+---+-----+--+------+--+------+--+------+---+`
 `/   /   /   /     /  /      /  /      /  /      /   /`
`+---+---+---+-----+--+------+--+------+--+------+---+`
````/   /   /     /  /      /  /      /  /      /   /`
```+---+---+-----+--+------+--+------+--+------+---+`
    ``/    \    /    \    /    \    /    \    /    \`
    `+      +--+      +--+      +--+      +--+      +`
    ``\    /    \    /    \    /    \    /    \    /`
    ```+--+      +--+      +--+      +--+      +--+`
    ``/    \    /    \    /    \    /    \    /    \`
    `+      +--+      +--+      +--+      +--+      +`
    ``\    /    \    /    \    /    \    /    \    /`
    ```+--+      +--+      +--+      +--+      +--+`
    ``/    \    /    \    /    \    /    \    /    \`
    `+      +--+      +--+      +--+      +--+      +`
    ``\    /    \    /    \    /    \    /    \    /`
    ```+--+      +--+      +--+      +--+      +--+`
    ``/    \    /    \    /    \    /    \    /``````
    `+      +--+      +--+      +--+      +--+```
    ``\    /    \    /    \    /    \    /```````
    ```+--+      +--+      +--+      +--+```
    ```````\    /    \    /    \    /``````
      ``````+--+------+--+------+--+``
       ```````````````````      `````
"""	
		templates.append(template)


		# irregular, with text, protected whitespace
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


		# TODO: not implemented. requires special handling for _ 
		template = r"""
`__````__````__````__````__````__````__````__````__````__````__````
/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__
\__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
\__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
\__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
\__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
\__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
\__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
\__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
\__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
\__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
\__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
\__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
\__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
\__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
\__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \
/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/
\__/``\__/``\__/``\__/``\__/``\__/``\__/``\__/``\__/``\__/``\__/
"""	
	
		#templates.append(template)

		print "Here's a quick demo using templates\n"
		maze = mazeify()
		maze.scan_diagonal = options.zigzag
		maze.scan_wall_space = not options.no_wall_scan
		for template in templates:
			print "input template:"
			print ""
			print template
			maze.parseTemplate(template,options.startx,options.starty)
			out = maze.toString()
			print ""
			print "output:"
			print ""
			print out


	# parse a template file and display maze
	def parse_file(options):
		maze = mazeify()
		maze.scan_diagonal = options.zigzag
		maze.debug = options.debug	
		maze.thickness = int(options.thickness)
		maze.scan_wall_space = not options.no_wall_scan
		maze.parseTemplateFile(options.filename,options.startx,options.starty)
		out = maze.toString()
		print out


	# create basis maze
	def create_maze(options):
		maze = mazeify()
		template = maze.tessellate_square(options.width, options.height)
		maze.scan_wall_space = not options.no_wall_scan
		maze.parseTemplate(template)
		out = maze.toString()
		print out


	# parse cli options 
	parser = optparse.OptionParser()
	parser.add_option('-f', '--file', action='store', dest='filename', help='ASCII template file', default='') 
	parser.add_option('-d', '--debug', action='store_true', dest='debug', help='enable debug', default=False) 
	parser.add_option('-t', '--thickness', action='store', type="int", dest='thickness', help='wall thickness', default=1) 
	parser.add_option('-z', '--zigzag', action='store_true', dest='zigzag', help='allow diagonal scanning', default=False) 
	parser.add_option('-W', '--width', action='store', dest='width', type="int", help='width', default=20) 
	parser.add_option('-H', '--height', action='store', dest='height', type="int", help='height', default=20) 
	parser.add_option('-m', '--maze', action='store_true', dest='maze', help='create a basic maze.', default=False) 
	parser.add_option('--start-x', action='store', dest='startx', help='start scan at x', default=-1) 
	parser.add_option('--start-y', action='store', dest='starty', help='start scan at y', default=-1) 
	parser.add_option('--no-wall-scan', action='store_true', dest='no_wall_scan', help="don't scan any space that was previously taken by a wall", default=False) 

	options, args = parser.parse_args()

	if options.filename != '':
		parse_file(options)
	elif options.maze:
		create_maze(options)
	else:
		demo(options)

