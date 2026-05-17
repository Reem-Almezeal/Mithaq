# =============================================================================
# payments/services/moyasar_service.py
# OWNED BY: Ghadi
#
# PURPOSE:
#   All communication with the Moyasar payment API lives here.
#   Nothing outside this file should ever call the Moyasar API directly.
#
# SANDBOX VS PRODUCTION:
#   Keys are in .env — NEVER put them in code.
#   Current .env uses sandbox keys (sk_test_... / pk_test_...).
#   Before going live: replace with production keys from moyasar.com dashboard.
#   Also update MOYASAR_CALLBACK_URL in .env to the real server domain.
#
# MOYASAR AMOUNTS:
#   Moyasar uses halalas (smallest SAR unit): 1 SAR = 100 halalas.
#   All amounts are multiplied by 100 before sending to the API.
#   Example: plan.price = 99 SAR → API receives amount = 9900
#
# SECURITY RULES (never break these):
#   - Never trust callback query params alone — always call verify_payment()
#     to re-fetch the real status from Moyasar's API.
#   - Always check amount matches the local PaymentRecord before activating.
#   - SELECT FOR UPDATE on PaymentRecord prevents double-processing.
#
# CALLED FROM:
#   payments/views.py → CheckoutView.post()         → initiate_payment()
#   payments/views.py → PaymentCallbackView.get()   → handle_callback()
#
# FUTURE WORK (Ghadi):
#   - Handle REFUNDED status from Moyasar (add to handle_callback)
#   - Support stcpay and applepay (currently card only)
#   - Add retry logic if Moyasar API is temporarily down
# =============================================================================

import logging
import uuid

import requests
from django.conf import settings
from django.db import transaction

from payments.models import PaymentRecord
from subscriptions.models import SubscriptionPlan

logger = logging.getLogger(__name__)


class MoyasarError(Exception):
    """Raised when the Moyasar API is unreachable or returns an unexpected response."""
    pass


def _auth() -> tuple:
    """Return HTTP Basic Auth tuple for Moyasar: (secret_key, empty_password)."""
    return (settings.MOYASAR_API_KEY, '')


