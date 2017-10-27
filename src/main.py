#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
import os
import argparse
import converter as Converter
import tablegen as TableGenerator

if __name__ == "__main__":
    """Quick testing of script in dev
    """
    parser = argparse.ArgumentParser()
    # modes of running the script
    parser.add_argument("--convert", help="Create ASCII art from image", action="store_true")
    parser.add_argument("--font2table", help="Generate table from a font file", action="store_true")
    parser.add_argument("--font2img", help="Generate images from a font file", action="store_true")
    parser.add_argument("--img2table", help="Generate table from images", action="store_true")

    # encoding options
    parser.add_argument("--use-latin-1", help="Use latin-1 encoding.", action="store_true")

    # params for ASCII art generation
    parser.add_argument("--img", help="Image to convert", default=None)
    parser.add_argument("--table-path", help="table to use", default=os.path.join("tables", "tables.txt"))
    parser.add_argument("--op-size", help="output size of ASCII art, more the number, bigger it will be", type=int, default=7)

    # params for table generation
    parser.add_argument("--font-file", help="Font file", default=None)
    parser.add_argument("--font-size", help="Font size in pt", default=20, type=int)
    parser.add_argument("--bitmap-size", help="Size of font bitmap", default=20, type=int)
    parser.add_argument("--bitmap-out-dir", help="output directory for writing font bitmaps", default="font-bitmaps")
    parser.add_argument("--data-dir", help="directory containing character image files")
    parser.add_argument("--ext", help="Extension of character image files", default="png")
    parser.add_argument("--table-out", help="table output file", default="table.txt")
    parser.add_argument("--no-optimization", help="dont use scaling optimization, -_-", action="store_true")
    

    args = parser.parse_args()
    
    if args.convert:
        img_file = args.img
        table_path = args.table_path
        op_size = args.op_size
        if img_file == None or table_path == None or op_size < 1:
            print("Please provide valid args")
            exit(-1)
        Converter.convert_and_print(img_file, table_path, op_size)

    else:
        font_file = args.font_file
        font_size = args.font_size
        img_dimensions = args.bitmap_size
        bitmap_out_dir = args.bitmap_out_dir
        out_file = args.table_out
        extension = args.ext
        scaling_optimization = not args.no_optimization
        use_latin_1 = args.use_latin_1
        if args.font2table:
            # font to table
            TableGenerator.table_from_font(font_file, 
                                           font_size, 
                                           img_dimensions, 
                                           bitmap_out_dir, 
                                           out_file, 
                                           extension=extension,
                                           scaling_optimization=scaling_optimization,
                                           use_latin_1=use_latin_1)

        elif args.font2img:
            TableGenerator.generate_images_for_charset(font_file, 
                                                       font_size, 
                                                       img_dimensions, 
                                                       bitmap_out_dir,
                                                       use_latin_1=use_latin_1
                                                       )
        elif args.img2table:
            TableGenerator.generate_table(bitmap_out_dir, out_file, extension=extension, scaling_optimization=scaling_optimization) 

        else:
            parser.print_help()
            exit(-1)