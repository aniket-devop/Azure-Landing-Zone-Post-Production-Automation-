
import json
import logging

import azure.functions as func

app = func.FunctionApp(
    http_auth_level=func.AuthLevel.ANONYMOUS
)


@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Return the health status of the IYAV application."""
    logging.info("IYAV health endpoint called")

    response = {
        "project": "IYAV",
        "status": "healthy",
        "mode": "foundation"
    }

    return func.HttpResponse(
        json.dumps(response),
        status_code=200,
        mimetype="application/json"
    )
