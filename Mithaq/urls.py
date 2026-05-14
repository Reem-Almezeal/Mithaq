from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

urlpatterns = [
    path("", core_views.home, name="home"),
    path("admin/", admin.site.urls),

    path("accounts/", include("accounts.urls")),
    path('api/contracts/', include('contracts.urls')),
    path('api/contracts/', include('audit.urls')),
    path("milestones/", include("milestones.urls")),
    path("signatures/", include("signatures.urls")),
    path("audit/", include("audit.urls")),
    path("blockchain/", include("blockchain.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("notifications/", include("notifications.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/subscriptions/", include("subscriptions.urls")),
    path("wallet/", include("wallet.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
