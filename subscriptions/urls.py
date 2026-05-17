# =============================================================================
# subscriptions/urls.py   →   mounted at: api/subscriptions/ (Mithaq/urls.py)
#
# Full URL map:
#   PUBLIC  (no auth):
#       GET  /api/subscriptions/plans/
#       GET  /api/subscriptions/plans-page/           ← HTML page
#       GET  /api/subscriptions/checkout-page/<id>/   ← HTML page
#
#   AUTHENTICATED:
#       GET  /api/subscriptions/status/
#       GET  /api/subscriptions/upgrade-options/
#
# FUTURE WORK: add more URLs here as new views are built
# =============================================================================

from django.urls import path

from . import views

app_name = "subscriptions"

urlpatterns = [
    # API endpoints
    path('plans/',           views.PlanListView.as_view(),          name='plans'),
    path('status/',          views.SubscriptionStatusView.as_view(), name='status'),
    path('upgrade-options/', views.UpgradeOptionsView.as_view(),     name='upgrade_options'),
    # Template pages
    path('plans-page/',                       views.plans_page,    name='plans_page'),
    path('checkout-page/<int:plan_id>/',      views.checkout_page, name='checkout_page'),
]
