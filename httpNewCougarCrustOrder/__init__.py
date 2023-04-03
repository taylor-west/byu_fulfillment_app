import datetime
import logging
import json
from . import CougCrustOrderFromHttp

import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_body().decode("utf8").strip('"').strip().replace("\\'", '"') \
                        .replace("False", "false").replace("True", "true")
        logging.info(f'New Request Received:\n{str(req_body)}')

        req_body = json.loads(req_body)
    
    except ValueError as ex:
        return func.HttpResponse(
             f'Error While Parsing Order. Invalid Data Format\n{ex}',
             status_code=400
        )
    
    # if request body is valid json
    try:
        results = CougCrustOrderFromHttp.new_order(req_body)

    except ValueError as ex:
        return func.HttpResponse(
             f'Invalid Data Format\n{ex}',
             status_code=400
        )
    except Exception as ex:
        return func.HttpResponse(
             str(ex),
             status_code=500
        )
    
    return func.HttpResponse(
        f"{results['num_orders_inserted']} Orders were inserted. " + \
        f"{results['num_duplicate_orders']} Orders already existed",
        status_code=200
    )
