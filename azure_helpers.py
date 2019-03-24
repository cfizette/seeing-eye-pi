import os
import subprocess
import requests
import time
import pdb
from xml.etree import ElementTree
from dotenv import load_dotenv, find_dotenv
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
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

    def generate_caption(self, stream):
        analysis = self.client.describe_image_in_stream(stream, 1, 'en')
        return "I see " + analysis.captions[0].text


class TmpSpeaker:
    def __init__(self):
        pass

    def speak(self, text):
        print(text)
        subprocess.call(['espeak', "'{}'".format(text), '2>/dev/null'])


#TODO add logging
class AzureTextToSpeech(object):
    def __init__(self, key=SPEECH_KEY, rest_url=SPEECH_REST_URL):
        self.key = key
        self.rest_url = rest_url
        self.access_token = None
        self.get_token()

    def get_token(self, fetch_token_url=SPEECH_FETCH_TOKEN_URL):
        headers = {
            'Ocp-Apim-Subscription-Key': self.key
        }
        response = requests.post(fetch_token_url, headers=headers)
        self.access_token = str(response.text)

    def get_audio(self, text):
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
            'Content-Type': 'application/ssml+xml',
            'X-Microsoft-OutputFormat': 'raw-24khz-16bit-mono-pcm',
            'User-Agent': 'seeing-eye-pi'
        }
        xml_body = ElementTree.Element('speak', version='1.0')
        xml_body.set('{http://www.w3.org/XML/1998/namespace}lang', 'en-us')
        voice = ElementTree.SubElement(xml_body, 'voice')
        voice.set('{http://www.w3.org/XML/1998/namespace}lang', 'en-US')
        voice.set('name', 'Microsoft Server Speech Text to Speech Voice (en-US, Guy24KRUS)')
        voice.text = text
        body = ElementTree.tostring(xml_body)

        response = requests.post(self.rest_url, headers=headers, data=body)
        if response.status_code == 200:
            print("\nStatus code: " + str(response.status_code))
            return response.content
        else:
            print("\nStatus code: " + str(response.status_code) + "\nSomething went wrong. Check your subscription key and headers.\n")
            return None