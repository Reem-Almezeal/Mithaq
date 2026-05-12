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
            from rest_framework import status
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
