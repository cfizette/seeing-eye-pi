# Loads existing image instead of using the camera to take a photo

import os
import io
import re
import sys
import pdb
import pygame
import time
import subprocess
from PIL import Image
from os.path import join
import RPi.GPIO as GPIO
from picamera import PiCamera
from buttons import GPIOButton
from timeit import default_timer as timer
from api_requests import ImageToSpeechRequest

TAKE_PHOTO_PIN = 17
QUIT_PIN = 27
WINDOW_SIZE = (640,480)
FULL_IMAGE_SIZE = WINDOW_SIZE
RGB_DATA_SIZE = WINDOW_SIZE[0] * WINDOW_SIZE[1] * 3  
WAIT_AFTER_PHOTO = 3
IMG_DIR = 'photos'
AUDIO_FREQUENCY = 12000 #TODO figure out correct setting for this
REQUEST_URL = 'https://seeing-eye-pi.azure-api.net/ImageToSpeechV1NorthCentralUS/HttpTrigger'
SHUTTER_EFFECT_PATH = 'assets/camera-shutter.ogg'
# 12000 sounds good on my computer but I have to increase it to sound correct on the Raspberry Pi


class CameraAppFilesystem:
    """
    Handles saving images and their captions.
    Saves images as IMG_N.jpg
    Saves captions as IMG_N.txt
    """
    def __init__(self, img_dir=IMG_DIR):
        self.img_dir = img_dir
        self.file_num = 1
        self.init_filesystem()

    def init_filesystem(self):
        # Create directory and set file number higher than existing ones
        if not os.path.exists(self.img_dir):
            os.makedirs(self.img_dir)
        for filename in os.listdir(self.img_dir):
            n = int(re.split('[_.]', filename)[1])
            if n >= self.file_num:
                self.file_num = n+1

    def save_img_and_caption(self, stream, caption):
        image_filename = 'IMG_{}.jpg'.format(self.file_num)
        caption_filename = 'IMG_{}.txt'.format(self.file_num)
        im = Image.open(stream)
        im.save(join(self.img_dir, image_filename))
        with open(join(self.img_dir, caption_filename), 'w') as f:
            f.write(caption)
        self.file_num += 1


class CameraApp:
    def __init__(self, **kwargs):
        # For now just use globals to initialize attributes
        self.image_to_speech = ImageToSpeechRequest(url=REQUEST_URL)
        self.rgb = bytearray(RGB_DATA_SIZE)
        self.filesystem = CameraAppFilesystem()
        self.shutter_effect = pygame.mixer.Sound(SHUTTER_EFFECT_PATH)
        # Setup button interrupts
        self.setup_interrupt_button(TAKE_PHOTO_PIN, self.capture_and_process_image)
        self.setup_interrupt_button(QUIT_PIN, self.quit)

    def setup_interrupt_button(self, pin, callback):
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(pin, GPIO.FALLING, callback, 50)

    def capture_photo_to_stream(self, use_video_port, resize, img_format):
        stream = io.BytesIO()
        self.camera.capture(stream, use_video_port=use_video_port, resize=resize, format=img_format)
        stream.seek(0)
        return stream

    def play_pygame_sound(self, sound):
        channel = sound.play()
        # Need to pause to allow sound to be played
        while channel.get_busy():
            pygame.time.delay(10)

    def capture_and_process_image(self, pin=None):
        # Load existing image and process it
        print('Loading image')
        self.play_pygame_sound(self.shutter_effect)
        with open('assets/cat.jpg', 'rb') as f:
            image_bytes = f.read()
        print('Sending photo to Azure')
        caption, audio = self.image_to_speech.post_request(image_bytes)
        print(caption)
        print("Received audio")
        print('Playing audio')
        sound = pygame.mixer.Sound(audio)
        self.play_pygame_sound(sound)
        print("Saving data")
        # self.filesystem.save_img_and_caption(stream, 'foo')  # TODO add caption here
    
    def quit(self, pin=None):
        pygame.quit()
        sys.exit

    def run(self):
        while True:
            pass


if __name__ == "__main__":
    print('hi')
    pygame.mixer.pre_init(frequency=AUDIO_FREQUENCY) 
    pygame.init()
    app = CameraApp()
    app.run()
        