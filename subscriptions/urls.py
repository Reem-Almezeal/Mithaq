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
