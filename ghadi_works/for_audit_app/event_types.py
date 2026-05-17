# =============================================================================
# FILE: ghadi_works/for_audit_app/event_types.py
#
# WHAT THIS IS:
#   Two new AuditEvent types that Ghadi needs added to the audit app.
#   The audit app belongs to a teammate — ask them to add these lines.
#
# WHERE TO PUT IT:
#   File:  audit/models.py
#   Class: AuditEvent.EventType (the TextChoices class inside AuditEvent)
#   Place: in the Subscription section, right after SUBSCRIPTION_ACTIVATED
#
# HOW TO ADD IT — tell your teammate to paste these two lines:
#
#   SUBSCRIPTION_EXPIRED   = 'SUBSCRIPTION_EXPIRED',   'اشتراك انتهى'
#   CONTRACT_LIMIT_CHECKED = 'CONTRACT_LIMIT_CHECKED',  'فُحص حد العقود'
#
# EXACT LOCATION (show them this diff):
#
#   # ── Subscription ──────────────────────
#   SUBSCRIPTION_ACTIVATED  = 'SUBSCRIPTION_ACTIVATED',  'اشتراك فُعِّل'
# + SUBSCRIPTION_EXPIRED    = 'SUBSCRIPTION_EXPIRED',    'اشتراك انتهى'
# + CONTRACT_LIMIT_CHECKED  = 'CONTRACT_LIMIT_CHECKED',  'فُحص حد العقود'
#   # ── Contract ──────────────────────────
#
# WHY THESE ARE NEEDED:
#   - SUBSCRIPTION_EXPIRED:
#       Written by check_and_expire_subscriptions() in
#       subscriptions/services/subscription_service.py
#       whenever a subscription's expires_at passes.
#       Lets the audit trail show when a user's subscription expired.
#
#   - CONTRACT_LIMIT_CHECKED:
#       Written by check_contract_limit() in
#       subscriptions/services/subscription_service.py
#       every time a user successfully creates a contract (after the
#       limit check passes). Tracks contract usage in the audit log.
#
# IMPORTANT:
#   No migration is needed. Django does NOT enforce TextChoices at the
#   database level — they are Python-only. Adding them is a one-line
#   change with zero risk.
#
#   Until the teammate adds these, both service functions will silently
#   skip writing the audit event (wrapped in try/except) — the app will
#   NOT crash.
# =============================================================================

# Lines to add to audit/models.py → AuditEvent.EventType:

SUBSCRIPTION_EXPIRED   = 'SUBSCRIPTION_EXPIRED',   'اشتراك انتهى'
CONTRACT_LIMIT_CHECKED = 'CONTRACT_LIMIT_CHECKED',  'فُحص حد العقود'
