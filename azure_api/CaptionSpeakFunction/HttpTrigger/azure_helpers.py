import os
import subprocess
import requests
import time
from dotenv import load_dotenv, find_dotenv
from xml.etree import ElementTree
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
import io
from typing import Tuple

load_dotenv(find_dotenv())

COMPUTER_VISION_ENDPOINT = os.environ['COMPUTER_VISION_ENDPOINT']
COMPUTER_VISION_KEY = os.environ['COMPUTER_VISION_ACCOUNT_KEY']

SPEECH_KEY = os.environ['SPEECH_ACCOUNT_KEY']
SPEECH_FETCH_TOKEN_URL = os.environ['SPEECH_FETCH_TOKEN_URL']
SPEECH_REST_URL = os.environ['SPEECH_REST_URL']


# TODO add exception handeling in case of index out of range error, also investigate this
class AzureCaptioner:
    def __init__(self, endpoint=COMPUTER_VISION_ENDPOINT, key=COMPUTER_VISION_KEY):
        self.credentials = CognitiveServicesCredentials(key)
        self.client = ComputerVisionClient(endpoint, self.credentials)

    def generate_caption(self, stream: io.BytesIO) -> str:
        """Generate a caption for an image using Azure
        
        Arguments:
            stream {io.BytesIO} -- Byte stream containing image data
        
        Returns:
            str -- Caption for the image
        """

        analysis = self.client.describe_image_in_stream(image=stream, max_candidates=1, language='en')
        return "I see " + analysis.captions[0].text


class TmpSpeaker:
    # Converts text to speech using espeak command line tool, for testing purposes
    def __init__(self):
        pass

    def speak(self, text):
        print(text)
        subprocess.call(['espeak', "'{}'".format(text), '2>/dev/null'])


# TODO add logging
# TODO Add params for tts config
# TODO check if token is expired and refresh if needed (remember to initialie tts at beginning of azure function)
class AzureTextToSpeech(object):
    def __init__(self, key=SPEECH_KEY, rest_url=SPEECH_REST_URL, fetch_token_url=SPEECH_FETCH_TOKEN_URL):
        self.key = key
        self.rest_url = rest_url
        self.fetch_token_url = fetch_token_url
        self.access_token = None
        self.get_token()

    def get_token(self):
        # Get access token from Azure

        headers = {
            'Ocp-Apim-Subscription-Key': self.key
        }
        response = requests.post(self.fetch_token_url, headers=headers)
        self.access_token = str(response.text)

    def construct_ssml(self, text: str) -> str:
        """Construct SSML (Speech Synthesis Markup Language) configuration for speech REST API
        
        Arguments:
            text {str} -- text to be synthesized into speech
        
        Returns:
            {str} -- String representation of the SSML config
        """

        xml_body = ElementTree.Element('speak', version='1.0')
        xml_body.set('{http://www.w3.org/XML/1998/namespace}lang', 'en-us')
        voice = ElementTree.SubElement(xml_body, 'voice')
        voice.set('{http://www.w3.org/XML/1998/namespace}lang', 'en-US')
        voice.set('name', 'Microsoft Server Speech Text to Speech Voice (en-US, Guy24KRUS)')
        voice.text = text
        return ElementTree.tostring(xml_body)

    def get_audio(self, text: str) -> requests.Response:
        """Convert text to audio using Azure Text to Speech REST API
        
        Arguments:
            text {str} -- Text to be synthesized into speech
        
        Returns:
            response -- Response object returned from Azure. Body contains audio data.
        """

        headers = {
            'Authorization': 'Bearer ' + self.access_token,
            'Content-Type': 'application/ssml+xml',
            'X-Microsoft-OutputFormat': 'raw-24khz-16bit-mono-pcm',
            'User-Agent': 'seeing-eye-pi'
        }
        
        body = self.construct_ssml(text)
        response = requests.post(self.rest_url, headers=headers, data=body)
        if response.status_code == 200:
            print("\nStatus code: " + str(response.status_code))
        else:
            print("\nStatus code: " + str(response.status_code) + "\nSomething went wrong. Check your subscription key and headers.\n")
        return response

# TODO create base class to generalize this process, may want different captioning or tts systems in the future
class AzureImageToSpeech(object):
    def __init__(self, 
                 cv_endpoint=COMPUTER_VISION_ENDPOINT,
                 cv_key=COMPUTER_VISION_KEY,
                 speech_key=SPEECH_KEY,
                 speech_rest_url=SPEECH_REST_URL,
                 speech_fetch_token_url=SPEECH_FETCH_TOKEN_URL):

        self.cv_endpoint = cv_endpoint
        self.cv_key = cv_key
        self.speech_key = speech_key
        self.speech_rest_url = speech_rest_url
        self.speech_fetch_token_url = speech_fetch_token_url
        self.captioner = AzureCaptioner(endpoint=self.cv_endpoint, key=self.cv_key)
        self.tts = AzureTextToSpeech(key=self.speech_key, rest_url=self.speech_rest_url, fetch_token_url=speech_fetch_token_url)

    def get_caption_and_audio(self, image: io.BytesIO) -> Tuple[str, bytes]:
        """Caption an image and convert the caption to audio
        
        Arguments:
            image {io.BytesIO} -- Byte stream containing image data
        
        Returns:
            Tuple[str, bytes] -- Caption and audio of caption.
        """
        caption = self.captioner.generate_caption(image)
        audio_response = self.tts.get_audio(caption)
        return caption, audio_response.content
