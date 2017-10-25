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

The current script is a mess and will be cleaned in later updates. But running the following command should help:

    python src/converter.py --help
 
Following steps are necessary to get started:

1. Generate character bitmaps from font file. Current command (maybe outdated):

        python src/converter.py --font-path path/to/tff --bitmap-out-dir output_dir

2. Generate the table from these images. Current command (maybe outdated):

        python src/converter.py --data-dir path/to/bitmap/output/dir 

## Contributing

Fork, pull request, wait, repeat!
