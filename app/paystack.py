"""
Thin wrapper around Paystack's REST API. Keys come from the encrypted
PlatformSetting row (app/models.py), not environment variables — an
admin configures them at /admin/settings.

Paystack's amounts are always in the currency's minor unit (kobo for
NGN), which is also how this app stores every price — see the comment
on ServiceRequest.price in models.py.
"""
import hashlib
import hmac

import requests

PAYSTACK_BASE_URL = "https://api.paystack.co"


class PaystackError(Exception):
    pass


def _get_settings():
    from app.models import PlatformSetting

    return PlatformSetting.query.get(1)


def paystack_configured():
    settings = _get_settings()
    return bool(settings and settings.is_configured)


def initialize_transaction(email, amount_kobo, reference, callback_url):
    """
    Start a Paystack checkout. Returns the authorization_url to redirect
    the customer to. Raises PaystackError on failure — callers should
    catch it and show a friendly message rather than a stack trace.
    """
    settings = _get_settings()
    if not settings or not settings.is_configured:
        raise PaystackError("Paystack isn't configured yet.")

    resp = requests.post(
        f"{PAYSTACK_BASE_URL}/transaction/initialize",
        headers={"Authorization": f"Bearer {settings.paystack_secret_key}"},
        json={
            "email": email,
            "amount": amount_kobo,
            "reference": reference,
            "callback_url": callback_url,
        },
        timeout=15,
    )
    data = resp.json()
    if not resp.ok or not data.get("status"):
        raise PaystackError(data.get("message", "Paystack couldn't start the payment."))
    return data["data"]["authorization_url"]


def verify_transaction(reference):
    """
    Confirm a transaction's real status directly with Paystack — used both
    by the webhook handler and the callback-redirect page, since neither
    a webhook call nor a redirect back to our site should be trusted on
    its own as proof of payment. Returns the Paystack transaction data
    dict (status, amount, etc.) or raises PaystackError.
    """
    settings = _get_settings()
    if not settings or not settings.is_configured:
        raise PaystackError("Paystack isn't configured yet.")

    resp = requests.get(
        f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}",
        headers={"Authorization": f"Bearer {settings.paystack_secret_key}"},
        timeout=15,
    )
    data = resp.json()
    if not resp.ok or not data.get("status"):
        raise PaystackError(data.get("message", "Couldn't verify that payment with Paystack."))
    return data["data"]


def verify_webhook_signature(request_body_bytes, signature_header):
    """
    Paystack signs webhook payloads with HMAC-SHA512 of the raw request
    body, using the secret key. Must be checked before trusting ANY
    webhook payload — otherwise anyone who finds the webhook URL could
    POST a fake "payment successful" event.
    """
    settings = _get_settings()
    if not settings or not settings.paystack_secret_key:
        return False
    expected = hmac.new(
        settings.paystack_secret_key.encode(), request_body_bytes, hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header or "")
