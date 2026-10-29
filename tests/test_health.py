
import json

import azure.functions as func

from function_app import health


def test_health_endpoint():
    request = func.HttpRequest(
        method="GET",
        url="http://localhost/api/health",
        headers={},
        params={},
        body=b""
    )

    response = health(request)

    assert response.status_code == 200

    payload = json.loads(response.get_body())
    assert payload["project"] == "IYAV"
    assert payload["status"] == "healthy"
