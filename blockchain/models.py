import uuid
from django.db import models


class ChainTransaction(models.Model):

    class OperationType(models.TextChoices):
        CONTRACT_REGISTER = 'CONTRACT_REGISTER', 'تسجيل عقد'

    class Status(models.TextChoices):
        PENDING   = 'PENDING',   'معلّق'
        SUBMITTED = 'SUBMITTED', 'مُرسَل'
        CONFIRMED = 'CONFIRMED', 'مؤكّد'
        FAILED    = 'FAILED',    'فشل'

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    operation_type  = models.CharField(max_length=50, choices=OperationType.choices)
    contract        = models.ForeignKey(
                          'contracts.Contract',        # ← string reference
                          on_delete=models.RESTRICT,
                          related_name='chain_transactions'
                      )
    status          = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    idempotency_key = models.CharField(max_length=100, unique=True)
    contract_hash   = models.CharField(max_length=64)
    tx_hash         = models.CharField(max_length=66, blank=True)
    block_number    = models.BigIntegerField(null=True, blank=True)
    retry_count     = models.PositiveIntegerField(default=0)
    error_message   = models.TextField(blank=True)
    submitted_at    = models.DateTimeField(null=True, blank=True)
    confirmed_at    = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chain_transactions'
        indexes = [
            models.Index(fields=['status', 'created_at'],    name='chain_pending_idx'),
            models.Index(fields=['contract', '-created_at'], name='chain_contract_idx'),
        ]

    def __str__(self):
        return f"{self.contract.title_ar} — {self.status}"