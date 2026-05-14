# =============================================================================
# FILE: ghadi_works/for_contracts_app/urls_snippet.py
#
# WHAT THIS IS:
#   The URL entry to add to contracts/urls.py once the contracts team
#   has added ContractCreateView to contracts/views.py.
#
# WHERE TO PUT IT:
#   File: contracts/urls.py
#   Add the import and the path() entry below.
#
# CURRENT STATE OF contracts/urls.py:
#   urlpatterns = []   ← it is empty right now
#
# FINAL STATE AFTER ADDING:
#   from django.urls import path
#   from . import views
#   app_name = "contracts"
#   urlpatterns = [
#       path('create/', views.ContractCreateView.as_view(), name='create'),
#       # ... contracts team adds more URLs here
#   ]
#
# NOTE:
#   The main urls.py (Mithaq/urls.py) already has:
#       path("contracts/", include("contracts.urls"))
#   So the full URL will be:
#       POST /contracts/create/
# =============================================================================

# ── PASTE THIS INTO contracts/urls.py urlpatterns list ───────────────────────
from django.urls import path
from . import views

app_name = "contracts"

urlpatterns = [
    # Ghadi's subscription enforcement gate — must stay first
    path('create/', views.ContractCreateView.as_view(), name='create'),

    # Contracts team adds their other endpoints here:
    # path('list/',           views.ContractListView.as_view(),   name='list'),
    # path('<uuid:pk>/',      views.ContractDetailView.as_view(), name='detail'),
    # path('<uuid:pk>/sign/', views.ContractSignView.as_view(),   name='sign'),
]
