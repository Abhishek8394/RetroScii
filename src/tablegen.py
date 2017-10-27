#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
import os
from PIL import Image, ImageDraw, ImageFont
import json
from math import ceil
import constants as Constants

def generate_char_image(font_file, chr_code, font_size, img_dimensions, bitmap_out_dir, should_save=True):
    """Generate a png image for a character.
    
    Args:
        font_file (string): Location of TTF of font to use
        chr_code (int): Integer code of character
        font_size (int): Font size in pts
        img_dimensions (int): Image will be a square of this size.
        bitmap_out_dir (string): Output directory
        should_save (bool): Save Image to file if this is True

    Returns:
        (PIL.Image, string) : Image created along with its save file name
    """
    # use latin-1 encoding to support some "extended ascii"
    chr_symbol = chr(chr_code).encode("latin-1").decode("latin-1")
    image = Image.new("RGB", (img_dimensions,img_dimensions), (0,0,0)) #can do rgba too but not needed
    font = ImageFont.truetype(font_file, font_size)
    draw = ImageDraw.Draw(image)
    draw.text((5, 0), chr_symbol, (255,255,255), font=font)
    # to make image crisper
    img_resized = image.resize((img_dimensions//2,img_dimensions//2))
    save_file_name = "_".join(["ascii",str(chr_code),str(font_size)]) + ".png"
    save_path = os.path.join(bitmap_out_dir, save_file_name)
    if should_save:
        image.save(save_path)
    return image, save_file_name

def generate_images_for_charset(font_file, font_size, img_dimensions, bitmap_out_dir, meta_file_name="meta.txt"):
    """Generate images for a charset with font and size settings.
    
    Args:
        font_file (string): Location of TTF of font to use
        font_size (int): Font size in pts
        img_dimensions (int): Image will be a square of this size.
        bitmap_out_dir (string): Output directory
        meta_file_name (string) : filename, not the path; of the meta data file.
    """
    # entire displayable ascii set
    meta_data={}
    i2file = {}
    file2i = {}
    if not os.path.exists(bitmap_out_dir):
        os.makedirs(bitmap_out_dir)
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
        _, save_path = generate_char_image(font_file, i, font_size, img_dimensions, bitmap_out_dir)
        i2file[i] = save_path
        file2i[save_path] = i
    print("\ndone generating images.")
    meta_file_name = os.path.join(bitmap_out_dir, meta_file_name)
    print("Writing meta_data to",meta_file_name)
    meta_data[Constants.I2FILE_KEY] = i2file
    meta_data[Constants.FILE2I_KEY] = file2i
    with open(meta_file_name, "w") as f:
        f.write(json.dumps(meta_data, indent=2))
        f.write("\n")
    print("done")


def avg_brightness_pixel(pixel):
    """ Calculate the average brightness of a pixel.
    
    Args:
        pixel (tuple) : Tuple containing pixel densities, must be length 3 (RGB) or 4(RGBA)
    
    Returns:
        float: average brightness of a pixel
    
    Raises:
        Exception: If not a RGB or RGBA pixel
    """
    # 8-bit pixel.
    if type(pixel) == int:
        return pixel
    # rgb
    if len(pixel) == 3:
        return sum(pixel) / len(pixel)
    elif len(pixel) == 4:
        # TODO: verify correctness
        # rgba pixel, multiply with intensity. Not sure if correct. 
        return sum(pixel[:-1])/3 + pixel[-1]/255
    raise Exception("provide a RGB or RGBA tuple")

def avg_brightness_calculator(pix, w, h, row_st=0, col_st=0):
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
    for i in range(row_st, row_st + h):
        for j in range(col_st, col_st + w):
            # print(i,j)
            brightness_avg += avg_brightness_pixel(pix[i,j]) / img_size
    # print("---")
    return brightness_avg

def get_images_filenames(images_folder, extension):
    """Get all relevant images from the folder
    
    Args:
        images_folder (str): Folder to search in. Does not search recursively
        extension (str): file extension to look for
    
    Returns:
        list(str) : List of file names (not paths) of relevant files
    """
    result = []
    extension = extension.lower()
    for i in os.listdir(images_folder):
        curr = os.path.join(images_folder,i)
        if os.path.isfile(curr):
            f_ext = i.split(".")[-1]
            if f_ext.lower() == extension:
                result.append(i)
    return result

def generate_table(images_folder, out_file, extension="png", precision=4, meta_file_name="meta.txt", scaling_optimization=True):
    """Generate the brightness table used in conversion. 
       TODO: Maybe create a K-D tree
    
    Args:
        images_folder (str): Folder to search for images
        out_file (str): Output file to write the table in
        extension (str, optional): Extension of files to process
        precision (int, optional): Floating point precision to be kept
        meta_file_name (str, optional): name of meta data file in images folder
        scaling_optimization (bool, optional): Perform the scaling optimization during table generation.
    
    Raises:
        Exception: Invalid meta data object
    """
    images = get_images_filenames(images_folder, extension)
    meta_data = {}
    with open(os.path.join(images_folder,meta_file_name),"r") as f:
        meta_data = json.load(f)
    
    if Constants.FILE2I_KEY not in meta_data or Constants.I2FILE_KEY not in meta_data:
        raise Exception("Did not find \"{}\" or  \"{}\" in meta_data".format(Constants.FILE2I_KEY, Constants.I2FILE_KEY))
    result={}
    hashtable = {}
    minval = None
    maxval = None
    w,h = None, None
    print("Generating table")
    for i in images:
        ascii_code = meta_data[Constants.FILE2I_KEY][i]
        img_file = os.path.abspath(os.path.join(images_folder, i))
        img = Image.open(img_file)
        w,h = img.size
        pix = img.load()
        avg_brightness = avg_brightness_calculator(pix,w,h)
        avg_brightness = round(avg_brightness, precision)
        if avg_brightness in hashtable:
            print("hash collision: ",hashtable[avg_brightness],ascii_code)
        else:
            hashtable[avg_brightness] = ascii_code
            minval = avg_brightness if minval==None else min(minval, avg_brightness)
            maxval = avg_brightness if maxval==None else max(maxval, avg_brightness)
    
    # TODO: handle None values.
    scaled_hashtable = {}
    if scaling_optimization:
        for i in hashtable:
            scaled_avg_brightness = 255 * (i - minval) / (maxval-minval)
            scaled_hashtable[scaled_avg_brightness] = hashtable[i]
    else:
        scaled_hashtable = hashtable

    result[Constants.TABLE_KEY] = scaled_hashtable
    result[Constants.STATS_KEY] = {}
    # keeping the original min and max vals in case it is required to reverse the op.
    result[Constants.STATS_KEY][Constants.MIN_VAL_KEY] = minval
    result[Constants.STATS_KEY][Constants.MAX_VAL_KEY] = maxval
    result[Constants.META_KEY] = {}
    result[Constants.META_KEY][Constants.DATA_FOLDER_KEY] = images_folder
    result[Constants.META_KEY][Constants.IMAGE_WIDTH_KEY], result[Constants.META_KEY][Constants.IMAGE_HEIGHT_KEY] = w, h

    print("writing table to:",out_file)    
    with open(out_file, "w") as f:
        f.write(json.dumps(result, indent=2))
        f.write("\n")
    print("done")


def table_from_font(font_file, font_size, img_dimensions, bitmap_out_dir, out_file, extension="png", precision=4, meta_file_name="meta.txt", scaling_optimization=True):
    """Create the stats table from the font file. Wrapper for the entire process.
    
    Args:
        font_file (str): Path to font file, must be TTF file.
        font_size (int): font size to use for bitmap generation
        img_dimensions (int): image size of generated bitmaps, usually size of a character in terminal (pixels)
        bitmap_out_dir (str): Directory in which to store the generated bitmaps
        out_file (str): file in which to store the table
        extension (str, optional): Extension of bitmap files created in the process
        precision (int, optional): floating point precision to use in calculations
        meta_file_name (str, optional): Name of meta data file created in the process
        scaling_optimization (bool, optional): allow use of scaling optimization
    """
    if not os.path.exists(bitmap_out_dir):
        os.makedirs(bitmap_out_dir)
    generate_images_for_charset(font_file, font_size, img_dimensions, bitmap_out_dir, meta_file_name=meta_file_name)
    generate_table(bitmap_out_dir, out_file, extension=extension, precision=precision, meta_file_name=meta_file_name, scaling_optimization=scaling_optimization) 