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
WINDOW_SIZE = (320,240)
FULL_IMAGE_SIZE = WINDOW_SIZE
RGB_DATA_SIZE = WINDOW_SIZE[0] * WINDOW_SIZE[1] * 3  
WAIT_AFTER_PHOTO = 3
IMG_DIR = 'photos'
AUDIO_FREQUENCY = 12000 #TODO figure out correct setting for this
REQUEST_URL = 'https://seeing-eye-pi.azure-api.net/ImageToSpeechV1/HttpTrigger'
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
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.camera = PiCamera()
        self.filesystem = CameraAppFilesystem()
        self.take_photo_button = GPIOButton(TAKE_PHOTO_PIN)
        self.quit_button = GPIOButton(QUIT_PIN)
        self.shutter_effect = pygame.mixer.Sound(SHUTTER_EFFECT_PATH)

    def show_viewfinder(self):
        stream = self.capture_photo_to_stream(use_video_port=True, resize=WINDOW_SIZE, img_format='rgb')
        stream.readinto(self.rgb)
        # Convert to pygame image
        img = pygame.image.frombuffer(self.rgb[0:(RGB_DATA_SIZE)], WINDOW_SIZE, 'RGB')
        # Display image on pygame screen
        if img is None or img.get_height() < WINDOW_SIZE[1]: # Letterbox, clear background
            self.screen.fill(0)
        if img:
            self.screen.blit(img, ((WINDOW_SIZE[0] - img.get_width() ) / 2, (WINDOW_SIZE[1] - img.get_height()) / 2))
        pygame.display.update()

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

    def capture_and_process_image(self):
        print('Taking photo in capture_and_process_image')
        self.play_pygame_sound(self.shutter_effect)
        stream = self.capture_photo_to_stream(use_video_port=False, resize=FULL_IMAGE_SIZE, img_format='jpeg')
        image_bytes = stream.read()
        print('Sending photo to Azure')
        audio = self.image_to_speech.post_request(image_bytes)
        print("Received audio")
        print('Playing audio')
        sound = pygame.mixer.Sound(audio)
        self.play_pygame_sound(sound)
        print("Saving data")
        self.filesystem.save_img_and_caption(stream, 'foo')  # TODO add caption here

    def run(self):
        while True:
            self.show_viewfinder()
            if self.take_photo_button.is_pressed():
                self.capture_and_process_image()
            if self.quit_button.is_pressed():
                pygame.quit()
                sys.exit()

if __name__ == "__main__":
    pygame.mixer.pre_init(frequency=AUDIO_FREQUENCY) 
    pygame.init()
    app = CameraApp()
    app.run()
        