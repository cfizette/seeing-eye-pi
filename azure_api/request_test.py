import requests
import io


with open('foo.txt') as f:
    data = f.read()
    r = requests.get('http://localhost:7071/api/HttpTrigger', data=data)



print(r.text)
