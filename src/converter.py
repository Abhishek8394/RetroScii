#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
import os
from PIL import Image, ImageDraw, ImageFont
import json
from math import ceil
import constants as Constants
from tablegen import avg_brightness_calculator

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
    chr_width, chr_height = table_obj[Constants.META_KEY][Constants.IMAGE_WIDTH_KEY], table_obj[Constants.META_KEY][Constants.IMAGE_HEIGHT_KEY]
    chr_width = ceil(chr_width / op_size)
    chr_height = ceil(chr_height / op_size)
    # do the conversion and print it
    result = img2Ascii(pixels, table_obj[Constants.TABLE_KEY], w, h, chr_width, chr_height)
    for i in result:
        print("".join(i))