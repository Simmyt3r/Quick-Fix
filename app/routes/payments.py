from datetime import datetime
from secrets import token_hex

from flask import Blueprint, current_app, flash, redirect, request, url_for
from flask_login import current_user, login_required

from app.extensions import csrf, db, limiter
from app.models import Payment, ServiceRequest
from app.paystack import PaystackError, initialize_transaction, verify_transaction, verify_webhook_signature

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


def _mark_paid(payment, verified_amount):
    """Shared by both the webhook and the callback-verify path, since
    either one might be the first to see a successful payment — whichever
    gets there first does the work, the other is a safe no-op."""
    job = payment.service_request

    if payment.status == "paid":
        return  # already handled by the other path

    if verified_amount != payment.amount:
        # Paystack confirms a different amount than we expect — don't
        # trust it. This should never happen outside tampering or a
        # serious bug, so it's worth its own log line.
        current_app.logger.error(
            "Payment %s amount mismatch: expected %s, Paystack says %s",
            payment.paystack_reference, payment.amount, verified_amount,
        )
        payment.status = "failed"
        db.session.commit()
        return

    payment.status = "paid"
    payment.paid_at = datetime.utcnow()
    if job.status == "accepted":
        job.status = "in_progress"
    db.session.commit()


@payments_bp.route("/<int:request_id>/start", methods=["POST"])
@login_required
@limiter.limit("10 per hour", methods=["POST"])
def start(request_id):
    job = ServiceRequest.query.get_or_404(request_id)

    if job.customer_id != current_user.id:
        flash("You can only pay for your own requests.", "error")
        return redirect(url_for("dashboard.home"))
    if job.status != "accepted":
        flash("This job isn't ready for payment yet.", "error")
        return redirect(url_for("dashboard.home"))
    if not job.price:
        flash("This job doesn't have a price set yet.", "error")
        return redirect(url_for("dashboard.home"))

    reference = f"qf_{job.id}_{token_hex(8)}"
    payment = Payment(
        service_request_id=job.id,
        customer_id=current_user.id,
        paystack_reference=reference,
        amount=job.price,
    )
    db.session.add(payment)
    db.session.commit()

    try:
        checkout_url = initialize_transaction(
            email=current_user.email,
            amount_kobo=job.price,
            reference=reference,
            callback_url=url_for("payments.callback", reference=reference, _external=True),
        )
    except PaystackError as exc:
        payment.status = "failed"
        db.session.commit()
        flash(f"Couldn't start payment: {exc}", "error")
        return redirect(url_for("dashboard.home"))

    return redirect(checkout_url)


@payments_bp.route("/callback/<reference>")
def callback(reference):
    """Paystack redirects the customer's browser back here after checkout.
    This is NEVER trusted as proof of payment on its own — a customer
    could hit this URL directly without paying — so it re-verifies
    directly with Paystack's API before marking anything paid. The
    webhook (below) is the real source of truth; this exists so the
    customer sees an immediate result instead of staring at a blank
    redirect until the webhook eventually fires."""
    payment = Payment.query.filter_by(paystack_reference=reference).first()
    if payment is None:
        flash("We couldn't find that payment.", "error")
        return redirect(url_for("dashboard.home"))

    try:
        data = verify_transaction(reference)
    except PaystackError:
        flash("We couldn't confirm that payment yet — check back shortly.", "error")
        return redirect(url_for("dashboard.home"))

    if data.get("status") == "success":
        _mark_paid(payment, data.get("amount"))
        flash("Payment received — the job is now in progress.", "success")
    else:
        if payment.status != "paid":
            payment.status = "failed"
            db.session.commit()
        flash("That payment didn't go through. You can try again from your dashboard.", "error")

    return redirect(url_for("dashboard.home"))


@payments_bp.route("/webhook", methods=["POST"])
@csrf.exempt  # Paystack posts here directly, with no CSRF token — signature verification is the real guard
def webhook():
    """
    The actual source of truth for payment status — Paystack calls this
    server-to-server once a transaction completes, independent of whether
    the customer's browser ever made it back to /payments/callback (they
    might close the tab, lose connection, etc.). Every request is
    signature-verified before anything in the payload is trusted.
    """
    signature = request.headers.get("X-Paystack-Signature", "")
    if not verify_webhook_signature(request.get_data(), signature):
        current_app.logger.warning("Rejected webhook with invalid Paystack signature")
        return "", 401

    payload = request.get_json(silent=True) or {}
    if payload.get("event") != "charge.success":
        return "", 200  # acknowledge anything we don't act on, so Paystack stops retrying it

    reference = payload.get("data", {}).get("reference")
    amount = payload.get("data", {}).get("amount")
    payment = Payment.query.filter_by(paystack_reference=reference).first()
    if payment is None:
        current_app.logger.warning("Webhook for unknown payment reference: %s", reference)
        return "", 200

    _mark_paid(payment, amount)
    return "", 200
