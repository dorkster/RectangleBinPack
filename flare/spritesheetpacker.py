#!/usr/bin/python3

from PIL import Image
import argparse
import flareSpriteSheetPacking

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Shrink animations definition file and image.')

    parser.add_argument('--mod', help = 'path to mod folder.', dest = 'mod',
                metavar = 'path', type = type(""), nargs = 1, required = True)

    parser.add_argument('--animation', help = 'path to a animation file.', dest = 'animation',
                metavar = 'path', type = type(""), nargs = 1)

    parser.add_argument('--tileset', help = 'path to a tileset file.', dest = 'tileset',
                metavar = 'path', type = type(""), nargs = 1)

    parser.add_argument('--resize', help = 'resizes the animation to 50%% of its original size', action = 'store_true', default = False)

    parser.add_argument('--save-always', dest = "save_always", help = 'saves the animation and image even if the new size is not smaller', action = 'store_true', default = False)

    args = parser.parse_args()
    if args.mod is None and (args.animation is None or args.tileset is None):
        print("Animation/tileset and mod path must be supplied.")
        exit(1)
    elif args.animation is not None and args.tileset is not None:
        print("Can't resize both an animation and a tileset. Aborting.")
        exit(1)
    else:
        mod = args.mod[0]
        imgnames = []

        animname = None
        tilesetname = None
        defname = None
        if args.animation is not None:
            defname = animname = args.animation[0]
        elif args.tileset is not None:
            defname = tilesetname = args.tileset[0]

        if not defname:
            print('No animation or tileset definition. Exiting.')
            exit(1)

        with open(defname) as f:
            for line in f.readlines():
                if (animname is not None and line.startswith('image=')):
                    img_string = line.split('=')[1].rstrip('\n')
                    img_fields = img_string.split(',')
                    if len(img_fields) > 1:
                        imgnames.append((mod + '/' + img_fields[0], img_fields[0], img_fields[1]))
                    else:
                        imgnames.append((mod + '/' + img_fields[0], img_fields[0], flareSpriteSheetPacking.DEFAULT_IMG_ID))
                elif (tilesetname is not None and line.startswith('img=')):
                    # TODO support tilesets with multiple images
                    img_string = line.split('=')[1].rstrip('\n')
                    imgnames = [(mod + '/' + img_string, img_string, flareSpriteSheetPacking.DEFAULT_IMG_ID)]
        if len(imgnames) == 0:
            print('No image path found in the spritesheet definition: ' + defname)
            exit(1)

        parsed_data = {}

        for imgname in imgnames:
            imgid = imgname[2]

            if animname is not None:
                parsed_data[imgid] = flareSpriteSheetPacking.parseAnimationFile(animname, imgname)
            elif tilesetname is not None:
                parsed_data[imgid] = flareSpriteSheetPacking.parseTilesetFile(tilesetname, imgname)

            imgs = flareSpriteSheetPacking.markDuplicates(parsed_data[imgid][0])

            if args.resize:
                imgs = flareSpriteSheetPacking.resizeImages(imgs)

            rects = flareSpriteSheetPacking.extractRects(imgs)
            newrects = flareSpriteSheetPacking.findBestEnclosingRectangle(rects, parsed_data[imgid][1])
            parsed_data[imgid][0] = flareSpriteSheetPacking.matchRects(newrects, parsed_data[imgid][0])

            size = flareSpriteSheetPacking.calculateImageSize(parsed_data[imgid][0])
            oldsize = parsed_data[imgid][1]["original_image_size"]

            if args.save_always or (size[0] * size[1] < oldsize[0] * oldsize[1]):
                flareSpriteSheetPacking.writeImageFile(imgname, parsed_data[imgid][0], size)

        if animname is not None:
            flareSpriteSheetPacking.writeAnimationfile(animname, imgnames, parsed_data)
        elif tilesetname is not None:
            flareSpriteSheetPacking.writeTilesetFile(tilesetname, imgnames, parsed_data)
