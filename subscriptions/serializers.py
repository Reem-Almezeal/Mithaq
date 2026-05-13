from rest_framework import serializers

from .models import SubscriptionPlan, UserSubscription


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = (
            'id', 'name', 'name_ar', 'plan_type',
            'price', 'contract_limit', 'duration_days',
        )


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    can_create_contract = serializers.SerializerMethodField()

    class Meta:
        model = UserSubscription
        fields = (
            'id', 'plan', 'status', 'contracts_used',
            'started_at', 'expires_at', 'can_create_contract',
        )

    def get_can_create_contract(self, obj: UserSubscription) -> bool:
        return obj.can_create_contract()
