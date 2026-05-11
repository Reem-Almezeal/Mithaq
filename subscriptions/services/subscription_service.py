from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from subscriptions.models import SubscriptionPlan, UserSubscription


def assign_free_plan(user) -> UserSubscription:
    """
    Assign the Free plan to a newly registered user.

    Creates an ACTIVE UserSubscription with no expiry date (duration_days=0
    means the Free plan never expires). Must be called immediately after
    user creation. Raises RuntimeError if the Free plan has not been seeded yet.
    """
    try:
        free_plan = SubscriptionPlan.objects.get(plan_type=SubscriptionPlan.PlanType.FREE)
    except SubscriptionPlan.DoesNotExist:
        raise RuntimeError(
            "Free plan not found. Run: python manage.py seed_plans"
        )

    return UserSubscription.objects.create( 
        user=user,
        plan=free_plan,
        status=UserSubscription.Status.ACTIVE,
        contracts_used=0,
        started_at=timezone.now(),
        expires_at=None,
    )


def get_user_subscription(user) -> UserSubscription | None:
    """
    Return the active UserSubscription for the given user, or None.
    Eagerly loads the related plan to avoid extra queries.
    """
    return (
        UserSubscription.objects
        .select_related('plan')
        .filter(user=user, status=UserSubscription.Status.ACTIVE)
        .first()
    )


def increment_contracts_used(user) -> UserSubscription:
    """
    Atomically increment contracts_used on the user's active subscription.

    Uses SELECT FOR UPDATE to prevent a race condition where two concurrent
    requests both pass the can_create_contract() check before either saves.
    Raises ValueError if the user has no active subscription or has hit their
    plan's contract limit.
    """
    with transaction.atomic():
        try:
            sub = (
                UserSubscription.objects
                .select_for_update()
                .select_related('plan')
                .get(user=user, status=UserSubscription.Status.ACTIVE)
            )
        except UserSubscription.DoesNotExist:
            raise ValueError("المستخدم لا يملك اشتراكاً نشطاً")

        if not sub.can_create_contract():
            raise ValueError(
                "لقد وصلت إلى الحد الأقصى من العقود المسموح بها في باقتك الحالية"
            )

        sub.contracts_used += 1
        sub.save(update_fields=['contracts_used', 'updated_at'])
        return sub


def upgrade_subscription(user, new_plan: SubscriptionPlan) -> UserSubscription:
    """
    Switch the user's subscription to a new plan.

    Resets contracts_used to 0, updates started_at/expires_at based on the
    new plan's duration_days, and marks the subscription ACTIVE. Uses
    SELECT FOR UPDATE to prevent concurrent upgrades on the same user.
    """
    with transaction.atomic():
        sub = UserSubscription.objects.select_for_update().get(user=user)
        sub.plan = new_plan
        sub.status = UserSubscription.Status.ACTIVE
        sub.contracts_used = 0
        sub.started_at = timezone.now()
        sub.expires_at = (
            timezone.now() + timedelta(days=new_plan.duration_days)
            if new_plan.duration_days > 0
            else None
        )
        sub.save()
        return sub
