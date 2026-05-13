import hashlib
import json

from django.db import transaction
from django.core.exceptions import ValidationError

from contracts.models import Contract, ContractParty
from signatures.models import Signature


class SigningService:

    @staticmethod
    def compute_canonical_hash(version):
        """
        يبني JSON محدد الترتيب من بنود النسخة ثم يحسب SHA-256.
        نفس البيانات = نفس الـ hash دائماً.
        """
        clauses = version.clauses.order_by('order_index')

        payload = {
            'contract_id':    str(version.contract.id),
            'version_number': version.version_number,
            'title_ar':       version.contract.title_ar,
            'clauses': [
                {
                    'order':      c.order_index,
                    'type':       c.clause_type,
                    'title_ar':   c.title_ar,
                    'content_ar': c.content_ar,
                    'content_en': c.content_en,
                }
                for c in clauses
            ]
        }

        # sort_keys=True ضروري — يضمن نفس الترتيب دائماً
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    # ──────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def validate_and_sign(contract, signer, submitted_hash, request=None):
        """
        contract      = Contract instance
        signer        = User instance
        submitted_hash = الـ hash اللي أرسله المستخدم من الـ frontend
        request       = HttpRequest (اختياري — لتسجيل الـ IP)
        """

        # ── 1. select_for_update — يمنع race conditions ───────
        contract = Contract.objects.select_for_update().get(pk=contract.pk)

        # ── 2. تحقق من حالة العقد ─────────────────────────────
        if contract.status != Contract.Status.PENDING_SIGNATURES:
            raise ValidationError('العقد مو في مرحلة التوقيع')

        # ── 3. تحقق أن الـ signer طرف في العقد ───────────────
        try:
            party = ContractParty.objects.get(contract=contract, user=signer)
        except ContractParty.DoesNotExist:
            raise ValidationError('لست طرفاً في هذا العقد')

        # ── 4. تحقق أنه ما وقّع مسبقاً ───────────────────────
        if Signature.objects.filter(contract=contract, signer=signer).exists():
            raise ValidationError('وقّعت على هذا العقد مسبقاً')

        # ── 5. تحقق أن الـ hash متطابق ────────────────────────
        if submitted_hash != contract.canonical_hash:
            raise ValidationError('الـ hash غير متطابق — العقد تغيّر')

        # ── 6. سجّل التوقيع ───────────────────────────────────
        ip_address = None
        user_agent = ''
        if request:
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')

        signature = Signature.objects.create(
            contract         = contract,
            contract_version = contract.current_version,
            signer           = signer,
            signed_hash      = submitted_hash,
            ip_address       = ip_address,
            user_agent       = user_agent,
        )

        # ── 7. تحقق إذا كل الأطراف وقّعوا ────────────────────
        total_parties   = contract.parties.count()
        total_signatures = Signature.objects.filter(contract=contract).count()

        if total_signatures == total_parties:
            contract.status = Contract.Status.SIGNED
            contract.save(update_fields=['status', 'updated_at'])

            # ← هنا لاحقاً نضيف: trigger blockchain task

        return signature