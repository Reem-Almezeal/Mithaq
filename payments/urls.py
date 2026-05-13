# =============================================================================
# payments/urls.py   →   mounted at: api/payments/ (Mithaq/urls.py)
#
# Full URL map:
#   AUTHENTICATED:
#       POST /api/payments/checkout/<plan_id>/  ← JS fetch() from checkout.html
#
#   PUBLIC (Moyasar redirects here after payment):
#       GET  /api/payments/callback/            ← Moyasar calls this
#       GET  /api/payments/success/             ← User sees this after success
#       GET  /api/payments/failed/              ← User sees this after failure
#
#   CALLBACK URL in .env:
#       MOYASAR_CALLBACK_URL=http://localhost:8000/api/payments/callback/
#       Update this to the real domain before going to production.
#
# FUTURE WORK: add GET /api/payments/history/ for payment records list
# =============================================================================

from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path('checkout/<int:plan_id>/', views.CheckoutView.as_view(),        name='checkout'),
    path('callback/',               views.PaymentCallbackView.as_view(), name='callback'),
    path('success/',                views.payment_success,                name='success'),
    path('failed/',                 views.payment_failed,                 name='failed'),
]
