from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path('checkout/<int:plan_id>/', views.CheckoutView.as_view(),        name='checkout'),
    path('callback/',               views.PaymentCallbackView.as_view(), name='callback'),
    path('success/',                views.payment_success,                name='success'),
    path('failed/',                 views.payment_failed,                 name='failed'),
]
