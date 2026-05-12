from django.shortcuts import render
from dashboard.models import DashboardSubscription


def dashboard_view(request):
    contracts = []

    status = request.GET.get("status")
    contract_type = request.GET.get("type")
    date_filter = request.GET.get("date")

    current_subscription = None

    if request.user.is_authenticated:
        current_subscription = (
            DashboardSubscription.objects
            .filter(user=request.user, is_active=True)
            .first()
        )

    context = {
        "contracts": contracts,

        "total_contracts": 0,
        "completed_contracts": 0,
        "active_contracts": 0,
        "pending_signatures": 0,
        "rejected_contracts": 0,
        "draft_contracts": 0,

        "pending_approvals": 0,
        "received_invitations": 0,
        "under_review_contracts": 0,
        "completed_this_month": 0,
        "avg_completion": 0,

        "current_subscription": current_subscription,

        "selected_status": status,
        "selected_type": contract_type,
        "selected_date": date_filter,
    }

    return render(request, "dashboard/dashboard.html", context)