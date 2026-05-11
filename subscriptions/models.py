from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class SubscriptionPlan(models.Model):
    class PlanType(models.TextChoices):
        FREE = 'FREE', 'مجانية'
        SINGLE = 'SINGLE', 'عقد واحد'
        MONTHLY = 'MONTHLY', 'شهري'

    name = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PlanType.choices, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    contract_limit = models.IntegerField(help_text="-1 = unlimited")
    duration_days = models.IntegerField(help_text="0 = forever (Free plan)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "باقة"
        verbose_name_plural = "الباقات"

    def __str__(self):
        return f"{self.name_ar} ({self.name})"


class UserSubscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'نشط'
        EXPIRED = 'EXPIRED', 'منتهي'
        CANCELLED = 'CANCELLED', 'ملغي'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    contracts_used = models.IntegerField(default=0)
    started_at = models.DateTimeField()
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "اشتراك"
        verbose_name_plural = "الاشتراكات"

    def __str__(self):
        return f"{self.user.username} — {self.plan.name_ar}"

    def can_create_contract(self) -> bool:
        """Returns True if the user is allowed to create another contract."""
        return self.plan.contract_limit == -1 or self.contracts_used < self.plan.contract_limit


class PaymentRecord(models.Model):
    class Status(models.TextChoices):
        INITIATED = 'INITIATED', 'بدأ'
        PAID = 'PAID', 'مدفوع'
        FAILED = 'FAILED', 'فشل'
        REFUNDED = 'REFUNDED', 'مسترد'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='payments')
    moyasar_payment_id = models.CharField(max_length=200, unique=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=10, default='SAR')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INITIATED)
    payment_method = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "سجل دفع"
        verbose_name_plural = "سجلات الدفع"

    def __str__(self):
        return f"{self.user.username} — {self.amount} {self.currency} ({self.status})"

 
