import uuid
from django.db import models
from django.conf import settings


class Signature(models.Model):

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract         = models.ForeignKey(
                           'contracts.Contract',
                           on_delete=models.RESTRICT,
                           related_name='signatures'
                       )
    contract_version = models.ForeignKey(
                           'contracts.ContractVersion',
                           on_delete=models.RESTRICT,
                           related_name='signatures'
                       )
    signer           = models.ForeignKey(
                           settings.AUTH_USER_MODEL,
                           on_delete=models.RESTRICT,
                           related_name='signatures'
                       )
    signed_hash      = models.CharField(max_length=64)
    ip_address       = models.GenericIPAddressField(blank=True, null=True)
    user_agent       = models.TextField(blank=True)
    signed_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'signatures'
        constraints = [
            models.UniqueConstraint(
                fields=['contract', 'signer'],
                name='signatures_unique_per_party',
            ),
        ]
        indexes = [
            models.Index(fields=['contract', 'signed_at'], name='signatures_contract_idx'),
            models.Index(fields=['signer'],                name='signatures_signer_idx'),
        ]

    def __str__(self):
        return f"{self.signer} وقّع على {self.contract.title_ar}"