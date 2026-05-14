from blockchain.services import ChainTransactionStore


def submit_pending_operation(store: ChainTransactionStore, operation_id, tx_hash: str):
    return store.mark_submitted(operation_id, tx_hash=tx_hash)


def confirm_submitted_operation(store: ChainTransactionStore, operation_id, block_number: int):
    return store.mark_confirmed(operation_id, block_number=block_number)