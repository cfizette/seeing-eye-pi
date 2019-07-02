import os
import subprocess
import requests
import time
import pdb
import io
import base64
import json

class ImageToSpeechRequest(object):
    def __init__(self, url):
        self.url = url
    
    def post_request(self, image: bytes) -> str:
        image_encoded = base64.b64encode(image)
        response = requests.post(self.url, image_encoded) 
        caption = response.headers['caption']
        audio_b64 = response.content
        audio = base64.b64decode(audio_b64)
        return caption, audio
