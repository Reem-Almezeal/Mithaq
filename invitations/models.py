import uuid
import secrets
from django.db import models
from django.conf import settings
from django.utils import timezone



class Invitation(models.Model):

    class Status(models.TextChoices):
        PENDING  = 'PENDING',  'معلّق'
        ACCEPTED = 'ACCEPTED', 'مقبول'
        DECLINED = 'DECLINED', 'مرفوض'
        EXPIRED  = 'EXPIRED',  'منتهي'

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract       = models.ForeignKey(
                         'contracts.Contract',
                         on_delete=models.CASCADE,
                         related_name='invitations'
                     )
    inviter        = models.ForeignKey(
                         settings.AUTH_USER_MODEL,
                         on_delete=models.CASCADE,
                         related_name='sent_invitations'
                     )
    invitee_email  = models.EmailField()
    token          = models.CharField(max_length=64, unique=True, editable=False)
    status         = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    expires_at     = models.DateTimeField()
    accepted_at    = models.DateTimeField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'invitations'
        unique_together = [['contract', 'invitee_email']]  # ← ما يُدعى نفس الشخص مرتين
        indexes = [
            models.Index(fields=['token'],  name='invitations_token_idx'),
            models.Index(fields=['status'], name='invitations_status_idx'),
        ]

    def save(self, *args, **kwargs):
        # يولّد الـ token تلقائياً عند الإنشاء فقط
        if not self.token:
            self.token = secrets.token_urlsafe(48)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return self.status == self.Status.PENDING and not self.is_expired

    def __str__(self):
        return f"دعوة لـ {self.invitee_email} — {self.contract.title_ar} [{self.status}]"
