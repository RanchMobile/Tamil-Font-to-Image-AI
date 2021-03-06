#!/usr/bin/env python
import argparse
import glob
import io
import os
import random
import shutil
import numpy
from PIL import Image, ImageFont, ImageDraw
from scipy.ndimage.interpolation import map_coordinates
from scipy.ndimage.filters import gaussian_filter


SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

# Width and height of the resulting image.
IMAGE_WIDTH = 160
IMAGE_HEIGHT = 160

# Number of random distortion images to generate per font and character.
DISTORTION_COUNT = 25

# Default data paths.
DEFAULT_LABEL_FILE = os.path.join(SCRIPT_PATH,
                                  'labels/tamil_small.txt')
DEFAULT_FONTS_DIR = os.path.join(SCRIPT_PATH, 'fonts/unicode/one')
DEFAULT_OUTPUT_DIR = os.path.join(SCRIPT_PATH, 'image-data/'+ str(IMAGE_WIDTH) + 'x' + str(IMAGE_HEIGHT) + '/')


def generate_tamil_images(label_file, fonts_dir, output_dir):
    """Generate tamil image files.

    This will take in the passed in labels file and will generate several
    images using the font files provided in the font directory. The font
    directory is expected to be populated with *.ttf (True Type Font) files.
    The generated images will be stored in the given output directory. Image
    paths will have their corresponding labels listed in a CSV file.
    """
    with io.open(label_file, 'r', encoding='utf-8') as f:
        labels = f.read().splitlines()

    image_dir = os.path.join(output_dir, 'images')
    if not os.path.exists(image_dir):
        os.makedirs(os.path.join(image_dir))

    # Get a list of the fonts.
    fonts = glob.glob(os.path.join(fonts_dir, '*.ttf'))

    labels_csv = io.open(os.path.join(output_dir, 'labels-map.csv'), 'w',
                         encoding='utf-8')

    total_count = 0
    prev_count = 0
    folder_count = 0
    for character in labels:
        folder_count += 1
        #print('%s: %d',character,len(character))
        # Print image count roughly every 5000 images.
        if total_count - prev_count > 5000:
            prev_count = total_count
            print('{} images generated...'.format(total_count))
        mychar = character
        for font in fonts:
            total_count += 1
            image = Image.new('L', (IMAGE_WIDTH, IMAGE_HEIGHT), color='white')
            font = ImageFont.truetype(font, int(80/len(mychar)))
            drawing = ImageDraw.Draw(image)
            w, h = drawing.textsize(mychar, font=font)
            drawing.text(
                ((IMAGE_WIDTH-w)/2, (IMAGE_HEIGHT-h)/2),
                mychar,
                fill=(0),
                font=font
            )
            file_string = '{}_{}.jpg'.format(mychar, total_count)
            #file_path = os.path.join(image_dir, 'f'+str(folder_count))
            file_path = os.path.join(image_dir, file_string)
            orgFile = file_path
            image.save(file_path)
            

            #directory creation
            mvDir = os.path.join(image_dir, mychar + '_' + str(folder_count))
            if not os.path.exists(mvDir):
                os.makedirs(mvDir)
            
            for i in range(DISTORTION_COUNT):
                total_count += 1
                dist_string = '{}_{}.jpg'.format(mychar, total_count)
                #file_path = os.path.join(image_dir, 'f'+str(folder_count))
                file_path = os.path.join(image_dir, dist_string)
                arr = numpy.array(image)

                distorted_array = elastic_distort(
                    arr, alpha=random.randint(30, 36),
                    sigma=random.randint(5, 6)
                )
                distorted_image = Image.fromarray(distorted_array)
                distorted_image.save(file_path)
                img = Image.open(file_path)
                dr = ImageDraw.Draw(img)
                cor = (0,0, IMAGE_WIDTH,IMAGE_HEIGHT)
                dr.rectangle(cor, outline="white", width=5)
                img.save(file_path)
                distLoc = os.path.join(mvDir, dist_string)
                shutil.move(file_path, distLoc)
                labels_csv.write(u'{},{}\n'.format(mychar, distLoc))
            origLoc = os.path.join(mvDir, file_string)
            newPath = os.path.join(mvDir, origLoc)
            shutil.move(orgFile, newPath)
            labels_csv.write(u'{},{}\n'.format(mychar, newPath))
            
    print('Finished generating {} images.'.format(total_count))
    labels_csv.close()


def elastic_distort(image, alpha, sigma):
    """Perform elastic distortion on an image.

    Here, alpha refers to the scaling factor that controls the intensity of the
    deformation. The sigma variable refers to the Gaussian filter standard
    deviation.
    """
    random_state = numpy.random.RandomState(None)
    shape = image.shape

    dx = gaussian_filter(
        (random_state.rand(*shape) * 2 - 1),
        sigma, mode="constant"
    ) * alpha
    dy = gaussian_filter(
        (random_state.rand(*shape) * 2 - 1),
        sigma, mode="constant"
    ) * alpha

    x, y = numpy.meshgrid(numpy.arange(shape[0]), numpy.arange(shape[1]))
    indices = numpy.reshape(y+dy, (-1, 1)), numpy.reshape(x+dx, (-1, 1))
    return map_coordinates(image, indices, order=1).reshape(shape)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--label-file', type=str, dest='label_file',
                        default=DEFAULT_LABEL_FILE,
                        help='File containing newline delimited labels.')
    parser.add_argument('--font-dir', type=str, dest='fonts_dir',
                        default=DEFAULT_FONTS_DIR,
                        help='Directory of ttf fonts to use.')
    parser.add_argument('--output-dir', type=str, dest='output_dir',
                        default=DEFAULT_OUTPUT_DIR,
                        help='Output directory to store generated images and '
                             'label CSV file.')
    args = parser.parse_args()
    generate_tamil_images(args.label_file, args.fonts_dir, args.output_dir)
