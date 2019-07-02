import logging
import io
import azure.functions as func
from HttpTrigger.azure_helpers import AzureCaptioner, AzureTextToSpeech, AzureImageToSpeech
import base64
import json

# TODO Investigate how cacheing this object works on an azure function
# Does this actually increase responsiveness since we don't need to fetch a token
# every time a request is made?
# Figure out how to tell when token is expired and then re-fetch it.
its = AzureImageToSpeech()

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Generate caption describing image and audio of that caption.
    
    Arguments:
        req {func.HttpRequest} -- Body of HttpRequest must contain b64 encoded image.
                                  See Azure Computer Vision API for details on supported image formats.
    
    Returns:
        func.HttpResponse -- Body: Base 64 encoded audio
                             Headers: {
                                 'caption': String of caption
                             }
    """
    logging.info('Python HTTP trigger function processed a request.')

    # Read, decode, and construct generator
    image_encoded = req.get_body()
    image_decoded = base64.b64decode(image_encoded)
    image = io.BytesIO(image_decoded)

    if image:
        caption, audio = its.get_caption_and_audio(image)
        audio_b64 = base64.b64encode(audio)
        headers = {'caption':caption}
        return func.HttpResponse(body=audio_b64, headers=headers)
    # TODO Create better response if error occurs
    else:
        return func.HttpResponse(
             "Please pass a name on the query string or in the request body",
             status_code=400
        )
