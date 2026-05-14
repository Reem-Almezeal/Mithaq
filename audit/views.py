from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from contracts.models import Contract
from contracts.permissions import IsContractParty
from audit.models import AuditEvent
from audit.serializers import AuditEventSerializer


class AuditTimelineView(APIView):
    permission_classes = [IsAuthenticated, IsContractParty]

    def get(self, request, pk):
        contract = get_object_or_404(Contract, pk=pk)
        self.check_object_permissions(request, contract)

        events = AuditEvent.objects.filter(
            contract=contract
        ).select_related('actor').order_by('-created_at')

        # pagination بسيطة
        page     = int(request.query_params.get('page', 1))
        per_page = 20
        start    = (page - 1) * per_page
        end      = start + per_page

        serializer = AuditEventSerializer(events[start:end], many=True)
        return Response({
            'count':   events.count(),
            'page':    page,
            'results': serializer.data,
        })