#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
import os
from PIL import Image, ImageDraw, ImageFont
import argparse
import json
from math import ceil

# meta data keys
I2FILE_KEY = "i2file"
FILE2I_KEY = "file2i"

# result table keys
TABLE_KEY = "table"
STATS_KEY = "stats"
MIN_VAL_KEY = "min_brightness"
MAX_VAL_KEY = "max_brightness"
DATA_FOLDER_KEY = "src_data_folder"
META_KEY = "meta"
IMAGE_WIDTH_KEY = "char_width"
IMAGE_HEIGHT_KEY = "char_height"

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
    meta_data[I2FILE_KEY] = i2file
    meta_data[FILE2I_KEY] = file2i
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
    
    if FILE2I_KEY not in meta_data or I2FILE_KEY not in meta_data:
        raise Exception("Did not find \"{}\" or  \"{}\" in meta_data".format(FILE2I_KEY, I2FILE_KEY))
    result={}
    hashtable = {}
    minval = None
    maxval = None
    w,h = None, None
    print("Generating table")
    for i in images:
        ascii_code = meta_data[FILE2I_KEY][i]
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

    result[TABLE_KEY] = scaled_hashtable
    result[STATS_KEY] = {}
    # keeping the original min and max vals in case it is required to reverse the op.
    result[STATS_KEY][MIN_VAL_KEY] = minval
    result[STATS_KEY][MAX_VAL_KEY] = maxval
    result[META_KEY] = {}
    result[META_KEY][DATA_FOLDER_KEY] = images_folder
    result[META_KEY][IMAGE_WIDTH_KEY], result[META_KEY][IMAGE_HEIGHT_KEY] = w, h

    print("writing table to:",out_file)    
    with open(out_file, "w") as f:
        f.write(json.dumps(result, indent=2))
        f.write("\n")
    print("done")

def get_closest_chr_code(table, search_val):
    idx = None
    code = None
    search_val = float(search_val)
    for i in table:
        curr_value = float(i)
        if idx==None or abs(curr_value - search_val) < abs(idx - search_val):
            idx = curr_value
            code = table[i]
    return int(code)


def img2Ascii(pixels, table, img_width, img_height, chr_width, chr_height, op_width=None, op_height=None):
    """Convert an image into ASCII art.
    
    Args:
        pixels (pixel[][]): Image that is to be converted.
        table (dict): A table to lookup ascii characters based on brightness
        img_width (int): width of input image in pixels
        img_height (int): height of input image in pixels
        chr_width (int): chr width pixels
        chr_height (int): chr height pixels
        op_width (int): output width in number of columns
        op_height (int): output height in number of rows
    
    Returns:
        str[][]: The matrix of ascii chars
    """
    result_width = max(img_width // chr_width, 1)
    result_height = max(img_height // chr_height, 1)
    result=[]
    # print("Input is {}x{} px and each char is {}x{} px".format(img_width, img_height, chr_width, chr_height))
    # print("output will be {}x{}".format(result_width, result_height))
    for i in range(result_height):
        tmp=[]
        for j in range(result_width):
            # Theory:
            # row_st must be according to i and col_st must be according to j if we consider pixels a matrix.
            # But the way PIL.PixelAccess works is (i,j) returns (width+i, height+j)
            row_st = j * chr_height
            col_st = i * chr_width
            img_patch_brightness = avg_brightness_calculator(pixels, chr_width, chr_height, row_st, col_st)
            closest = get_closest_chr_code(table, img_patch_brightness)
            tmp.append(chr(closest).encode("latin-1").decode("latin-1"))
        result.append(tmp)
    return result

def convert_and_print(img_file, table_path, op_size):
    """Convert image file into ASCII art and print it.
    
    Args:
        img_file (str): path to image file.
        table_path (str): path to the stat table.
        op_size (int): Output scaling. It works as follows; 
                        - The number of columns will be (img_width (px) * op_size) / character_width (px)
                        - The number of rows will be calculated similarly using heights.
                        Hence more the op_size, the bigger the image will be
    """ 
    
    # load up the table and the image
    table_obj = {}
    with open(table_path,"r") as f:
        try:
            table_obj = json.load(f)
        except ValueError:
            print("problem parsing table JSON, aborting...")
            return
    image = Image.open(img_file)
    w,h = image.size
    pixels = image.load()

    # Calculate character widths after scaling
    chr_width, chr_height = table_obj[META_KEY][IMAGE_WIDTH_KEY], table_obj[META_KEY][IMAGE_HEIGHT_KEY]
    chr_width = ceil(chr_width / op_size)
    chr_height = ceil(chr_height / op_size)
    # do the conversion and print it
    result = img2Ascii(pixels, table_obj[TABLE_KEY], w, h, chr_width, chr_height)
    for i in result:
        print("".join(i))


if __name__ == "__main__":
    """Quick testing of script in dev
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--img", help="Image file to convert", default=None)
    parser.add_argument("--font-path", help="Font file", default=None)
    parser.add_argument("--font-size", help="Font size in pt", default=20, type=int)
    parser.add_argument("--bitmap-size", help="Size of font bitmap", default=20, type=int)
    parser.add_argument("--bitmap-out-dir", help="output directory for writing font bitmaps", default="font-bitmaps")
    parser.add_argument("--data-dir", help="directory containing character image files")
    parser.add_argument("--ext", help="Extension of character image files", default="png")
    parser.add_argument("--table-out", help="table output file", default="table.txt")
    parser.add_argument("--no-optimization", help="dont use scaling optimization, -_-", action="store_true")
    parser.add_argument("--convert-img", help="image to convert", default=None)
    parser.add_argument("--table-path", help="table to use", default=None)
    parser.add_argument("--output-size", help="output size of ASCII art, more the number, bigger it will be", type=int, default=7)

    args = parser.parse_args()

    img_file = args.img
    font_file = args.font_path
    font_size = args.font_size
    img_dimensions = args.bitmap_size
    bitmap_out_dir = os.path.abspath(args.bitmap_out_dir)
    data_dir = args.data_dir
    ext = args.ext
    table_out = args.table_out
    scaling_optimization = not args.no_optimization
    convert_img = args.convert_img
    table_path = args.table_path
    output_size = args.output_size

    if convert_img!=None and table_path!=None:
        convert_and_print(convert_img, table_path, output_size)


    if not os.path.exists(bitmap_out_dir):
        os.makedirs(bitmap_out_dir)

    if data_dir:
        data_dir = os.path.abspath(data_dir)
        generate_table(data_dir, table_out, extension=ext, precision=4, scaling_optimization=scaling_optimization) 

    elif font_file:
        generate_images_for_charset(font_file, font_size, img_dimensions, bitmap_out_dir)
    elif img_file:
        im = Image.open(img_file)
        pix = im.load()
        print(im.size)
        print(pix[10,10])
        print(avg_brightness_calculator(pix, im.size[0], im.size[1]))