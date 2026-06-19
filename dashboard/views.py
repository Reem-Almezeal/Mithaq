from django.http import HttpRequest
from django.shortcuts import render
from django.db.models import Q
from django.utils import timezone

from contracts.models import Contract, ContractModificationRequest
from invitations.models import SigningInvitation
from subscriptions.models import UserSubscription


STATUS_MAP = {
    'draft':             Contract.Status.DRAFT,
    'pending_signature': Contract.Status.PENDING_SIGNATURES,
    'signed':            Contract.Status.SIGNED,
    'completed':         Contract.Status.COMPLETED,
    'cancelled':         Contract.Status.CANCELLED,
}


def dashboard_view(request: HttpRequest):
    status_filter          = request.GET.get('status', '')
    type_filter            = request.GET.get('type', '')
    date_filter            = request.GET.get('date', 'newest')
    contracts              = Contract.objects.none()
    total_contracts        = 0
    completed_contracts    = 0
    active_contracts       = 0
    pending_signatures     = 0
    draft_contracts        = 0
    rejected_contracts     = 0
    pending_approvals      = 0
    received_invitations   = 0
    under_review_contracts = 0
    completed_this_month   = 0
    avg_completion         = 0
    current_subscription   = None

    if request.user.is_authenticated:
        current_subscription = (
            UserSubscription.objects
            .select_related('plan')
            .filter(user=request.user, status=UserSubscription.Status.ACTIVE)
            .first()
        )

        # All contracts where this user is creator or party
        base_qs = Contract.objects.filter(
            Q(creator=request.user) | Q(parties__user=request.user)
        ).distinct()

        # --- Stats on unfiltered set ---
        total_contracts     = base_qs.count()
        completed_contracts = base_qs.filter(status=Contract.Status.COMPLETED).count()
        pending_signatures  = base_qs.filter(status=Contract.Status.PENDING_SIGNATURES).count()
        signed_contracts    = base_qs.filter(status=Contract.Status.SIGNED).count()
        # Active = any contract in progress (awaiting signatures OR already signed but not yet completed)
        active_contracts    = base_qs.filter(
            status__in=[Contract.Status.PENDING_SIGNATURES, Contract.Status.SIGNED]
        ).count()
        draft_contracts     = base_qs.filter(status=Contract.Status.DRAFT).count()
        rejected_contracts  = base_qs.filter(status=Contract.Status.CANCELLED).count()

        now = timezone.now()
        completed_this_month = base_qs.filter(
            status=Contract.Status.COMPLETED,
            completed_at__year=now.year,
            completed_at__month=now.month,
        ).count()

        # Modification requests on this user's contracts made by others, still awaiting review
        pending_approvals = ContractModificationRequest.objects.filter(
            contract__in=base_qs,
            status=ContractModificationRequest.Status.PENDING,
        ).exclude(requested_by=request.user).count()

        # Signing invitations addressed to this user that are still actionable
        received_invitations = SigningInvitation.objects.filter(
            Q(invitee_user=request.user) | Q(signer_email=request.user.email),
            status__in=[
                SigningInvitation.Status.PENDING,
                SigningInvitation.Status.SENT,
                SigningInvitation.Status.VIEWED,
            ],
        ).distinct().count()

        # Contracts that have at least one open modification request
        under_review_contracts = base_qs.filter(
            modification_requests__status=ContractModificationRequest.Status.PENDING
        ).distinct().count()

        if total_contracts:
            progress_sum = (
                draft_contracts     * 25 +
                pending_signatures  * 50 +
                signed_contracts    * 75 +
                completed_contracts * 100
            )
            avg_completion = round(progress_sum / total_contracts)

        # --- Apply filters for the contracts table ---
        qs = base_qs

        if status_filter and status_filter in STATUS_MAP:
            qs = qs.filter(status=STATUS_MAP[status_filter])

        if type_filter == 'created':
            qs = qs.filter(creator=request.user)
        elif type_filter == 'received':
            qs = qs.exclude(creator=request.user)

        qs = qs.order_by('created_at' if date_filter == 'oldest' else '-created_at')

        contracts = qs.select_related('creator')

    context = {
        'contracts':              contracts,
        'total_contracts':        total_contracts,
        'completed_contracts':    completed_contracts,
        'active_contracts':       active_contracts,
        'pending_signatures':     pending_signatures,
        'rejected_contracts':     rejected_contracts,
        'draft_contracts':        draft_contracts,
        'pending_approvals':      pending_approvals,
        'received_invitations':   received_invitations,
        'under_review_contracts': under_review_contracts,
        'completed_this_month':   completed_this_month,
        'avg_completion':         avg_completion,
        'current_subscription':   current_subscription,
        'selected_status':        status_filter,
        'selected_type':          type_filter,
        'selected_date':          date_filter,
    }

    return render(request, 'dashboard/dashboard.html', context)
