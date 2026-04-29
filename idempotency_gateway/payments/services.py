import hashlib
import json
import time
import threading
from .models import IdempotencyRecord

# Global lock registry — one lock per idempotency key
_locks = {}
_locks_mutex = threading.Lock()


def get_lock_for_key(key: str) -> threading.Lock:
    """Get or create a lock for a specific idempotency key."""
    with _locks_mutex:
        if key not in _locks:
            _locks[key] = threading.Lock()
        return _locks[key]


def hash_body(request_body: dict) -> str:
    """Create a consistent hash of the request body for comparison."""
    serialized = json.dumps(request_body, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()


def process_payment(record: IdempotencyRecord) -> dict:
    """Simulate payment processing with a 2 second delay."""
    time.sleep(2)
    amount = record.request_body.get("amount")
    currency = record.request_body.get("currency")
    return {
        "status": "Success",
        "message": f"Charged {amount} {currency}",
        "idempotency_key": record.idempotency_key,
    }


def handle_payment(idempotency_key: str, request_body: dict):
    """
    Core idempotency logic:
    - New key: process and save
    - Same key + same body: return cached response
    - Same key + different body: return 409 conflict
    - In-flight: wait for processing to finish, return result
    """
    body_hash = hash_body(request_body)

    # Get a lock specific to this idempotency key
    lock = get_lock_for_key(idempotency_key)

    with lock:
        existing = IdempotencyRecord.objects.filter(
            idempotency_key=idempotency_key
        ).first()

        # Case 1: New key — process payment
        if not existing:
            record = IdempotencyRecord.objects.create(
                idempotency_key=idempotency_key,
                request_body=request_body,
                is_processing=True,
            )
            response_data = process_payment(record)
            record.response_body = response_data
            record.status_code = 201
            record.is_processing = False
            record.save()
            return response_data, 201, False

        # Case 2: Same key + different body — reject
        if hash_body(existing.request_body) != body_hash:
            return {
                "error": "Idempotency key already used for a different request body"
            }, 409, False

        # Case 3: Same key + same body — return cached response
        return existing.response_body, existing.status_code, True