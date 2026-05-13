from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class PaymentRecord(models.Model):
    class Status(models.TextChoices):
        INITIATED = 'INITIATED', 'بدأ'
        PAID      = 'PAID',      'مدفوع'
        FAILED    = 'FAILED',    'فشل'
        REFUNDED  = 'REFUNDED',  'مسترد'

    user               = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    # String reference avoids a direct import from subscriptions at module load time
    plan               = models.ForeignKey('subscriptions.SubscriptionPlan', on_delete=models.PROTECT, related_name='payments')
    moyasar_payment_id = models.CharField(max_length=200, unique=True)
    amount             = models.DecimalField(max_digits=8, decimal_places=2)
    currency           = models.CharField(max_length=10, default='SAR')
    status             = models.CharField(max_length=20, choices=Status.choices, default=Status.INITIATED)
    payment_method     = models.CharField(max_length=50, null=True, blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "سجل دفع"
        verbose_name_plural = "سجلات الدفع"

    def __str__(self):
        return f"{self.user} — {self.amount} {self.currency} ({self.status})"
