import os
import subprocess
from dotenv import load_dotenv, find_dotenv
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
load_dotenv(find_dotenv())

REGION = os.environ['ACCOUNT_REGION']
KEY = os.environ['ACCOUNT_KEY']

# TODO add exception handeling in case of index out of range error, also investigate this
class AzureCaptioner:
    def __init__(self, region=REGION, key=KEY):
        self.credentials = CognitiveServicesCredentials(key)
        self.client = ComputerVisionClient(region, self.credentials)

    def generate_caption(self, stream):
        analysis = self.client.describe_image_in_stream(stream, 1, 'en')
        return "I see " + analysis.captions[0].text


class TmpSpeaker:
    def __init__(self):
        pass

    def speak(self, text):
        print(text)
        subprocess.call(['espeak', "'{}'".format(text), '2>/dev/null'])