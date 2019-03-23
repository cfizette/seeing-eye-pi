import os
from os.path import join
import re
from picamera import PiCamera
from time import sleep
from timeit import default_timer as timer
import pygame
import io
import pdb
from PIL import Image
import numpy as np
import subprocess

WINDOW_SIZE = (320,240)
NN_INPUT_SIZE = (320,240)
WAIT_AFTER_PHOTO = 3
IMG_DIR = 'photos'


# Check that the directory is made and find max image
if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)
FILE_NUM = 1
for filename in os.listdir(IMG_DIR):
    n = int(re.split('[_.]', filename)[1])
    if n > FILE_NUM:
        FILE_NUM = n+1


def button_pressed():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                return True
    return False


def speak_caption(caption):
    print(caption)
    subprocess.call(['espeak', "'{}'".format(caption), '2>/dev/null'])


def generate_caption(img):
    # TODO may need to convert image before putting into model, maybe not, rgb should work
    return "I see a big puppy"


def save_img_and_caption(img, caption):
    global FILE_NUM
    # pass the pygame image here
    image_filename = 'IMG_{}.jpg'.format(FILE_NUM)
    caption_filename = 'IMG_{}.txt'.format(FILE_NUM)
    im = Image.fromarray(img)
    im.save(join(IMG_DIR, image_filename))

    # pygame.image.save(img, join(IMG_DIR, image_filename))
    with open(join(IMG_DIR, caption_filename), 'w') as f:
        f.write(caption)
    # Increment file number
    FILE_NUM += 1


# MAIN PROGRAM -------------------------------------------------
pygame.init()
screen = pygame.display.set_mode(WINDOW_SIZE)
rgb = bytearray(WINDOW_SIZE[0] * WINDOW_SIZE[1] * 3)
camera = PiCamera()
start = timer()

while timer() - start < 20:
    # Byte array to hold image
    stream = io.BytesIO()

    # Capture image to byte array
    camera.capture(stream, use_video_port=True, resize=WINDOW_SIZE, format='rgb')
    stream.seek(0)
    stream.readinto(rgb)

    # Convert to pygame image
    img = pygame.image.frombuffer(rgb[0:(WINDOW_SIZE[0] * WINDOW_SIZE[1] * 3)], WINDOW_SIZE, 'RGB')

    # Display image on pygame screen
    if img is None or img.get_height() < WINDOW_SIZE[1]: # Letterbox, clear background
        screen.fill(0)
    if img:
        screen.blit(img, ((WINDOW_SIZE[0] - img.get_width() ) / 2, (WINDOW_SIZE[1] - img.get_height()) / 2))
    pygame.display.update()

    # Check if button pressed and perform appropriate actions if it is
    if button_pressed():
        # Currently saved image is limited by screen resolution, may eventually want to 
        # dump full res picture into disk, resize in memory, and send to neural net
        # Order of these operations depends on memory limitations. Not sure how much NN needs
        stream = io.BytesIO()
        camera.capture(stream, use_video_port=False, resize=WINDOW_SIZE, format='rgb')
        stream.seek(0)
        stream.readinto(rgb)
        # img = pygame.image.frombuffer(rgb[0:(WINDOW_SIZE[0] * WINDOW_SIZE[1] * 3)], WINDOW_SIZE, 'RGB')
        # np_img = pygame.surfarray.array3d(img)
        np_img = np.frombuffer(rgb, dtype=np.uint8).reshape((WINDOW_SIZE[1], WINDOW_SIZE[0], 3))

        caption = generate_caption(np_img) # probably need to somehow convert to numpy array or tensor
        speak_caption(caption)
        save_img_and_caption(np_img, caption)


