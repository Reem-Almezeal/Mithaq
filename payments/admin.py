from django.contrib import admin

from .models import PaymentRecord


@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'amount', 'currency', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'currency')
    search_fields = ('user__email', 'moyasar_payment_id')
    raw_id_fields = ('user',)
    readonly_fields = ('moyasar_payment_id', 'created_at', 'updated_at')
