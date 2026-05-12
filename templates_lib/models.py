import uuid
from django.db import models
from django.conf import settings
from core.models import SoftDeleteModel


class ContractTemplate(SoftDeleteModel):

    class Category(models.TextChoices):
        DESIGN     = 'design',     'تصميم'
        SOFTWARE   = 'software',   'برمجة'
        CONTENT    = 'content',    'محتوى'
        RETAINER   = 'retainer',   'شهري'
        SERVICES   = 'services',   'خدمات عامة'
        MARKETING  = 'marketing',  'تسويق'
        CONSULTING = 'consulting', 'استشارات'
        LEGAL      = 'legal',      'قانوني'
        OTHER      = 'other',      'أخرى'

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category   = models.CharField(max_length=50, choices=Category.choices)
    name_ar    = models.CharField(max_length=255)
    name_en    = models.CharField(max_length=255, blank=True)
    body_ar    = models.TextField()
    body_en    = models.TextField(blank=True)
    is_active  = models.BooleanField(default=True)
    created_by = models.ForeignKey(
                     settings.AUTH_USER_MODEL,
                     on_delete=models.SET_NULL,
                     null=True, blank=True
                 )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'contract_templates'
        indexes = [
            models.Index(
                fields=['category'],
                condition=models.Q(is_active=True, deleted_at__isnull=True),
                name='templates_active_idx',
            ),
        ]

    def __str__(self):
        return f"{self.name_ar} ({self.category})"