from rest_framework import serializers
from audit.models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(
        source='actor.full_name',
        default='النظام',
        read_only=True
    )

    class Meta:
        model  = AuditEvent
        fields = [
            'id', 'event_type', 'actor_name',
            'payload', 'ip_address', 'created_at',
        ]