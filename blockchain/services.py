from django.utils import timezone
from blockchain.models import ChainTransaction


class ChainTransactionStore:

    def create_operation(self, *, contract, contract_hash, idempotency_key):
        operation, created = ChainTransaction.objects.get_or_create(
            idempotency_key=idempotency_key,
            defaults={
                'operation_type': ChainTransaction.OperationType.CONTRACT_REGISTER,
                'contract':       contract,
                'contract_hash':  contract_hash,
            }
        )
        return operation

    def mark_submitted(self, operation_id, *, tx_hash):
        operation = self._get(operation_id)
        if not tx_hash.startswith('0x') or len(tx_hash) != 66:
            raise ValueError('tx_hash يجب أن يكون 0x-prefixed 32-byte hex')
        operation.tx_hash      = tx_hash
        operation.status       = ChainTransaction.Status.SUBMITTED
        operation.submitted_at = timezone.now()
        operation.save(update_fields=['tx_hash', 'status', 'submitted_at', 'updated_at'])
        return operation

    def mark_confirmed(self, operation_id, *, block_number):
        operation = self._get(operation_id)
        if operation.status != ChainTransaction.Status.SUBMITTED:
            raise ValueError('فقط SUBMITTED يمكن تأكيده')
        operation.block_number = block_number
        operation.status       = ChainTransaction.Status.CONFIRMED
        operation.confirmed_at = timezone.now()
        operation.save(update_fields=['block_number', 'status', 'confirmed_at', 'updated_at'])
        return operation

    def mark_failed(self, operation_id, *, error_message):
        operation = self._get(operation_id)
        operation.error_message = error_message
        operation.status        = ChainTransaction.Status.FAILED
        operation.retry_count  += 1
        operation.save(update_fields=['error_message', 'status', 'retry_count', 'updated_at'])
        return operation

    def _get(self, operation_id):
        try:
            return ChainTransaction.objects.get(pk=operation_id)
        except ChainTransaction.DoesNotExist as exc:
            raise KeyError(f'chain transaction غير موجود: {operation_id}') from exc