"""Current delivery-order consent version. Bump when the 须知 text changes."""

DELIVERY_CONSENT_VERSION = '2026-09'


def user_has_delivery_consent(user):
    """True when the user signed the current 配送订单须知 version."""
    if user is None:
        return False
    return getattr(user, 'delivery_consent_version', None) == DELIVERY_CONSENT_VERSION
