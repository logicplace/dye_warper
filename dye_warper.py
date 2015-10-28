#!/usr/bin/env python
#-*- coding:utf-8 -*-

# Copyright 2015 Kadalyn (logicplace.com)
# MIT Licensed

#
# You must have Python 2.7 with PIL installed.
# or Python 3 with Pillow installed if you can get it to work.
# Python 2.7 with Pillow works too.
# This was only tested on Linux but it should work on Windows,
# you know, if you can get PIL/Pillow installed.
# See dye_warper.py --help for usage.
# General use is probably going to be something like:
#  python dye_warper.py -d C:\Nexon\Mabinogi -p cloth 0 0 0 0
#
# This will never support creating palette or distortion files.
#

import sys, os, re, struct, math
from argparse import ArgumentParser
from xml.dom.minidom import parse as xmlParse

try: from PIL import Image
except ImportError: import Image

parser = ArgumentParser(add_help=False,
	description = "Warp dye palettes from Mabinogi."
)
parser.add_argument("-?", "--help", action="help")
parser.add_argument("--version", action="version", version="1")

source = parser.add_mutually_exclusive_group()
source.add_argument("-d", "--data",
	help="Data folder location, not including the data folder itself."
)
nodata = parser.add_argument_group()
nodata.add_argument("-t", "--distort", action="append",
	help="Distortion file(s). First has ID of 1 etc."
)
nodata.add_argument("-w", "--width",
	help="Palette width. By default tries to find a square."
)
nodata.add_argument("-h", "--height",
	help="Palette height. By default tries to find a square."
)
nodata.add_argument("-m", "--morph", action="append",
	help="Perform a morph (does these sequentially). Format is DistortionTableID,Type,Rate. Type is 1 for horz and 2 for vert. You may specify only a rate and it will assume a distortion table ID of 1 and a type of whatever the last one wasn't (first entry would be 1)."
)

parser.add_argument("-l", "--list", action="store_true",
	help="List available palettes"
)
parser.add_argument("-p", "--palette",
	help="Palette name or file to use. Use -l to list available palettes."
)
parser.add_argument("-o", "--output", default="warped.png",
	help="File to save warped image to."
)
parser.add_argument("-v", "--verbose", action="store_true", help="Verbose details.")
parser.add_argument("args", nargs="*", help="Morphing arguments.")

args = parser.parse_args(sys.argv[1:])

def readDistortionFile(filename):
	f = open(filename, "rb")
	binary = f.read()
	vals = struct.unpack("B" * len(binary), binary)
	f.close()
	return vals
#enddef

paletteFile, distortions, morphs, width, height = None, None, None, None, None
if args.data:
	xmlFile = os.path.join(args.data, "data", "db", "colortable.xml")
	xml = xmlParse(xmlFile)

	if args.palette:
		try: paletteFile = open(args.palette, "rb")
		except IOError: pass
	#endif

	if args.list or paletteFile is None:
		nameParser = re.compile(r'^data/color/([^.]+)\.raw$', re.I)
		for colorTable in xml.getElementsByTagName("ColorTableList")[0].getElementsByTagName("ColorTable"):
			bitmap = colorTable.getAttribute("Bitmap")
			name = nameParser.match(bitmap).group(1)
			if name:
				if args.list: print(name)
				elif name.lower() == args.palette.lower():
					paletteFile = open(os.path.join(args.data, bitmap.lower()), "rb")

					# Find dimensions:
					width = int(colorTable.getAttribute("Width"))
					height = int(colorTable.getAttribute("Height"))

					# Find morphs:
					morphs = [(
						i - 1, # Index in "distortions"
						colorTable.getAttribute("DistortType%i" % i),
						float(colorTable.getAttribute("DistortRate%i" % i)),
					) for i in range(1, 5)]

					# Find distortion:
					distortID1 = colorTable.getAttribute("DistortID1")
					distortID2 = colorTable.getAttribute("DistortID2")
					distortID3 = colorTable.getAttribute("DistortID3")
					distortID4 = colorTable.getAttribute("DistortID4")

					dMap = dict([(
						elem.getAttribute("DistortMapID"),
						os.path.join(args.data, elem.getAttribute("DistortBaseFile"))
					) for elem in xml.getElementsByTagName("DistortMap")])

					if distortID1 == distortID2 == distortID3 == distortID4:
						distortions = [readDistortionFile(dMap[distortID1])] * 4
					else:
						distortions = [
							readDistortionFile(dMap[distortID1]),
							readDistortionFile(dMap[distortID2]),
							readDistortionFile(dMap[distortID3]),
							readDistortionFile(dMap[distortID4])
						]
					#endif
					break
				#endif
			#endif
		#endfor

		if args.list: sys.exit(0)
	#endif