def initiate_payment(user, plan: SubscriptionPlan) -> str:
    """
    Create a PaymentRecord and call the Moyasar API to open a payment session.

    A temporary unique placeholder is written to moyasar_payment_id so the record
    can be saved before the API call (its ID is included in metadata sent to Moyasar).
    The real Moyasar payment ID replaces it once the API responds successfully.

    Amount is converted from SAR to halalas (× 100) as required by Moyasar.

    Returns:
        The Moyasar-hosted payment URL to redirect the user to.

    Raises:
        MoyasarError: if the API is unreachable, times out, or returns an unexpected body.
    """
    amount_halalas = int(plan.price * 100)

    payment_record = PaymentRecord.objects.create(
        user=user,
        plan=plan,
        moyasar_payment_id=f'tmp_{uuid.uuid4().hex}',
        amount=plan.price,
        currency='SAR',
        status=PaymentRecord.Status.INITIATED,
    )

    payload = {
        'amount': amount_halalas,
        'currency': 'SAR',
        'description': f'Mithaq - {plan.name_ar}',
        'callback_url': settings.MOYASAR_CALLBACK_URL,
        'metadata': {
            'user_id': str(user.id),
            'plan_id': str(plan.id),
            'payment_record_id': str(payment_record.id),
        },
    }

    logger.info(
        'Initiating Moyasar payment | user=%s plan=%s amount_halalas=%s',
        user.id, plan.id, amount_halalas,
    )

    try:
        response = requests.post(
            f'{settings.MOYASAR_BASE_URL}/payments',
            json=payload,
            auth=_auth(),
            timeout=10,
        )
        logger.info(
            'Moyasar initiate response | http_status=%s body=%.500s',
            response.status_code, response.text,
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        payment_record.delete()
        raise MoyasarError('Moyasar API timed out after 10 seconds')
    except requests.exceptions.RequestException as exc:
        payment_record.delete()
        raise MoyasarError(f'Moyasar API request failed: {exc}')

    moyasar_id = data.get('id')
    # Card payments return the hosted page URL under source.transaction_url
    payment_url = (
        data.get('source', {}).get('transaction_url')
        or data.get('url')
    )

    if not moyasar_id or not payment_url:
        payment_record.delete()
        raise MoyasarError(f'Unexpected Moyasar response structure: {data}')

    payment_record.moyasar_payment_id = moyasar_id
    payment_record.save(update_fields=['moyasar_payment_id'])

    logger.info(
        'PaymentRecord id=%s linked to Moyasar payment_id=%s',
        payment_record.id, moyasar_id,
    )
    return payment_url


def handle_callback(moyasar_payment_id: str) -> str:
    """
    Process a Moyasar payment callback safely.

    Never trusts the callback query parameters alone — always re-fetches the
    payment status from the Moyasar API to verify it.

    Uses SELECT FOR UPDATE on the PaymentRecord to prevent double-processing
    when Moyasar fires the callback more than once.

    Performs an amount integrity check: if the amount Moyasar reports does not
    match what was stored locally (in halalas), the payment is rejected and
    logged as a warning without activating the subscription.

    Returns:
        'paid'      — payment verified, subscription activated.
        'failed'    — payment failed, cancelled, or amount mismatch.
        'initiated' — payment still pending (no action taken).

    Raises:
        ValueError:    if no matching PaymentRecord exists locally.
        MoyasarError:  if the Moyasar verification API call fails.
    """
    from subscriptions.services.subscription_service import activate_subscription

    logger.info('Handling callback | moyasar_payment_id=%s', moyasar_payment_id)

    moyasar_data = verify_payment(moyasar_payment_id)
    moyasar_status = moyasar_data.get('status', '').lower()
    moyasar_amount = moyasar_data.get('amount')  # halalas

    logger.info(
        'Moyasar verified | payment_id=%s status=%s amount_halalas=%s',
        moyasar_payment_id, moyasar_status, moyasar_amount,
    )

    with transaction.atomic():
        try:
            record = (
                PaymentRecord.objects
                .select_for_update()
                .select_related('user', 'plan')
                .get(moyasar_payment_id=moyasar_payment_id)
            )
        except PaymentRecord.DoesNotExist:
            logger.error('No PaymentRecord found | moyasar_payment_id=%s', moyasar_payment_id)
            raise ValueError(f'PaymentRecord not found for Moyasar ID: {moyasar_payment_id}')

        # Idempotency: callback already processed successfully
        if record.status == PaymentRecord.Status.PAID:
            logger.info('Callback already processed, skipping | payment_id=%s', moyasar_payment_id)
            return 'paid'

        # Amount integrity check (local SAR × 100 must match Moyasar halalas)
        expected_halalas = int(record.amount * 100)
        if moyasar_amount != expected_halalas:
            logger.warning(
                'Amount mismatch — NOT activating | expected_halalas=%s moyasar_halalas=%s payment_id=%s',
                expected_halalas, moyasar_amount, moyasar_payment_id,
            )
            record.status = PaymentRecord.Status.FAILED
            record.save(update_fields=['status', 'updated_at'])
            return 'failed'

        if moyasar_status == 'paid':
            record.status = PaymentRecord.Status.PAID
            record.save(update_fields=['status', 'updated_at'])
            activate_subscription(record.user, record.plan)
            logger.info(
                'Subscription activated | user=%s plan=%s',
                record.user.id, record.plan.id,
            )
            return 'paid'

        if moyasar_status in ('failed', 'cancelled'):
            record.status = PaymentRecord.Status.FAILED
            record.save(update_fields=['status', 'updated_at'])
            logger.info('Payment %s | user=%s', moyasar_status, record.user.id)
            return 'failed'

        return 'initiated'


def verify_payment(moyasar_payment_id: str) -> dict:
    """
    Fetch the raw payment object from the Moyasar API.

    Used internally by handle_callback and available for manual verification.

    Returns:
        The full Moyasar payment dict (amounts are in halalas).

    Raises:
        MoyasarError: if the request times out or the HTTP call fails.
    """
    url = f'{settings.MOYASAR_BASE_URL}/payments/{moyasar_payment_id}'
    logger.info('Verifying payment | moyasar_payment_id=%s', moyasar_payment_id)

    try:
        response = requests.get(url, auth=_auth(), timeout=10)
        logger.info('Moyasar verify response | http_status=%s', response.status_code)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        raise MoyasarError('Moyasar API timed out after 10 seconds')
    except requests.exceptions.RequestException as exc:
        raise MoyasarError(f'Moyasar API request failed: {exc}')
