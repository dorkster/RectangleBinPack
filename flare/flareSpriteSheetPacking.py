#!/usr/bin/python3
# This is just a library file for the spritesheetpacker.py executable

from PIL import Image
from PIL import ImageChops
import os
import random
import sys
import time
import tempfile
import subprocess
import hashlib

import numpy as np

DEFAULT_IMG_ID = '_default_'

try:
    os.nice(15)
except:
    print("not able to be nice!")

def parseAnimationFile(fname, imgname):
    images = []
    raw_img = Image.open(imgname[0])
    print('processing ' + imgname[0])

    # getbbox() requires pixels to be 0 on all channels to work properly
    black = Image.new('RGBA', raw_img.size)
    img = Image.alpha_composite(raw_img, black)

    def processNextSection():
        images = []
        if 'position' not in locals():
            print("Error: image detected as not compressed but has no position\n")
        if imgname[2] != DEFAULT_IMG_ID:
            print("Error: image has ID, but section is not compressed\n")
            return
        for index in range(0, frames):
            for direction in range(0,8):
                x = (position + index) * render_size_x
                y = direction * render_size_y
                w = x + render_size_x
                h = y + render_size_y
                imgrect = (x, y, w, h)
                partimg = img.copy().crop(imgrect)
                bbox = partimg.split()[partimg.getbands().index('A')].getbbox()
                roffset = (render_offset_x, render_offset_y)

                if bbox is None:
                    print("Warning in: " + imgname[1])
                    print("* empty image at: (" + str(x) + ", " + str(y) + ", " + str(w) + ", " + str(h) + ")")
                    print("* name / position / direction is: " + sectionname + " / " + str(position) + " / " + str(direction))
                    print("* resizing to 1x1" + "\n")
                    bbox = (0, 0, 1, 1)
                    roffset = (0, 0)

                newimg = partimg.crop(bbox)

                f = {
                    "name" : sectionname,
                    "type" : _type,
                    "direction" : direction,
                    "index" : index,
                    "duration" : duration,
                    "frames" : frames,
                    "renderoffset" : (roffset[0]-bbox[0], roffset[1]-bbox[1]),
                    "image" : newimg,
                    "width" : newimg.size[0],
                    "height" : newimg.size[1],
                    "active_frame" : active_frame,
                    "active_sub_frame": active_sub_frame,
                    "frametag": ""
                }
                images += [f]

        return images


    animation = open(fname, 'r')
    lines = animation.readlines();
    animation.close()

    additionalinformation = {}
    additionalinformation["original_image_size"] = img.size
    additionalinformation["cached_input"] = ''
    additionalinformation["cached_output"] = ''
    additionalinformation["imagename"] = imgname

    firstsection = True
    newsection = False
    compressedloading = False
    active_frame = None
    active_sub_frame = None
    for line in lines:
        if line.startswith("#flare_sprite_packer_input="):
            additionalinformation["cached_input"] = line.split("=")[1].strip()

        if line.startswith("#flare_sprite_packer_output="):
            additionalinformation["cached_output"] = line.split("=")[1].strip()

        if line.startswith("render_size"):
            value = line.split("=")[1]
            render_size_x = int(value.split(",")[0])
            render_size_y = int(value.split(",")[1])

        if line.startswith("render_offset"):
            value = line.split("=")[1]
            render_offset_x = int(value.split(",")[0])
            render_offset_y = int(value.split(",")[1])

        if line.startswith("position"):
            position = int(line.split("=")[1])

        if line.startswith("frames"):
            frames = int(line.split("=")[1])

        if line.startswith("duration"):
            duration = line.split("=")[1].strip()

        if line.startswith("type"):
            _type = line.split("=")[1].strip()

        if line.startswith("active_frame"):
            active_frame = line.split("=")[1].strip()

        if line.startswith("active_sub_frame"):
            active_sub_frame = line.split("=")[1].strip()

        if line.startswith("frame="):
            compressedloading = True;
            vals = line.split("=")[1].split(",")
            index = int(vals[0])
            direction = int(vals[1])
            x = int(vals[2])
            y = int(vals[3])
            w = x + int(vals[4])
            h = y + int(vals[5])
            render_offset_x = int(vals[6])
            render_offset_y = int(vals[7])

            if len(vals) > 8:
                frametag = vals[8].rstrip('\n')
            else:
                frametag = ""

            if (frametag == "" and imgname[2] == DEFAULT_IMG_ID) or (imgname[2] != DEFAULT_IMG_ID and imgname[2] == frametag):
                imgrect = (x, y, w, h)
                partimg = img.copy().crop(imgrect)
                bbox = partimg.split()[partimg.getbands().index('A')].getbbox()

                if bbox is None:
                    print("Warning in: " + imgname[1])
                    print("* empty image at: (" + str(x) + ", " + str(y) + ", " + str(w) + ", " + str(h) + ")")
                    print("* name / direction is: " + sectionname + " / " + str(direction))
                    print("* resizing to 1x1" + "\n")
                    bbox = (0, 0, 1, 1)
                    render_offset_x = 0
                    render_offset_y = 0

                newimg = partimg.crop(bbox)

                f = {
                    "name" : sectionname,
                    "type" : _type,
                    "direction" : direction,
                    "index" : index,
                    "duration" : duration,
                    "frames" : frames,
                    "renderoffset" : (render_offset_x-bbox[0], render_offset_y-bbox[1]),
                    "image" : newimg,
                    "active_frame" : active_frame,
                    "active_sub_frame" : active_sub_frame,
                    "frametag": frametag,
                }
                images += [f]

        if line.startswith("["):
            newsection = True
            if not firstsection and not compressedloading:
                images += processNextSection()
            compressedloading = False
            sectionname=line.strip()[1:-1]
            if firstsection:
                additionalinformation['firstsection'] = sectionname
            firstsection=False

    if not compressedloading:
        images += processNextSection()
    return [images, additionalinformation]

