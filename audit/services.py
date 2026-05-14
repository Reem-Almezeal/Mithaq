from audit.models import AuditEvent


def log_event(contract, event_type, actor=None, payload=None, request=None):
    """
    نقطة الدخول الوحيدة لتسجيل الأحداث.
    تُستدعى من contracts/services/ فقط — لا من views.
    """
    ip_address = None
    user_agent = ''

    if request:
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

    AuditEvent.objects.create(
        contract   = contract,
        event_type = event_type,
        actor      = actor,
        payload    = payload or {},
        ip_address = ip_address,
        user_agent = user_agent,
    )