import logging
import io
import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    body = req.get_body()
    #body = io.BytesIO(body)
    if not body:
        pass

    if body:
        return func.HttpResponse('{}'.format(str(body)))
    else:
        return func.HttpResponse(
             "Please pass a name on the query string or in the request body",
             status_code=400
        )