def parseTilesetFile(fname, imgname):
    images = []
    # imgtag = imgname[1]
    imgname = imgname[0]
    raw_img = Image.open(imgname)
    print('processing ' + imgname)

    # getbbox() requires pixels to be 0 on all channels to work properly
    black = Image.new('RGBA', raw_img.size)
    img = Image.alpha_composite(raw_img, black)

    tileset = open(fname, 'r')
    lines = tileset.readlines();
    tileset.close()

    additionalinformation = {}
    additionalinformation["original_image_size"] = img.size
    additionalinformation["animations"] = {}
    additionalinformation["cached_input"] = ''
    additionalinformation["cached_output"] = ''

    for line in lines:
        if line.startswith("#flare_sprite_packer_input="):
            additionalinformation["cached_input"] = line.split("=")[1].strip()

        if line.startswith("#flare_sprite_packer_output="):
            additionalinformation["cached_output"] = line.split("=")[1].strip()

        if line.startswith("img="):
            imgname = line.split("=")[1] # keep this information to write out again!
            additionalinformation["imagename"] = imgname

        if line.startswith("tile="):
            vals = line.split("=")[1].split(",")
            index = int(vals[0])
            x = orig_x = int(vals[1])
            y = orig_y = int(vals[2])
            w = x + int(vals[3])
            h = y + int(vals[4])
            render_offset_x = int(vals[5])
            render_offset_y = int(vals[6])
            oldrect = imgrect = (x, y, w, h)
            oldoffset = (render_offset_x, render_offset_y)
            partimg = img.copy().crop(imgrect)
            bbox = partimg.split()[partimg.getbands().index('A')].getbbox()

            if bbox is None:
                print("Warning in: " + imgname.strip('\n'))
                print("* empty image at: (" + str(x) + ", " + str(y) + ", " + str(w) + ", " + str(h) + ")")
                print("* tile ID is: " + str(index))
                print("* resizing to 1x1" + "\n")
                bbox = (0, 0, 1, 1)
                render_offset_x = 0
                render_offset_y = 0

            newimg = partimg.crop(bbox)

            f = {
                "index" : index,
                "renderoffset" : (render_offset_x-bbox[0], render_offset_y-bbox[1]),
                "image" : newimg,
                "imagehash" : hashlib.sha1(newimg.tobytes()).hexdigest(),
                "oldrect" : oldrect, # animations can't be packed, so we'll need to restore the old size if this tile is an animation
                "oldoffset" : oldoffset,
            }
            images += [f]

        if line.startswith("animation"):
            animtile = None
            # line += ";"
            if not line.endswith(";\n"):
                line = line.rstrip("\n") + ";\n"
            vals = line.split("=")[1].split(";")
            if len(vals) >= 1:
                animtiles = list(filter(lambda s: s["index"] == int(vals[0]), images))
                animtile = animtiles[0]
            else:
                continue

            if animtile is not None:
                animtile["image"] = img.copy().crop(animtile["oldrect"])
                animtile["renderoffset"] = animtile["oldoffset"]
                valstart = iter(vals)
                next(valstart) # skip the index
                is_first_frame = True
                for animframe in valstart:
                    frame = animframe.split(",")
                    if len(frame) != 3:
                        break
                    # tile animations don't support varrying width/height, so don't crop
                    imgrect = (int(frame[0]), int(frame[1]), int(frame[0]) + animtile["image"].size[0], int(frame[1]) + animtile["image"].size[1])
                    newimg = img.copy().crop(imgrect)
                    newhash = hashlib.sha1(newimg.tobytes()).hexdigest()
                    if additionalinformation["animations"].get(animtile["index"]) is None:
                        additionalinformation["animations"][animtile["index"]] = []
                    additionalinformation["animations"][animtile["index"]].append((newhash, frame[2]))

                    f = {
                        "index" : animtile["index"],
                        "renderoffset" : animtile["renderoffset"],
                        "image" : newimg,
                        "imagehash" : newhash,
                        "oldrect" : animtile["oldrect"],
                        "oldoffset" : animtile["oldoffset"],
                    }
                    images += [f]

                    # the tile that points to an animation should be the first frame of said animation
                    if is_first_frame:
                        is_first_frame = False
                        animtile["image"] = newimg.copy()
                        animtile["imagehash"] = hashlib.sha1(newimg.tobytes()).hexdigest()

    return [images, additionalinformation]

