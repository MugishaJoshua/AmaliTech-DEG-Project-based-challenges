import hashlib 
import json
import time
from .models import IdempotencyRecord


def hash_body(request_body: dict) -> str:
    """we create a consistent hash of the request body for comparison."""
    serialized = json.dumps(request_body, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()

def process_payment(record: IdempotencyRecord) -> dict:
    """Simulate payment processing with a 2 second delay>"""
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
    core idempotency logic:
    -  New key: process and save
    -  Same key + same body: return cached response
    -  Same Key + different body: return 409 conflict
    """

    body_hash = hash_body(request_body)
    existing = IdempotencyRecord.Objects.filter(
        idempotency_key=idempotency_key
    ) .first()

    # Case 1: New Key - Process payment 
    if not existing:
        record = IdempotencyRecord.objects.create(
            idempotency_key=idempotency_key,
            request_body=request_body,
            is_processing=True
        )
        response_data = process_payment(record)
        record.response_body = response_data
        record.status_code = 201
        record.is_processing = False
        record.save()
        return response_data, 201, False
    
    # Case 2 : Same Key + Same body - Reject as duplicated
    if hash_body(existing.request_body) != body_hash:
        return {
            "error": "Idempotency key already used for a different request body"
        }, 409, False
    
    # Case 3: Same Key + Same Body - Return cached Response
    return existing.response_body, existing.status_code, True