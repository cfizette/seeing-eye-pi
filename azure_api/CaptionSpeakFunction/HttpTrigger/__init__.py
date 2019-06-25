import logging
import io
import azure.functions as func
from HttpTrigger.azure_helpers import AzureCaptioner
import base64


def main(req: func.HttpRequest) -> func.HttpResponse:
    # Body of request must contain b64 encoded image data

    logging.info('Python HTTP trigger function processed a request.')

    # Read, decode, and construct generator
    image_encoded = req.get_body()
    image_decoded = base64.b64decode(image_encoded)
    image = io.BytesIO(image_decoded)

    if not image:
        pass

    if image:
        captioner = AzureCaptioner()
        caption = captioner.generate_caption(image)
        return func.HttpResponse('{}'.format(caption))
    else:
        return func.HttpResponse(
             "Please pass a name on the query string or in the request body",
             status_code=400
        )
