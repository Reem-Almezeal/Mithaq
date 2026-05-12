import logging

from django.shortcuts import render, redirect
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from subscriptions.models import SubscriptionPlan
from subscriptions.services.subscription_service import get_user_subscription

from .services.moyasar_service import MoyasarError, handle_callback, initiate_payment

logger = logging.getLogger(__name__)


class CheckoutView(APIView):
    """POST /api/payments/checkout/<plan_id>/ — initiate a Moyasar payment session."""

    permission_classes = [IsAuthenticated]

    def post(self, request, plan_id):
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {'error': 'الباقة غير موجودة'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if plan.price == 0:
            return Response(
                {'error': 'هذه الباقة مجانية ولا تتطلب دفعاً'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sub = get_user_subscription(request.user)
        if sub and sub.plan.plan_type != SubscriptionPlan.PlanType.FREE:
            return Response(
                {'error': 'لديك اشتراك نشط بالفعل'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment_url = initiate_payment(request.user, plan)
        except MoyasarError as exc:
            logger.error('Moyasar error during checkout | user=%s plan=%s error=%s',
                         request.user.id, plan_id, exc)
            return Response(
                {'error': 'خدمة الدفع غير متاحة حالياً، يرجى المحاولة لاحقاً'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({'payment_url': payment_url})


class PaymentCallbackView(APIView):
    """
    GET /api/payments/callback/
    Public endpoint — Moyasar redirects the user here after payment.
    Always re-verifies status with the Moyasar API before activating anything.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        moyasar_payment_id = request.GET.get('id')

        if not moyasar_payment_id:
            logger.warning('Callback received with no payment ID in query params')
            return redirect('/api/payments/failed/')

        try:
            result = handle_callback(moyasar_payment_id)
        except Exception as exc:
            logger.error('Callback error | payment_id=%s error=%s', moyasar_payment_id, exc)
            return redirect('/api/payments/failed/')

        if result == 'paid':
            return redirect('/api/payments/success/')
        return redirect('/api/payments/failed/')


# ── HTML result pages ────────────────────────────────────────────────────────

def payment_success(request):
    """Render the payment success page with subscription details if the user is logged in."""
    sub = None
    if request.user.is_authenticated:
        sub = get_user_subscription(request.user)
    return render(request, 'payments/payment_success.html', {'subscription': sub})


def payment_failed(request):
    """Render the payment failed / retry page."""
    return render(request, 'payments/payment_failed.html')
