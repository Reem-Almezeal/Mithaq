from django.urls import path

from . import views

app_name = "subscriptions"

urlpatterns = [
    path('plans/',  views.PlanListView.as_view(),          name='plans'),
    path('status/', views.SubscriptionStatusView.as_view(), name='status'),
]
