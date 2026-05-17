# =============================================================================
# subscriptions/services/subscription_service.py
# OWNED BY: Ghadi
#
# PURPOSE:
#   All subscription business logic lives here.
#   Views and other apps call these functions — they never touch models directly.
#
# HOW IT CONNECTS TO OTHER APPS:
#
#   accounts/views.py → assign_free_plan(user)
#       Called right after User.objects.create_user() in sign_up().
#       Every new user automatically gets the Free plan (1 contract limit).
#
#   payments/services/moyasar_service.py → activate_subscription(user, plan)
#       Called inside handle_callback() after Moyasar confirms a payment.
#       Upgrades the user's plan and resets contracts_used to 0.
#
#   contracts/services/contract_workflow.py → check_contract_limit(user)
#       *** THIS INTEGRATION IS PENDING — see FUTURE WORK below ***
#       Must be called as the first line of ContractWorkflowService.create_contract()
#       before any DB write. If the user is over their limit → PermissionDenied (403).
#
# FUTURE WORK (Ghadi):
#
#   [1] Hook check_contract_limit into the contracts workflow.
#       File:   contracts/services/contract_workflow.py
#       Class:  ContractWorkflowService
#       Method: create_contract(creator, data)
#       → Add these 2 lines right before "# ── 1. Validation ──" (line ~29):
#
#           from subscriptions.services.subscription_service import check_contract_limit
#           check_contract_limit(creator)
#
#       Full snippet + explanation: ghadi_works/for_contracts_app/
#
#   [2] Ask audit team to add 2 EventTypes to audit/models.py:
#       SUBSCRIPTION_EXPIRED   = 'SUBSCRIPTION_EXPIRED',   'اشتراك انتهى'
#       CONTRACT_LIMIT_CHECKED = 'CONTRACT_LIMIT_CHECKED',  'فُحص حد العقود'
#       Full snippet: ghadi_works/for_audit_app/event_types.py
#       Until they add these, both functions silently skip the audit write (try/except).
#
#   [3] Schedule expire_subscriptions to run nightly:
#       python manage.py expire_subscriptions
#       Add to server cron or Celery beat later in the project.
# =============================================================================

import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from subscriptions.models import SubscriptionPlan, UserSubscription

logger = logging.getLogger(__name__)


# ── Called from: accounts/views.py → sign_up() ────────────────────────────────
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


# ── Called from: everywhere that needs to know the user's current plan ─────────
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


# ── Internal helper — prefer check_contract_limit() for user-facing enforcement ─
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


# ── Called from: payments/services/moyasar_service.py → handle_callback() ──────
def activate_subscription(user, plan: SubscriptionPlan) -> UserSubscription:
    """
    Activate or upgrade a user's subscription after a successful payment.

    If the user already has a UserSubscription it is updated in place; otherwise
    a new one is created. contracts_used is reset to 0 on every activation.
    expires_at is computed from plan.duration_days (None when duration_days == 0,
    meaning the plan never expires — e.g. the Free plan).

    Uses SELECT FOR UPDATE to prevent concurrent activations for the same user.
    Returns the saved UserSubscription.
    """
    with transaction.atomic():
        try:
            sub = UserSubscription.objects.select_for_update().get(user=user)
            sub.plan = plan
            sub.status = UserSubscription.Status.ACTIVE
            sub.contracts_used = 0
            sub.started_at = timezone.now()
            sub.expires_at = (
                timezone.now() + timedelta(days=plan.duration_days)
                if plan.duration_days > 0
                else None
            )
            sub.save()
        except UserSubscription.DoesNotExist:
            sub = UserSubscription.objects.create(
                user=user,
                plan=plan,
                status=UserSubscription.Status.ACTIVE,
                contracts_used=0,
                started_at=timezone.now(),
                expires_at=(
                    timezone.now() + timedelta(days=plan.duration_days)
                    if plan.duration_days > 0
                    else None
                ),
            )
    try:
        from audit.models import AuditEvent
        AuditEvent.objects.create(
            actor=user,
            event_type=AuditEvent.EventType.SUBSCRIPTION_ACTIVATED,
            payload={
                'plan': plan.name,
                'plan_ar': plan.name_ar,
                'plan_type': plan.plan_type,
            },
        )
    except Exception as exc:
        logger.warning('AuditEvent write failed for subscription activation: %s', exc)

    return sub


