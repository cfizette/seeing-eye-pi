import os
import io
import re
import sys
import pygame
from PIL import Image
from os.path import join
import RPi.GPIO as GPIO
from picamera import PiCamera
from api_requests import ImageToSpeechRequest
from typing import Tuple

APP_PATH = os.path.dirname(os.path.abspath(__file__))
TAKE_PHOTO_PIN = 17
QUIT_PIN = 27
WINDOW_SIZE = (640,480)
FULL_IMAGE_SIZE = WINDOW_SIZE
RGB_DATA_SIZE = WINDOW_SIZE[0] * WINDOW_SIZE[1] * 3  
WAIT_AFTER_PHOTO = 3
IMG_DIR = os.path.join(APP_PATH, 'photos')
AUDIO_FREQUENCY = 12000 #TODO figure out correct setting for this
REQUEST_URL = 'https://seeing-eye-pi.azure-api.net/ImageToSpeechV1NorthCentralUS/HttpTrigger'
SHUTTER_EFFECT_PATH = os.path.join(APP_PATH, 'assets/camera-shutter.ogg')


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

    def save_img_and_caption(self, stream: io.BytesIO, caption: str):
        """Save image and caption.
        Files are saved within self.img_dir.
        Images saved as IMG_<self.n>.jpg.
        Captions saved as IMG_<self.n>.txt
        
        Arguments:
            stream {io.BytesIO} -- Stream containing image.
            caption {str} -- String of caption.
        """
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
        self.screen = pygame.display.set_mode(WINDOW_SIZE, pygame.FULLSCREEN)
        self.camera = PiCamera()
        self.filesystem = CameraAppFilesystem()
        self.shutter_effect = pygame.mixer.Sound(SHUTTER_EFFECT_PATH)
        # Setup button interrupts
        self.setup_interrupt_button(TAKE_PHOTO_PIN, self.capture_and_process_image)
        self.setup_interrupt_button(QUIT_PIN, self.quit)

    def setup_interrupt_button(self, pin: int, callback: callable):
        """Configure falling interrupt on pin.
        Sets up GPIO pin with a pull up resistor. When button is pressed, it will be grounded.
        Thus a falling signal is used to trigger the interrupt.
        
        Arguments:
            pin {int} -- GPIO pin to use for interrupt.
            callback {callable} -- Function or other callable to be called on interrupt.
                The callable must be able to accept an argument being passed to it as pin is passed to it.
        """
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(pin, GPIO.FALLING, callback, 200)

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

    def capture_photo_to_stream(self, use_video_port: bool, resize: Tuple[int, int], img_format: str) -> io.BytesIO:
        """Capture image to stream.
        
        Arguments:
            use_video_port {bool} -- If true, use camera image port to capture image. Otherwise use video port.
            resize {Tuple[int, int]} -- Size of image to be captured.
            img_format {str} -- Dictates image format to be captured. See picamera documentation for supported formats.
        
        Returns:
            io.BytesIO -- Stream containing image data.
        """
        stream = io.BytesIO()
        self.camera.capture(stream, use_video_port=use_video_port, resize=resize, format=img_format)
        stream.seek(0)
        return stream

    def play_pygame_sound(self, sound: pygame.mixer.Sound):
        """Play a sound using pygame. 
        This function delays the program while the sound is being played to allow it to be played entirely.
        
        Arguments:
            sound {pygame.mixer.Sound} -- [description]
        """
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
        caption, audio = self.image_to_speech.post_request(image_bytes)
        print("Received audio and caption")
        print(caption)
        print('Playing audio')
        sound = pygame.mixer.Sound(audio)
        self.play_pygame_sound(sound)
        print("Saving data")
        self.filesystem.save_img_and_caption(stream, caption) 
    
    def quit(self):
        pygame.quit()
        sys.exit

    def run(self):
        while True:
            self.show_viewfinder()


if __name__ == "__main__":
    pygame.mixer.pre_init(frequency=AUDIO_FREQUENCY) 
    pygame.init()
    app = CameraApp()
    app.run()
        