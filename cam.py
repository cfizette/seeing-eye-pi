import os
import sys
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
from azure_helpers import AzureCaptioner, TmpSpeaker

WINDOW_SIZE = (320,240)
FULL_IMAGE_SIZE = WINDOW_SIZE
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


def save_img_and_caption(stream, caption, width=FULL_IMAGE_SIZE[1], height=FULL_IMAGE_SIZE[0]):
    global FILE_NUM
    image_filename = 'IMG_{}.jpg'.format(FILE_NUM)
    caption_filename = 'IMG_{}.txt'.format(FILE_NUM)
    im = Image.open(stream)
    im.save(join(IMG_DIR, image_filename))
    with open(join(IMG_DIR, caption_filename), 'w') as f:
        f.write(caption)
    # Increment file number
    FILE_NUM += 1

# TODO log errors from api calls, add exception handling
# TODO use azure text to speech while we're at it
# TODO refactor into single class

# MAIN PROGRAM -------------------------------------------------
captioner = AzureCaptioner()
tts = TmpSpeaker()
pygame.init()
screen = pygame.display.set_mode(WINDOW_SIZE)
rgb = bytearray(WINDOW_SIZE[0] * WINDOW_SIZE[1] * 3)
camera = PiCamera()
start = timer()


while timer() - start < 30:
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
        stream = io.BytesIO()
        camera.capture(stream, use_video_port=False, resize=FULL_IMAGE_SIZE, format='jpeg')
        stream.seek(0)
        # TODO: take image full size
        caption = captioner.generate_caption(stream) # probably need to somehow convert to numpy array or tensor
        tts.speak(caption)
        save_img_and_caption(stream, caption)
