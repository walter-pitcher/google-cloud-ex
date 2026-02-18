"""
Flask HTTP endpoint for Cloud Run.
Cloud Scheduler sends GET requests to this URL to trigger one poll cycle.
"""

import os

from flask import Flask

from main import run_poll

app = Flask(__name__)


@app.route("/", methods=["GET"])
def run() -> str:
    """Run one poll cycle and return OK."""
    run_poll()
    return "OK"


@app.route("/health", methods=["GET"])
def health() -> str:
    """Liveness/readiness check for Cloud Run."""
    return "OK"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