def markDuplicates(images):
    # assign global unique ids to each image:
    gid=0
    for im in images:
        im["gid"] = gid
        im["imagehash"] = hashlib.sha1(im["image"].tobytes()).hexdigest()
        gid += 1

    for im1 in images:
        for im2 in images:
            if im1["imagehash"] == im2["imagehash"]:
                smallergid = min(im1["gid"], im2["gid"])
                if "isequalto" in im1:
                    im1["isequalto"] = min(smallergid, im1["isequalto"])
                else:
                    im1["isequalto"] = smallergid

                if "isequalto" in im2:
                    im2["isequalto"] = min(smallergid, im2["isequalto"])
                else:
                    im2["isequalto"] = smallergid


    for im in images:
        if "isequalto" in im:
            if im["isequalto"] == im["gid"]:
                del im["isequalto"]

    return images

def resizeImages(imgs):
    for index, img in enumerate(imgs):
        imag = img["image"].load()
        for y in xrange(img["image"].size[1]):
            for x in xrange(img["image"].size[0]):
                if imag[x, y] == (255, 0, 255, 0):
                    imag[x, y] = (0, 0, 0, 0)

        newsize = (img["image"].size[0]/2, img["image"].size[1]/2)
        imgs[index]["image"] = img["image"].resize(newsize, Image.BICUBIC)
        imgs[index]["renderoffset"] = (imgs[index]["renderoffset"][0]/2, imgs[index]["renderoffset"][1]/2)
    return imgs

def extractRects(images):
    """returns an array of dicts having only width, height and index.
    The index describes the position in the passed array"""
    ret = []
    for xindex, x in enumerate(images):
        if not "isequalto" in x:
            r = {"width" : x["image"].size[0], "height" : x["image"].size[1], "index" : xindex, "gid" : x["gid"]}
            ret += [r]
    return ret

def findBestEnclosingRectangle(rects, additionalinformation):
    rectPassString = ""
    for rect in sorted(rects, key = lambda x: x["index"]):
        rectPassString += " " + str(rect["width"]) + " " + str(rect["height"])

    cache_input = rectPassString.strip()
    if additionalinformation["cached_input"] != "" and additionalinformation["cached_output"] != "" and cache_input == additionalinformation["cached_input"]:
        # cache found, use it to populate positions
        print("Cache found! Skipping rectpacker.")
        positions = []
        rect_coords = additionalinformation["cached_output"].split()
        assert(len(rect_coords) % 2 == 0)
        for i in range(0, len(rect_coords), 2):
            positions.append(rect_coords[i] + ' ' + rect_coords[i+1])
    else:
        # no cache found, run the packer binary
        print("No cache found. Running rectpacker...")
        tf = tempfile.mkstemp()
        if 'win' in sys.platform:
            string = sys.path[0] + "\\..\\bestEnclosingRect\\rectpacker.exe " + rectPassString
        elif sys.platform.startswith('linux'):
            string = sys.path[0] + "/../bestEnclosingRect/rectpacker " + rectPassString
        p = subprocess.call(string, stdout = tf[0], shell = True)

        filehandle = open(tf[1], 'r')
        positions = filehandle.readlines()
        filehandle.close()

        # create cache
        cache_output = ""
        for pos in positions:
            cache_output += pos.strip() + ' '
        cache_output = cache_output.rstrip()

        additionalinformation["cached_input"] = cache_input
        additionalinformation["cached_output"] = cache_output

    for pos, rect in zip(positions, rects):
        rect["x"] = int(pos.split()[0])
        rect["y"] = int(pos.split()[1])
    return rects

def matchRects(newrects, images):
    for r in newrects:
        index = r["index"]
        images[index]["x"] = r["x"]
        images[index]["y"] = r["y"]
        #assert(images[index]["width"] == r["width"])
        #assert(images[index]["height"] == r["height"])
    for im in images:
        if "isequalto" in im:
            im["x"] = images[im["isequalto"]]["x"]
            im["y"] = images[im["isequalto"]]["y"]

    return images

