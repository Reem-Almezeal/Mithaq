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
