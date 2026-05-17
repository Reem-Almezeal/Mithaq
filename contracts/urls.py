from django.urls import path
from contracts.views import (
    ContractListCreateView, ContractDetailView,
    ApproveView, SignView, CancelView,
    VersionListView, VersionDetailView,
)

from audit.views import AuditTimelineView

urlpatterns = [
    # Contract CRUD
    path('', ContractListCreateView.as_view()),
    path('<uuid:pk>/', ContractDetailView.as_view()),

    # Versions
    path('<uuid:pk>/versions/', VersionListView.as_view()),
    path('<uuid:pk>/versions/<int:version_number>/', VersionDetailView.as_view()),

    # Actions
    path('<uuid:pk>/approve/', ApproveView.as_view()),
    path('<uuid:pk>/sign/', SignView.as_view()),
    path('<uuid:pk>/cancel/', CancelView.as_view()),
    
    # Audit timeline
    path('<uuid:pk>/audit/', AuditTimelineView.as_view()),
]



