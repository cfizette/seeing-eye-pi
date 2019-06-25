import requests
import io
import base64
import pygame
import time

pygame.mixer.init(12000)

with open('cat.jpg', 'rb') as f:
    data = f.read()
    data = base64.b64encode(data)  # data must be b64 encoded to be read correctly by azure function
    #print(data[:10])
    #print(len(data))
    r = requests.post('http://localhost:7071/api/HttpTrigger', data)

audio = base64.b64decode(r.content)
sound = pygame.mixer.Sound(audio)
channel = sound.play()
while channel.get_busy():
    # maybe use something other than time.sleep
    time.sleep(0.1)