# ── PENDING INTEGRATION: needs to be wired into contracts/services/contract_workflow.py
# ── See FUTURE WORK [1] at the top of this file for the exact lines to add ─────
def check_contract_limit(user) -> UserSubscription:
    """
    Enforce contract creation limits before allowing a new contract.

    Unlike increment_contracts_used (which raises ValueError), this function
    raises PermissionDenied so views can return HTTP 403 directly to the user.

    Checks subscription existence and status first (without a lock), then
    acquires SELECT FOR UPDATE before incrementing contracts_used to prevent
    a race condition under concurrent requests.

    Returns the updated UserSubscription on success.
    """
    from django.core.exceptions import PermissionDenied

    try:
        sub = UserSubscription.objects.select_related('plan').get(user=user)
    except UserSubscription.DoesNotExist:
        raise PermissionDenied("لا يوجد اشتراك نشط. يرجى اختيار خطة.")

    if sub.status == UserSubscription.Status.EXPIRED:
        raise PermissionDenied("انتهت صلاحية اشتراكك. يرجى التجديد.")

    with transaction.atomic():
        sub = (
            UserSubscription.objects
            .select_for_update()
            .select_related('plan')
            .get(user=user)
        )

        if sub.status != UserSubscription.Status.ACTIVE:
            raise PermissionDenied("لا يوجد اشتراك نشط. يرجى اختيار خطة.")

        if not sub.can_create_contract():
            raise PermissionDenied("لقد استنفدت عدد العقود المسموح به في خطتك الحالية.")

        sub.contracts_used += 1
        sub.save(update_fields=['contracts_used', 'updated_at'])

    try:
        from audit.models import AuditEvent
        AuditEvent.objects.create(
            actor=user,
            event_type=AuditEvent.EventType.CONTRACT_LIMIT_CHECKED,
            payload={
                'contracts_used': sub.contracts_used,
                'contract_limit': sub.plan.contract_limit,
            },
        )
    except Exception as exc:
        logger.warning('AuditEvent write failed for contract limit check: %s', exc)

    return sub


# ── Run via: python manage.py expire_subscriptions (nightly cron later) ────────
def check_and_expire_subscriptions() -> int:
    """
    Expire all active subscriptions whose expires_at timestamp has passed.

    Queries for ACTIVE subscriptions with a non-null expires_at <= now(),
    sets each to EXPIRED, and writes an AuditEvent per subscription.
    Intended to be called from the expire_subscriptions management command
    or a scheduled task (Celery beat, cron).

    Returns the count of subscriptions that were expired.
    """
    now = timezone.now()
    due = UserSubscription.objects.filter(
        status=UserSubscription.Status.ACTIVE,
        expires_at__isnull=False,
        expires_at__lte=now,
    ).select_related('user', 'plan')

    count = 0
    for sub in due:
        sub.status = UserSubscription.Status.EXPIRED
        sub.save(update_fields=['status', 'updated_at'])
        count += 1

        try:
            from audit.models import AuditEvent
            AuditEvent.objects.create(
                actor=sub.user,
                event_type=AuditEvent.EventType.SUBSCRIPTION_EXPIRED,
                payload={
                    'plan': sub.plan.name,
                    'expired_at': now.isoformat(),
                },
            )
        except Exception as exc:
            logger.warning('AuditEvent write failed for subscription expiry: %s', exc)

    return count


# ── Available for future use (e.g. admin-initiated plan change) ────────────────
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
