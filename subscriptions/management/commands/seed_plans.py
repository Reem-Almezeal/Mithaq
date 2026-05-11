from django.core.management.base import BaseCommand

from subscriptions.models import SubscriptionPlan

PLANS = [
    {
        'name': 'Free Plan',
        'name_ar': 'مجانية',
        'plan_type': SubscriptionPlan.PlanType.FREE,
        'price': 0,
        'contract_limit': 1,
        'duration_days': 0,
    },
    {
        'name': 'Single Contract',
        'name_ar': 'عقد واحد',
        'plan_type': SubscriptionPlan.PlanType.SINGLE,
        'price': 29,
        'contract_limit': 1,
        'duration_days': 30,
    },
    {
        'name': 'Monthly Plan',
        'name_ar': 'الباقة الشهرية',
        'plan_type': SubscriptionPlan.PlanType.MONTHLY,
        'price': 99,
        'contract_limit': 10,
        'duration_days': 30,
    },
]


class Command(BaseCommand):
    help = 'Seed the database with the default subscription plans'

    def handle(self, *args, **options):
        created_count = 0

        for plan_data in PLANS:
            _, created = SubscriptionPlan.objects.get_or_create(
                plan_type=plan_data['plan_type'],
                defaults=plan_data,
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  [OK] Created: {plan_data["name"]}'))
            else:
                self.stdout.write(f'  [--] Already exists: {plan_data["name"]}')

        self.stdout.write(
            self.style.SUCCESS(f'\nDone: {created_count} plan(s) created.')
            if created_count
            else '\nDone: all plans already exist.'
        )
