
from threading import Lock

from flask import Flask, jsonify, request

app = Flask(__name__)

incidents = {}
lock = Lock()
next_number = 100001


@app.route("/api/incidents", methods=["POST"])
def create_incident():
    global next_number

    data = request.get_json(silent=True) or {}
    correlation_id = data.get("correlation_id")

    if not isinstance(correlation_id, str) or not correlation_id.strip():
        return jsonify({"error": "correlation_id is required"}), 400

    correlation_id = correlation_id.strip()

    with lock:
        # Duplicate requests reuse the existing incident.
        for incident in incidents.values():
            if incident["correlation_id"] == correlation_id and incident["state"] not in ("Resolved", "Closed"):
                return jsonify(incident), 200

        number = f"INC{next_number}"
        next_number += 1

        incident = {
            "number": number,
            "correlation_id": correlation_id,
            "short_description": data.get(
                "short_description", "IYAV automated incident"
            ),
            "state": "New"
        }

        incidents[number] = incident

    return jsonify(incident), 201


@app.route("/api/incidents", methods=["GET"])
def list_incidents():
    with lock:
        return jsonify(list(incidents.values())), 200


@app.route("/api/incidents/<number>", methods=["GET"])
def get_incident(number):
    with lock:
        incident = incidents.get(number)

        if incident is None:
            return jsonify({"error": "Incident not found"}), 404

        return jsonify(incident), 200


@app.route("/api/incidents/<number>", methods=["PATCH"])
def update_incident(number):
    data = request.get_json(silent=True) or {}

    with lock:
        incident = incidents.get(number)

        if incident is None:
            return jsonify({"error": "Incident not found"}), 404

        # A ticket cannot be resolved without verified recovery.
        if data.get("state") == "Resolved":
            if data.get("recovery_verified") is not True:
                return jsonify({
                    "error": "Verified recovery is required"
                }), 409

        if "state" in data:
            incident["state"] = data["state"]

        if "short_description" in data:
            incident["short_description"] = data["short_description"]

        return jsonify(incident), 200


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=8090,
        debug=False
    )

