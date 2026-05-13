from rest_framework.permissions import BasePermission
from rest_framework.exceptions import NotFound
from contracts.models import ContractParty
from signatures.models import Signature


class IsContractParty(BasePermission):
    def has_object_permission(self, request, view, obj):
        is_party = ContractParty.objects.filter(
            contract=obj,
            user=request.user
        ).exists()

        if not is_party:
            raise NotFound('العقد غير موجود')

        return True


class IsContractCreator(BasePermission):
    def has_object_permission(self, request, view, obj):
        is_party = ContractParty.objects.filter(
            contract=obj,
            user=request.user
        ).exists()

        if not is_party:
            raise NotFound('العقد غير موجود')

        return obj.creator == request.user


class CanEditClauses(BasePermission):
    def has_object_permission(self, request, view, obj):
        is_party = ContractParty.objects.filter(
            contract=obj,
            user=request.user
        ).exists()

        if not is_party:
            raise NotFound('العقد غير موجود')

        return obj.status == 'DRAFT'


class CanSign(BasePermission):
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