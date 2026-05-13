from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class SubscriptionPlan(models.Model):
    class PlanType(models.TextChoices):
        FREE    = 'FREE',    'مجانية'
        SINGLE  = 'SINGLE',  'عقد واحد'
        MONTHLY = 'MONTHLY', 'شهري'

    name           = models.CharField(max_length=100)
    name_ar        = models.CharField(max_length=100)
    plan_type      = models.CharField(max_length=20, choices=PlanType.choices, unique=True)
    price          = models.DecimalField(max_digits=8, decimal_places=2)
    contract_limit = models.IntegerField(help_text="-1 = unlimited")
    duration_days  = models.IntegerField(help_text="0 = forever (Free plan)")
    is_active      = models.BooleanField(default=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "باقة"
        verbose_name_plural = "الباقات"

    def __str__(self):
        return f"{self.name_ar} ({self.name})"


class UserSubscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE    = 'ACTIVE',    'نشط'
        EXPIRED   = 'EXPIRED',   'منتهي'
        CANCELLED = 'CANCELLED', 'ملغي'

    user           = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan           = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='subscriptions')
    status         = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    contracts_used = models.IntegerField(default=0)
    started_at     = models.DateTimeField()
    expires_at     = models.DateTimeField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "اشتراك"
        verbose_name_plural = "الاشتراكات"

    def __str__(self):
        return f"{self.user} — {self.plan.name_ar}"

    def can_create_contract(self) -> bool:
        """Returns True if the user is allowed to create another contract."""
        return self.plan.contract_limit == -1 or self.contracts_used < self.plan.contract_limit
