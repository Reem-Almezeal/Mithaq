# =============================================================================
# subscriptions/views.py
# OWNED BY: Ghadi
#
# RULE: Views are thin. Each view makes ONE service call and returns the result.
#       All logic lives in subscriptions/services/subscription_service.py.
#
# API ENDPOINTS (require JWT or session auth unless noted):
#   GET  /api/subscriptions/plans/            → PlanListView         (public)
#   GET  /api/subscriptions/status/           → SubscriptionStatusView
#   GET  /api/subscriptions/upgrade-options/  → UpgradeOptionsView
#
# TEMPLATE PAGES (HTML — require session login):
#   GET  /api/subscriptions/plans-page/              → plans_page()
#   GET  /api/subscriptions/checkout-page/<id>/      → checkout_page()
#
# FUTURE WORK (Ghadi):
#   - Add a subscription management page (cancel, view history)
#   - Add a webhook handler if Moyasar sends server-side events
#   - Consider moving template pages to a dedicated frontend once the
#     team decides on a frontend framework
# =============================================================================

from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SubscriptionPlan
from .serializers import SubscriptionPlanSerializer
from .services.subscription_service import get_user_subscription


class PlanListView(APIView):
    """GET /api/subscriptions/plans/ — public list of active subscription plans."""

    permission_classes = [AllowAny]

    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
        return Response(SubscriptionPlanSerializer(plans, many=True).data)


class SubscriptionStatusView(APIView):
    """GET /api/subscriptions/status/ — returns the authenticated user's current subscription."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        sub = get_user_subscription(request.user)
        if not sub:
            return Response(
                {'error': 'لا يوجد اشتراك نشط'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({
            'plan':           sub.plan.name,
            'plan_ar':        sub.plan.name_ar,
            'status':         sub.status,
            'contracts_used': sub.contracts_used,
            'contract_limit': sub.plan.contract_limit,
            'expires_at':     sub.expires_at.date().isoformat() if sub.expires_at else None,
        })


class UpgradeOptionsView(APIView):
    """GET /api/subscriptions/upgrade-options/ — current plan + plans the user can upgrade to."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        sub = get_user_subscription(request.user)
        if not sub:
            return Response(
                {'error': 'لا يوجد اشتراك نشط'},
                status=status.HTTP_404_NOT_FOUND,
            )

        options = SubscriptionPlan.objects.filter(
            is_active=True,
            price__gt=sub.plan.price,
        ).order_by('price')

        return Response({
            'current_plan':    sub.plan.name,
            'current_plan_ar': sub.plan.name_ar,
            'contracts_used':  sub.contracts_used,
            'contract_limit':  sub.plan.contract_limit,
            'can_create':      sub.can_create_contract(),
            'upgrade_options': SubscriptionPlanSerializer(options, many=True).data,
        })


# ── HTML template views ───────────────────────────────────────────────────────

def plans_page(request):
    """Render the plans listing page with the user's current subscription context."""
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
    sub = get_user_subscription(request.user) if request.user.is_authenticated else None
    return render(request, 'subscriptions/plans.html', {
        'plans': plans,
        'current_sub': sub,
    })


def checkout_page(request, plan_id):
    """Render the checkout confirmation page for a specific plan."""
    plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
    return render(request, 'subscriptions/checkout.html', {'plan': plan})
