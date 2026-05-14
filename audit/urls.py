from django.urls import path
from audit.views import AuditTimelineView

urlpatterns = [
    path('<uuid:pk>/audit/', AuditTimelineView.as_view()),
]