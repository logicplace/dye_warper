# General #
You must have Python 2.7 with PIL installed or Python 3 with Pillow installed if you can get it to work. Python 2.7 with Pillow works too.

This was only tested on Linux but it should work on Windows, you know, if you can get PIL/Pillow installed.

General use is probably going to be something like:

    python dye_warper.py -d C:\Nexon\Mabinogi -p cloth 0 0 0 0

This will never support creating palette or distortion files.

# Help #
#### -d, --data ####
You will generally probably use this version of sourcing the data, it handles the most for you. Point this to your extracted data folder, without including the data folder itself. For instance, if you have the folder: _"C:\Nexon\Mabinogi\data\color"_ then you'll want to pass `--data C:\Nexon\Mabinogi`

#### -l, --list ####
This scans the XML for available palette names (in the same way it scans to find the file paths for these names) and prints them all.

#### -p, --palette ####
Specify the palette name or full filepath.

An example palette name would be _cloth_ or _metal_ whereas an example path might be _"C:\Nexon\Mabinogi\data\color\cloth.raw"_

It attempts to open the argument as a filepath first, then it checks for it as a name (assuming --data was used).

#### -o, --output ####
Specify where to dump the final, warped palette image. By default it will dump it into the current working directory as _warped.png_.

#### -v, --verbose ####
Prints some extra information and also dumps images for: the visualization of the distortion, the raw palette, and one for each morph stage.

#### -t, --distort ###
Provide a custom distortion file. If this is used, you must also provide a custom palette file and morph options as it will not read the data folder. Mabinogi only has one distortion file so this should generally not be necessary.

You may provide more than one file. The first one provided is given an index of 1 and so forth.

#### -w, --width, -h, --height ####
When providing custom distortion information, you may explicitely provide the width and height if you want. These must be integers and you may omit one or both of them. It will attempt to guess those that are left out using the size of the palette file.

#### -m, --morph ####
When providing custom distortion information, you must provide custom morphing steps. They are executed in the order they are provided.

There are two valid forms for this: `DistortionTableID,Type,Rate` and simply `Rate`

DistortionTableID refers to the index in the provided distortion tables. The first one provided is 1 and so forth. By default the ID used is 1.

Type refers to the morph type. 1 is used for horizontal distortions and 2 is used for vertical distortions. By default it alternates, such that if the previous was 1 it would default to 2. If this is omitted for the first morph entry, the default is 1.

Rate is a float generally between 0 and 1 specifying how dramatic the distortion is. The higher the number, the more dramatic it is.

# Details #
Essentially Mabi runs through four distortions over a raw palette file. It does a horizontal distortion, then a vertical, horizontal, and vertical again. It applies these sequentially.

This distortion is generated from the combination of four random values (one for each distortion) provided by the server combined with a cached sin^2 wave and a weight (called the rate) defined per palette+distortion.

The system calculates `x' = x + rate * distortion[y + rnd]` or similarly `y' = y + rate * distortion[x + rnd]` Of course this is with respect to the bounds (ie. it's modulo math).

It then moves the pixel at x,y on the source palette to x',y or x,y' on the destination palette and repeats this process for each iteration.

The desination palette will always be 256 x 256 regarless of the size of the source palette.

Special thanks to Xcelled for doing all the hard work while I barked at him over Skype!!
