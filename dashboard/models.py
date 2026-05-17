from django.db import models
from django.conf import settings


class DashboardSubscription(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )

    plan_name = models.CharField(max_length=100)
    remaining_contracts = models.PositiveIntegerField(default=0)
    usage_percentage = models.PositiveIntegerField(default=0)
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
     return f"{self.user.email} - {self.plan_name}"
