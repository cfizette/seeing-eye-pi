import requests
import io
import base64
import time
from timeit import default_timer as timer

FUNCTION_URL = 'https://seeing-eye-pi.azure-api.net/ImageToSpeechV1/HttpTrigger'
N_ITER = 10

with open('cat.jpg', 'rb') as f:
    data = f.read()
    data = base64.b64encode(data)  # data must be b64 encoded to be read correctly by azure function
    #print(data[:10])
    #print(len(data))

    start = timer()
    for _ in range(N_ITER):
        r = requests.post(FUNCTION_URL, data)
    end = timer()

elapsed = end-start
average_time = elapsed / float(N_ITER)
print('Time elapsed: {}'.format(end-start))
print('Average time: {}'.format(average_time))


