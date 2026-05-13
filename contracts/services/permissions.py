from rest_framework.permissions import BasePermission
from rest_framework.exceptions import NotFound
from contracts.models import ContractParty
from signatures.models import Signature


class IsContractParty(BasePermission):
    """
    يتحقق أن المستخدم طرف في العقد.
    يرفع 404 مش 403 — يمنع تعداد العقود.
    """
    def has_object_permission(self, request, view, obj):
        is_party = ContractParty.objects.filter(
            contract=obj,
            user=request.user
        ).exists()

        if not is_party:
            raise NotFound('العقد غير موجود')

        return True


class IsContractCreator(BasePermission):
    """
    يتحقق أن المستخدم هو منشئ العقد.
    """
    def has_object_permission(self, request, view, obj):
        is_party = ContractParty.objects.filter(
            contract=obj,
            user=request.user
        ).exists()

        if not is_party:
            raise NotFound('العقد غير موجود')

        return obj.creator == request.user


class CanEditClauses(BasePermission):
    """
    طرف في العقد + حالة DRAFT فقط.
    """
    def has_object_permission(self, request, view, obj):
        is_party = ContractParty.objects.filter(
            contract=obj,
            user=request.user
        ).exists()

        if not is_party:
            raise NotFound('العقد غير موجود')

        return obj.status == 'DRAFT'


class CanSign(BasePermission):
    """
    طرف في العقد + حالة PENDING_SIGNATURES + ما وقّع بعد.
    """
    def has_object_permission(self, request, view, obj):
        is_party = ContractParty.objects.filter(
            contract=obj,
            user=request.user
        ).exists()

        if not is_party:
            raise NotFound('العقد غير موجود')

        if obj.status != 'PENDING_SIGNATURES':
            return False

        already_signed = Signature.objects.filter(
            contract=obj,
            signer=request.user
        ).exists()

        return not already_signed