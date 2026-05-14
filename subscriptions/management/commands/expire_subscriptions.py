# =============================================================================
# subscriptions/management/commands/expire_subscriptions.py
#
# WHAT IT DOES:
#   Finds all UserSubscriptions that are ACTIVE but whose expires_at has
#   passed, sets them to EXPIRED, and writes an AuditEvent for each.
#
# HOW TO RUN MANUALLY (during development):
#   python manage.py expire_subscriptions
#
# FUTURE WORK (Ghadi) — schedule this to run automatically:
#   Option A: Server cron job
#       0 3 * * * /path/to/venv/bin/python manage.py expire_subscriptions
#       (runs every night at 3 AM)
#
#   Option B: Celery beat (when Celery is added to the project)
#       In celery.py:
#           app.conf.beat_schedule = {
#               'expire-subscriptions-nightly': {
#                   'task': 'subscriptions.tasks.expire_subscriptions',
#                   'schedule': crontab(hour=3, minute=0),
#               },
#           }
#       Then move the logic to subscriptions/tasks.py
# =============================================================================

from django.core.management.base import BaseCommand

from subscriptions.services.subscription_service import check_and_expire_subscriptions


class Command(BaseCommand):
    help = 'Expire all active subscriptions whose expiry date has passed'

    def handle(self, *args, **options):
        count = check_and_expire_subscriptions()
        if count:
            self.stdout.write(self.style.SUCCESS(f'Expired {count} subscription(s).'))
        else:
            self.stdout.write('No subscriptions to expire.')
