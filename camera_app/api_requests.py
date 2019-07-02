import requests
import base64
import json
from typing import Tuple

class ImageToSpeechRequest(object):
    def __init__(self, url):
        self.url = url
    
    def post_request(self, image: bytes) -> Tuple[str, bytes]:
        """Post image and receive response.
        Image data sent in request body.
        Response contains the following:
            Headers: {'caption': String of caption describing processed image}
            Body: Base64 encoded audio of the caption
        
        Arguments:
            image {bytes} -- Image to be posted.
        
        Returns:
            Tuple[str, bytes] -- Caption and decoded audio.
        """
        image_encoded = base64.b64encode(image)
        response = requests.post(self.url, image_encoded) 
        caption = response.headers['caption']
        audio_b64 = response.content
        audio = base64.b64decode(audio_b64)
        return caption, audio
