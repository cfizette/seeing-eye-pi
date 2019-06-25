import requests
import io
import base64
import pygame

pygame.mixer.init()

with open('cat.jpg', 'rb') as f:
    data = f.read()
    data = base64.b64encode(data)  # data must be b64 encoded to be read correctly by azure function
    #print(data[:10])
    #print(len(data))
    r = requests.post('http://localhost:7071/api/HttpTrigger', data)

audio = base64.b64decode(r.content)
pygame.mixer.Sound(audio).play()

