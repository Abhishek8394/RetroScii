# RetroScii

Miss the good old days of ASCII art? I for one certainly do. This project converts an image into ASCII art.

## Setup

### Environment setup
Make sure you have all the dependencies installed, using a `virtualenv` is recommended, since this project uses [Python Pillow](https://python-pillow.org/)
library and people have reported issues with its installation.

With all that setup, run the following command:

    pip install -r requirements.txt
    
### Data Setup

A `TTF` font file is required to generate the initial data. Monospace fonts are preferred, tested with `Courier New`.
You can easily find this in your OS's fonts directory or use any font(let us know if you get cool results!).

## Usage

If you are on windows, run the following command to set the encoding of the terminal, the preferred setting is "latin-1" (because 128 chars weren't enough)

     chcp 1252

Running the following command for help:

    python src/main.py --help
 
1. If you already have a `tables` available with you, convert any image into ASCII art with this command or use the default one provided:

        python src\main.py --convert --table-path table.txt --img image/to/convert


Use the following command for making your own table from a font file:

    python src\main.py --font2table --font-file path/to/ttf --bitmap-out-dir path/to/output/dir --table-out path/table.txt

## Contributing

Fork, pull request, wait, repeat!
