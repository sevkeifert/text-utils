# text-utils
This repostory will contain miscellaneous command line utilities that slice and dice text, along with a few retro ASCII games.

Utilities:

calc 
> A simple command line calculator (just a wrapper for bc). 

cleantext 
> This script translates Microsoft Word characters (such as "smart" quotes) into standard ASCII characters.  All other non-standard MS chars are removed.  

index-java-classes.py
> This script indexes the java classes and java jars found under a directory.
It lists out every single class, file path, and jar file (if any).
 
outline 
> Create and parse text outlines from simple markup.  Supports roman numeral (I. A. 1. a.) and decimal formats(1, 1.2, 1.2.3).  Written in Perl.

maze.py 
> Draws a basic ASCII maze.  Accepts width, height and difficulty parameters.

maze-ify-ascii.py
> This script turns an ASCII tessellation into a maze.  The class includes methods for graphically manipulating text data, such as fill, 2D find/replace, parsing space withing character cell, edge filters, and interior/exterior detection of closed shapes.

Note: maze-ify-ascii.py is written for Python 2.x.  maze-ify-ascii-v3.py has been ported to Python 3.x.
 
svi
> secure vi text editor - to allow editing/viewing AES encrypted files from the command line.  (Bash script)
