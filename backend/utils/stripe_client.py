"""Stripe SDK client. Instantiates StripeClient — do not set stripe.api_key globally."""

from flask import current_app


def stripe_secret_key():
    return (current_app.config.get('STRIPE_SECRET_KEY') or '').strip()


def stripe_webhook_secret():
    return (current_app.config.get('STRIPE_WEBHOOK_SECRET') or '').strip()


def stripe_configured():
    return bool(stripe_secret_key())


def get_stripe_client():
    """Return a StripeClient or None if STRIPE_SECRET_KEY is missing."""
    key = stripe_secret_key()
    if not key:
        return None
    from stripe import StripeClient

    return StripeClient(key)


def stripe_dashboard_payment_url(payment_intent_id):
    if not payment_intent_id:
        return None
    base = (current_app.config.get('STRIPE_DASHBOARD_BASE') or 'https://dashboard.stripe.com/test').rstrip('/')
    return f'{base}/payments/{payment_intent_id}'
