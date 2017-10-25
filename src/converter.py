#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
import os
from PIL import Image, ImageDraw, ImageFont
import argparse


def generate_char_image(font_file, chr_code, font_size, img_dimensions, bitmap_out_dir):
    """Generate a png image for a character.
    
    Args:
        font_file (string): Location of TTF of font to use
        chr_code (int): Integer code of character
        font_size (int): Font size in pts
        img_dimensions (int): Image will be a square of this size.
        bitmap_out_dir (string): Output directory
    """
    chr_symbol = chr(chr_code)
    image = Image.new("RGB", (img_dimensions,img_dimensions), (255,255,255)) #can do rgba too but not needed
    font = ImageFont.truetype(font_file, font_size)
    draw = ImageDraw.Draw(image)
    draw.text((10, 10), chr_symbol, (0,0,0), font=font)
    # to make image crisper
    img_resized = image.resize((img_dimensions//2,img_dimensions//2))
    image.save(os.path.join(bitmap_out_dir, "_".join(["ascii",str(chr_code),str(font_size)]) + ".png"))

def generate_images_for_charset(font_file, font_size, img_dimensions, bitmap_out_dir):
    """Generate images for a charset with font and size settings.
    
    Args:
        font_file (string): Location of TTF of font to use
        font_size (int): Font size in pts
        img_dimensions (int): Image will be a square of this size.
        bitmap_out_dir (string): Output directory
    """
    # entire displayable ascii set
    for i in range(32,256):
        # shows up as boxes, ignore for now
        if i>=127 and i<=160:
            continue
        # sanity check
        try:
            chr_symbol = chr(i)
        except Exception:
            print(i, "couldnt render")
            continue
        print("Generating", i, end="\r")
        generate_char_image(font_file, i, font_size, img_dimensions, bitmap_out_dir)

    print("\ndone")

def avg_brightness_pixel(pixel):
    """ Calculate the average brightness of a pixel.
    
    Args:
        pixel (tuple) : Tuple containing pixel densities, must be length 3 (RGB) or 4(RGBA)
    
    Returns:
        float: average brightness of a pixel
    
    Raises:
        Exception: If not a RGB or RGBA pixel
    """
    # rgb
    if len(pixel) == 3:
        return sum(pixel) / len(pixel)
    elif len(pixel) == 4:
        # TODO: verify correctness
        # rgba pixel, multiply with intensity. Not sure if correct. 
        return sum(pixel[:-1])/3 + pixel[-1]/255
    raise Exception("provide a RGB or RGBA tuple")

def avg_brightness_calculator(pix, w, h):
    """ Calculate the average brightness of an image.

    Args:
       pix (PIL.PixelAccess) : The array of pixels
        w (int) : width of image
        h (int) : height of image
    
    Returns:
        float : The average brightness of image
    """
    brightness_avg = 0
    img_size = w*h
    for i in range(w):
        for j in range(h):
            brightness_avg += avg_brightness_pixel(pix[i,j]) / img_size
    return brightness_avg


if __name__ == "__main__":
    """Quick testing of script in dev
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--img", help="Image file to convert", default=None)
    parser.add_argument("--font-path", help="Font file", default=None)
    parser.add_argument("--font-size", help="Font size in pt", default=48, type=int)
    parser.add_argument("--bitmap-size", help="Size of font bitmap", default=64, type=int)
    parser.add_argument("--bitmap-out-dir", help="output directory for writing font bitmaps", default="font-bitmaps")

    args = parser.parse_args()

    img_file = args.img
    font_file = args.font_path
    font_size = args.font_size
    img_dimensions = args.bitmap_size
    bitmap_out_dir = os.path.abspath(args.bitmap_out_dir)

    if not os.path.exists(bitmap_out_dir):
        os.makedirs(bitmap_out_dir)

    if font_file:
        generate_images_for_charset(font_file, font_size, img_dimensions, bitmap_out_dir)
    if img_file:
        im = Image.open(img_file)
        pix = im.load()
        print(im.size)
        print(pix[10,10])
        avg_brightness_calculator(pix, im.size[0], im.size[1])