else:
	try: paletteFile = open(args.palette, "rb")
	except IOError:
		print("ERROR: Palette file not found.")
		sys.exit(1)
	#endtry

	try:
		distortions = [readDistortionFile(df) for df in args.distort]
	except IOError as e:
		print("ERROR: Distortion file not found: " + e.filename)
		sys.exit(1)
	#endtry

	prevType, morphs = "2", []
	for x in args.morph:
		try: dRate = float(x)
		except ValueError:
			dID, dType, dRate = x.split(",")
			dID = int(dID) - 1
			if dType not in ["1", "2"]:
				print("ERROR: Morph type must be 1 or 2.")
				sys.exit(4)
			#endif
			dRate = float(dRate)
		else: dID, dType = 0, {"1":"2","2":"1"}[prevType]
		prevType = dType

		morphs.append((dID, dType, dRate))
	#endfor

	if args.width: width = int(args.width)
	if args.height: height = int(args.height)
#endif

expecting = len(args.morph) if args.morph else 4
if len(args.args) != expecting:
	print("ERROR: Must have exactly %i morphing arguments specified." % expecting)
	sys.exit(3)
#endif

# By this point we should have all the files, but verify.
if paletteFile is None or distortions is None or morphs is None:
	print("ERROR: Palette or distortion files not found or morphs not defined.")
	sys.exit(2)
#endif

if args.verbose:
	for i, d in enumerate(distortions):
		print("Dumping visualization of distortion map %i to distortion%i.png" % (i,i))
		dvis = Image.new("1", (len(d), 256), "white")
		for x, y in enumerate(d):
			dvis.putpixel((x, 255 - y), 0)
		#endfor
		dvis.save("distortion%i.png" % i)
	#endfor
#endif

# Read the paletteFile...
paletteBin = paletteFile.read()
numPixels = len(paletteBin) / 4
if width is None and height is None:
	sq = math.sqrt(numPixels)
	if sq == math.floor(sq): width = height = int(sq)
	else:
		print("ERROR: Palette is not square!!")
		sys.exit(5)
	#endif
elif width is None:
	width = numPixels / float(height)
	if width == math.floor(width): width = int(width)
	else:
		print("ERROR: Palette is not rectangular!!")
		sys.exit(5)
	#endif
elif height is None:
	height = numPixels / float(width)
	if height == math.floor(height): height = int(height)
	else:
		print("ERROR: Palette is not rectangular!!")
		sys.exit(5)
	#endif
#endif

flashyPixels = 0
def chopWarn(x):
	global flashyPixels
	if x[3] not in b"\x00\xFF":
		flashyPixels += 1
	#endif
	return x[0:3]
#enddef

pixels = [struct.unpack(">BBB", chopWarn(paletteBin[i:i+4])) for i in range(0, len(paletteBin), 4)]
paletteFile.close()

if flashyPixels:
	print("WARNING: This palette contains flashies (%i pixel%s) that will not be represented in the final rendering." % (flashyPixels, "s" if flashyPixels > 1 else ""))
#endif

# ...and throw into PIL.
palette = Image.new("RGB", (width, height))
palette.putdata(pixels)
if args.verbose:
	print("Dumping raw palette to raw_palette.png")
	palette.save("raw_palette.png")
#endif

# Now do morphing...
currentWidth, currentHeight = width, height
finalWidth, finalHeight = 256, 256
for i, morph in enumerate(morphs):
	dID, dType, dRate = morph
	if args.verbose: print("Performing morph %i: type %s rate %f" % (i, dType, dRate))

	shift, distortion = int(args.args[i]), distortions[dID]
	distortionLen = len(distortion)

	newPalette = Image.new("RGB", (finalWidth, finalHeight))
	if dType == "1":
		# Horizontal morph (x-shift)
		for y in range(finalHeight):
			for x in range(finalWidth):
				dx = x + int(dRate * distortion[(y + shift) % distortionLen])
				newPalette.putpixel((dx % finalWidth, y), palette.getpixel((x % currentWidth, y % currentHeight)))
			#endfor
		#endfor
	elif dType == "2":
		# Vertical morph (y-shift)
		for y in range(finalHeight):
			for x in range(finalWidth):
				dy = y + int(dRate * distortion[(x + shift) % distortionLen])
				newPalette.putpixel((x, dy % finalHeight), palette.getpixel((x % currentWidth, y % currentHeight)))
			#endfor
		#endfor
	#endif

	palette = newPalette
	currentWidth, currentHeight = finalWidth, finalHeight
	if args.verbose and i < len(morphs) - 1:
		fn, ext = args.output.rsplit(".", 1)
		nfn = "%s-%i.%s" % (fn, i, ext)
		print("Saving morph stage to " + nfn)
		palette.save(nfn)
	#endif
#endfor

if args.verbose: print("Saving to " + args.output)
palette.save(args.output)
