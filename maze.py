#!/usr/bin/env python
#
# This draws ASCII mazes (written in Python)
# Modified from http://rosettacode.org/wiki/Maze_generation
#
#     widened cell rendering 
#     tweaked algorithm to produce variable 'curviness'
#     added optional command line options:
#    	width    height    difficulty	
#
# KS - 2015

from random import shuffle, randrange, randint
import sys

# default grid size 
w = 19
h = 20 
c = 50  # curvy-ness [0 - 100]

# read grid size from args if available
if len( sys.argv ) > 2:
	w = int( sys.argv[ 1 ] )
	h = int( sys.argv[ 2 ] )

if len( sys.argv ) > 3:
	c = int( sys.argv[ 3 ] )

deltas = [(-1, 0), (1, 0), (0, 1), (0, -1)]

def shift(l, n):
	return l[n:] + l[:n]

# get adjacent cells
def get_paths (x, y):
	global deltas, c
	d = []

    # prefer same delta?
	if randint( 0, 100 ) < c:
		deltas = shift(deltas,1)

	for (dx, dy) in deltas:
		d.append( (x + dx, y + dy) )

	return d
 
def make_maze(w, h):

	vis = [[0] * w + [1] for _ in range(h)] + [[1] * (w + 1)]
	ver = [["|   "] * w + ['|'] for _ in range(h)] + [[]]
	hor = [["+---"] * w + ['+'] for _ in range(h + 1)]

	def walk(x, y, d_old=[]):
		vis[y][x] = 1
		d = get_paths(x,y)
		
		for (xx, yy) in d:
			if vis[yy][xx]: continue
			if xx == x: hor[max(y, yy)][x] = "+   "
			if yy == y: ver[y][max(x, xx)] = "    "
			walk(xx, yy, d)

	walk(randrange(w), randrange(h))

	# punch holes
	hor[0][w-1] = '+   '
	hor[h][0] = '+   '

	for (a, b) in zip(hor, ver):
		print(''.join(a + ['\n'] + b))

make_maze(w,h)

