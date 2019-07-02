import requests
import io
import base64
import pygame
import time
import json

pygame.mixer.init(11500)
FUNCTION_URL = 'http://localhost:7072/api/HttpTrigger'

with open('cat.jpg', 'rb') as f:
    data = f.read()
    data = base64.b64encode(data)  # data must be b64 encoded to be read correctly by azure function
    #print(data[:10])
    #print(len(data))
    r = requests.post(FUNCTION_URL, data)

caption = r.headers['caption']
audio_encoded = r.content
audio = base64.b64decode(audio_encoded)
print(r)
print(r.content[10000:10010])
sound = pygame.mixer.Sound(audio)
channel = sound.play()
while channel.get_busy():
    time.sleep(0.1)
