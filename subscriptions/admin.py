from django.contrib import admin

from .models import PaymentRecord, SubscriptionPlan, UserSubscription


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'name', 'plan_type', 'price', 'contract_limit', 'duration_days', 'is_active')
    list_filter = ('plan_type', 'is_active')
    search_fields = ('name', 'name_ar')
    ordering = ('price',)


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'contracts_used', 'started_at', 'expires_at', 'updated_at')
    list_filter = ('status', 'plan')
    search_fields = ('user__username', 'user__email')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'amount', 'currency', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'currency')
    search_fields = ('user__username', 'user__email', 'moyasar_payment_id')
    raw_id_fields = ('user',)
    readonly_fields = ('moyasar_payment_id', 'created_at', 'updated_at')
