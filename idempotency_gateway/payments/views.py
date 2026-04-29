from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services import handle_payment

@api_view(['POST'])
def process_payment(request):
    # Check for Idempotency_key header
    idempotency_key = request.headers.get('Idempotency-key')
    if not idempotency_key:
        return Response(
            {
                "error": "Idempotency-Key header is required. "
            },
            status=400
        )

    request_body = request.data

    # Check for require fields
    if "amount" not in request_body or "currency" not in request_body:
        return Response(
            {"error": "Request body must contain amount and currency."},
            status=400
        )

    # Handle payment through the Service Layer
    response_data, status_code, cache_hit = handle_payment(
        idempotency_key, request_body
    )

    response = Response(response_data, status=status_code)

    # Add cache hit header for duplicate requests
    if cache_hit:
        response['X-Cache-Hit'] = 'true'

    return response