def calculateImageSize(images):
    w, h = 0, 0
    for n in images:
        w = max(n["x"] + n["image"].size[0], w)
        h = max(n["y"] + n["image"].size[1], h)
    return (w, h)

def writeImageFile(imgname, images, size):
    result = Image.new('RGBA', size, (0, 0, 0, 0))
    for r in images:
        assert (r["x"] + r["image"].size[0] <= size[0])
        assert (r["y"] + r["image"].size[1] <= size[1])
        result.paste(r["image"], (r["x"], r["y"]))
    print('Saving: ' + imgname[0])
    result.save(imgname[0], option = 'optimize')

def writeAnimationfile(animname, imgnames, parsed_data):

    def write_section(name):
        framelist = list(filter(lambda s: s["name"] == name, images))
        f.write("\n")
        f.write("["+name+"]\n")
        if len(framelist)>0:
            f.write("frames="+str(framelist[0]["frames"])+"\n")
            f.write("duration="+str(framelist[0]["duration"])+"\n")
            f.write("type="+str(framelist[0]["type"])+"\n")
            if framelist[0]["active_frame"]:
                f.write("active_frame="+str(framelist[0]["active_frame"])+"\n")
            if framelist[0]["active_sub_frame"]:
                f.write("active_sub_frame="+str(framelist[0]["active_sub_frame"])+"\n")
            for x in framelist:
                #frame=index,direction,x,y,w,h,offsetx,offsety
                f.write("frame=" + str(x["index"]) + "," + str(x["direction"]) + "," + str(x["x"]) + "," + str(x["y"]) + "," + str(x["image"].size[0]) + "," + str(x["image"].size[1]) + "," + str(x["renderoffset"][0]) + "," + str(x["renderoffset"][1]))
                if x["frametag"] != "":
                    f.write(',' + x["frametag"])
                f.write('\n')
        else:
            f.write("frames=1\n")
            f.write("duration=1s\n")
            f.write("type=back_forth\n")


    f = open(animname,'w')

    for imgname in imgnames:
        imgid = imgname[2]
        f.write("image=" + imgname[1])
        if imgname[2] != DEFAULT_IMG_ID:
            f.write(',' + imgname[2])
        f.write("\n")

    for imgname in imgnames:
        imgid = imgname[2]
        images = parsed_data[imgid][0]
        extra = parsed_data[imgid][1]

        # cache
        # TODO support cache for multi-image animations
        single_img = (len(imgnames) == 1 and imgid == DEFAULT_IMG_ID)

        if single_img and extra["cached_input"] and extra["cached_output"]:
            f.write("#flare_sprite_packer_input=" + extra["cached_input"]+"\n")
            f.write("#flare_sprite_packer_output=" + extra["cached_output"]+"\n\n")

        firstsection = extra["firstsection"]
        sectionnames = {}
        for img in images:
            sectionnames[img["name"]] = True

        for section in sectionnames:
            write_section(section)

    f.close()

def writeTilesetFile(animname, imgnames, parsed_data):
    f = open(animname,'w')

    for imgname in imgnames:
        imgid = imgname[2]
        images = parsed_data[imgid][0]
        extra = parsed_data[imgid][1]

        # cache
        # TODO support cache for multi-image animations
        single_img = (len(imgnames) == 1 and imgid == DEFAULT_IMG_ID)

        f.write('[tileset]\n')
        f.write('img=' + imgname[1] + '\n')
        if single_img and extra["cached_input"] and extra["cached_output"]:
            f.write("#flare_sprite_packer_input=" + extra["cached_input"]+"\n")
            f.write("#flare_sprite_packer_output=" + extra["cached_output"]+"\n")

        for x in images:
            if (x.get("skiptile")) == True:
                continue

            f.write("tile=" + str(x["index"]) + "," + str(x["x"]) + "," + str(x["y"]) + "," + str(x["image"].size[0]) + "," + str(x["image"].size[1]) + "," + str(x["renderoffset"][0]) + "," + str(x["renderoffset"][1]))
            f.write("\n")
            x["skiptile"] = True

            if extra["animations"].get(x["index"]) is not None:
                f.write("animation=" + str(x["index"]) + ";")
                for y in extra["animations"][x["index"]]:
                    animtile = list(filter(lambda s: s["imagehash"] == y[0], images))
                    if animtile is not None:
                        f.write(str(animtile[0]["x"]) + "," + str(animtile[0]["y"]) + "," + str(y[1]) + ";")
                f.write("\n")

            sameid = list(filter(lambda s: s["index"] == x["index"], images))
            for t in sameid:
                t["skiptile"] = True

    f.close()


if __name__ == "__main__":
    print("This is just a library file containing lots of functions.")
    print("Run spritesheetpacker.py instead")





