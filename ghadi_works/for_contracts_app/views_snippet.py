# =============================================================================
# FILE: ghadi_works/for_contracts_app/views_snippet.py
#
# WHAT THIS IS:
#   A new API view that the contracts team needs to add to contracts/views.py.
#   It handles POST /contracts/create/ and enforces subscription limits.
#
# WHERE TO PUT IT:
#   File: contracts/views.py
#   Add these imports at the top and paste the ContractCreateView class.
#
# HOW IT WORKS:
#   1. User POSTs to /contracts/create/ with { "title_ar": "..." }
#   2. The view calls create_contract() from contract_service.py
#   3. contract_service.py calls check_contract_limit(user) first:
#        → If user has no subscription → 403 "لا يوجد اشتراك نشط..."
#        → If subscription expired     → 403 "انتهت صلاحية اشتراكك..."
#        → If limit reached            → 403 "لقد استنفدت عدد العقود..."
#        → If OK                       → creates contract, returns 201
#   4. The view NEVER catches PermissionDenied itself —
#      it just lets it bubble up from the service. Views stay thin.
#
# WHAT TO TELL THE CONTRACTS TEAM:
#   "Replace the placeholder in contracts/views.py with this view.
#    You can extend ContractCreateView to accept more fields (template,
#    clauses, milestones) — just pass them to create_contract().
#    The subscription check is already handled inside the service."
# =============================================================================

# ── ADD THESE IMPORTS TO contracts/views.py ──────────────────────────────────
import logging

from django.core.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services.contract_service import create_contract

logger = logging.getLogger(__name__)
# ─────────────────────────────────────────────────────────────────────────────


class ContractCreateView(APIView):
    """
    POST /contracts/create/

    Create a new contract for the authenticated user.
    Returns 403 with an Arabic error message if the user's subscription
    does not allow creating more contracts.

    Request body (JSON):
        {
            "title_ar":       "عنوان العقد",       # required
            "title_en":       "Contract title",    # optional
            "description_ar": "وصف العقد"          # optional
        }

    Responses:
        201  { "id": "uuid", "title_ar": "..." }
        400  { "error": "عنوان العقد بالعربية مطلوب" }
        403  { "error": "<Arabic subscription error>" }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        title_ar = request.data.get('title_ar', '').strip()
        if not title_ar:
            return Response(
                {'error': 'عنوان العقد بالعربية مطلوب'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            contract = create_contract(
                user=request.user,
                title_ar=title_ar,
                title_en=request.data.get('title_en', ''),
                description_ar=request.data.get('description_ar', ''),
            )
        except PermissionDenied as exc:
            # The Arabic error message comes from check_contract_limit()
            # in subscriptions/services/subscription_service.py
            return Response(
                {'error': str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {'id': str(contract.id), 'title_ar': contract.title_ar},
            status=status.HTTP_201_CREATED,
        )
