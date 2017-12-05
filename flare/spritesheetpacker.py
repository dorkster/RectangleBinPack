#!/usr/bin/python2

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
        print "Animation/tileset and mod path must be supplied."
        exit(1)
    elif args.animation is not None and args.tileset is not None:
        print "Can't resize both an animation and a tileset. Aborting."
        exit(1)
    else:
        mod = args.mod[0]
        imgname = None

        animname = None
        tilesetname = None
        defname = None
        if args.animation is not None:
            defname = animname = args.animation[0]
        elif args.tileset is not None:
            defname = tilesetname = args.tileset[0]

        with open(defname) as f:
            for line in f.readlines():
                if (animname is not None and line.startswith('image=')) or (tilesetname is not None and line.startswith('img=')):
                    imgname=mod + '/' + (line.split('=')[1]).rstrip('\n')
        if imgname == None:
            print 'No image path found in the spritesheet definition:', defname
            exit(1)

        if animname is not None:
            imgrects, additionalinformation = flareSpriteSheetPacking.parseAnimationFile(animname, imgname)
        elif tilesetname is not None:
            imgrects, additionalinformation = flareSpriteSheetPacking.parseTilesetFile(tilesetname, imgname)

        imgs = flareSpriteSheetPacking.markDuplicates(imgrects)

        if args.resize:
            imgs = flareSpriteSheetPacking.resizeImages(imgs)

        rects = flareSpriteSheetPacking.extractRects(imgs)
        newrects = flareSpriteSheetPacking.findBestEnclosingRectangle(rects)
        imgrects = flareSpriteSheetPacking.matchRects(newrects, imgrects)

        size = flareSpriteSheetPacking.calculateImageSize(imgrects)
        oldsize = additionalinformation["original_image_size"]

        if args.save_always or (size[0] * size[1] < oldsize[0] * oldsize[1]):
            flareSpriteSheetPacking.writeImageFile(imgname, imgrects, size)
            if animname is not None:
                flareSpriteSheetPacking.writeAnimationfile(animname, imgrects, additionalinformation)
            elif tilesetname is not None:
                flareSpriteSheetPacking.writeTilesetFile(tilesetname, imgrects, additionalinformation)
