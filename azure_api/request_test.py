import requests
import io
import base64
import pygame
import time

pygame.mixer.init(11500)
FUNCTION_URL = 'https://imagetospeechv1.azurewebsites.net/api/httptrigger?code=7bSOAddjeDxEPv0vJhmD/Z1nZT8ZBHM1QQN499C/pCCgwRzvTHleOw=='

with open('cat.jpg', 'rb') as f:
    data = f.read()
    data = base64.b64encode(data)  # data must be b64 encoded to be read correctly by azure function
    #print(data[:10])
    #print(len(data))
    r = requests.post(FUNCTION_URL, data)

audio = base64.b64decode(r.content)
print(r)
print(r.content[:10])
sound = pygame.mixer.Sound(audio)
channel = sound.play()
while channel.get_busy():
    # maybe use something other than time.sleep
    time.sleep(0.1)

