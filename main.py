"""
Single-execution poller for Cloud Run.
Runs once per HTTP request (triggered by Cloud Scheduler).
No infinite loop — script starts, does work once, exits cleanly.
"""

import logging
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def poll_service() -> list[dict[str, Any]]:
    """
    Poll the publication/message service for new records.
    Replace with your real implementation (e.g. Pub/Sub pull, DB query).
    """
    # Example: mock records — replace with real poll (Pub/Sub, etc.)
    records = [
        {"id": "1", "payload": {"event": "order_created", "order_id": "ord-001"}},
        {"id": "2", "payload": {"event": "order_created", "order_id": "ord-002"}},
    ]
    logger.info("Polled %d record(s)", len(records))
    return records


def map_data(record: dict[str, Any]) -> dict[str, Any]:
    """
    Map/transform raw record into the shape needed by the API.
    """
    payload = record.get("payload", record)
    return {
        "record_id": record.get("id"),
        "event": payload.get("event"),
        "data": payload,
    }


def send_api(mapped: dict[str, Any]) -> None:
    """
    Send mapped data to your external API.
    Replace with real HTTP call (e.g. requests.post(...)).
    """
    # Example: log instead of real API call — replace with requests.post(...)
    logger.info("API send: %s", mapped)


def acknowledge(record: dict[str, Any]) -> None:
    """
    Acknowledge the record so it is not redelivered.
    Replace with your real ack (e.g. Pub/Sub ack, DB update).
    """
    logger.info("Acknowledged record id=%s", record.get("id"))


def run_poll() -> None:
    """
    Run one poll cycle: fetch records, process each, then exit.
    Called once per Cloud Scheduler trigger (or manual HTTP request).
    """
    records = poll_service()

    for r in records:
        mapped = map_data(r)
        send_api(mapped)
        acknowledge(r)

    logger.info("Run finished. Processed %d record(s).", len(records))


if __name__ == "__main__":
    run_poll()
