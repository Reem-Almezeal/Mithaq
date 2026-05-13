# =============================================================================
# FILE: ghadi_works/for_contracts_app/services/contract_service.py
#
# WHAT THIS IS:
#   The service layer for contract creation with subscription enforcement.
#   This is Ghadi's code that belongs inside the contracts app once the
#   contracts team has finished their work.
#
# WHERE TO PUT IT:
#   Create folder:  contracts/services/           (new directory)
#   Create file:    contracts/services/__init__.py (empty, see __init__.py)
#   Create file:    contracts/services/contract_service.py  ← this file
#
# HOW IT CONNECTS TO THE CONTRACTS TEAM'S WORK:
#   1. The contracts team will define their contract creation logic
#      (validation, template selection, parties, milestones, etc.)
#   2. Ghadi wraps their creation logic by calling check_contract_limit(user)
#      AT THE START — before any DB write.
#   3. If the user has no subscription or hit their limit → PermissionDenied
#      is raised and the contract is NOT created.
#   4. If the check passes → contracts_used is incremented → contract is created.
#
# WHAT TO TELL THE CONTRACTS TEAM:
#   "In your contract creation function, call check_contract_limit(user)
#    as the very first line. If it raises PermissionDenied, let it bubble up.
#    The view will catch it and return HTTP 403 to the frontend."
#
# DEPENDENCIES (both already exist):
#   - contracts/models.py  → Contract, ContractParty
#   - subscriptions/services/subscription_service.py → check_contract_limit
# =============================================================================

import logging

from contracts.models import Contract, ContractParty
from subscriptions.services.subscription_service import check_contract_limit

logger = logging.getLogger(__name__)


def create_contract(user, title_ar: str, title_en: str = '', description_ar: str = '') -> Contract:
    """
    Create a new contract for the given user, enforcing subscription limits.

    This is the ENTRY POINT for all contract creation. It must always be
    the first thing called before any contract data is written to the DB.

    Flow:
        1. check_contract_limit(user) runs first:
             - No subscription?  → PermissionDenied ("لا يوجد اشتراك نشط...")
             - Subscription expired? → PermissionDenied ("انتهت صلاحية اشتراكك...")
             - Limit reached?    → PermissionDenied ("لقد استنفدت عدد العقود...")
             - Limit OK?         → contracts_used incremented atomically, continues
        2. Contract is created in the DB.
        3. Creator is added as a ContractParty with role=CREATOR.

    The contracts team can extend this function to add their own logic
    (template selection, milestones, etc.) AFTER the check_contract_limit call.

    Raises:
        PermissionDenied: if the user cannot create a contract.
    Returns:
        The newly created Contract instance.
    """
    # ── SUBSCRIPTION GATE ────────────────────────────────────────────────────
    # This line must stay first. If it raises, nothing below runs.
    check_contract_limit(user)
    # ─────────────────────────────────────────────────────────────────────────

    contract = Contract.objects.create(
        title_ar=title_ar,
        title_en=title_en,
        description_ar=description_ar,
        creator=user,
    )

    # Add the creator as a party automatically
    ContractParty.objects.create(
        contract=contract,
        user=user,
        role=ContractParty.Role.CREATOR,
    )

    logger.info('Contract created | id=%s user=%s', contract.id, user.id)
    return contract
