import os
import io
import re
import sys
import pdb
import pygame
import subprocess
from PIL import Image
from os.path import join
import RPi.GPIO as GPIO
from picamera import PiCamera
from buttons import GPIOButton
from timeit import default_timer as timer
from api_requests import ImageToSpeechRequest
GPIO.setmode(GPIO.BCM)  # TODO: Run this when button is created

TAKE_PHOTO_PIN = 17
WINDOW_SIZE = (320,240)
FULL_IMAGE_SIZE = WINDOW_SIZE
WAIT_AFTER_PHOTO = 3
IMG_DIR = 'photos'
AUDIO_FREQUENCY = 12000 #TODO figure out correct setting for this
REQUEST_URL = 'https://seeing-eye-pi.azure-api.net/ImageToSpeechV1/HttpTrigger'
# 12000 sounds good on my computer but I have to increase it to sound correct on the Raspberry Pi


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

# TODO Create functions or classes for main application routines (viewfinder, taking photo, etc...)
# TODO log errors from api calls, add exception handling
# TODO use azure text to speech while we're at it
# TODO refactor into single class
# TODO refresh speech access token after some set amount of time. Token expires after 10 min https://docs.microsoft.com/azure/cognitive-services/authentication#authenticate-with-an-authentication-token
# token refresh takes around 1 to 1.5 seconds so we don't want to do it after every photo

# MAIN PROGRAM -------------------------------------------------
image_to_speech = ImageToSpeechRequest(url=REQUEST_URL)
pygame.mixer.pre_init(frequency=AUDIO_FREQUENCY) 
pygame.init()
screen = pygame.display.set_mode(WINDOW_SIZE)
rgb = bytearray(WINDOW_SIZE[0] * WINDOW_SIZE[1] * 3)
camera = PiCamera()
take_photo_button = GPIOButton(TAKE_PHOTO_PIN)
start = timer()


while timer() - start < 10:
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
    if take_photo_button.is_pressed():
        stream = io.BytesIO()
        camera.capture(stream, use_video_port=False, resize=FULL_IMAGE_SIZE, format='jpeg')
        stream.seek(0)
        image_bytes = stream.read()
        # TODO: take image full size
        audio = image_to_speech.post_request(image_bytes)
        # TODO: pause until audio is done playing
        pygame.mixer.Sound(audio).play()
        save_img_and_caption(stream, 'foo')
