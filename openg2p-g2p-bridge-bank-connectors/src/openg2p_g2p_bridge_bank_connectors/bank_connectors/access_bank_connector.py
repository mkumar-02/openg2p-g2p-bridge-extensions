import logging
from typing import List

import httpx
from openg2p_g2p_bridge_models.models import (
    FundsAvailableWithBankEnum,
    FundsBlockedWithBankEnum,
)

from ..bank_interface.bank_connector_interface import (
    BankConnectorInterface,
    BlockFundsResponse,
    CheckFundsResponse,
    DisbursementPaymentPayload,
    PaymentResponse,
    PaymentStatus,
)
from ..config import Settings
from ..helpers import AccessBankHelper

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class AccessBankConnector(BankConnectorInterface):
    def check_funds(self, account_number, currency, amount) -> CheckFundsResponse:
        """Not implemented for Bank connector - passing for now."""
        _logger.info("check_funds not implemented for AccessBankConnector")
        return CheckFundsResponse(status=FundsAvailableWithBankEnum.FUNDS_AVAILABLE, error_code="")

    def block_funds(self, account_number, currency, amount) -> BlockFundsResponse:
        """Not implemented for Bank connector - passing for now."""
        _logger.info("block_funds not implemented for AccessBankConnector")
        return BlockFundsResponse(
            status=FundsBlockedWithBankEnum.FUNDS_BLOCK_SUCCESS,
            block_reference_no="FUNDS_BLOCKED",
            error_code="",
        )

    def initiate_payment(
        self, disbursement_batch_control_id: str, payment_payloads: List[DisbursementPaymentPayload]
    ) -> PaymentResponse:
        """
        Process payment payloads using Access Bank's async wallet payment API.

        Args:
            disbursement_batch_control_id: Batch control ID
            payment_payloads: List of DisbursementPaymentPayload objects

        Returns:
            PaymentResponse indicating success, queued, or failure status
        """
        _logger.info(f"Initiating async wallet payment for {len(payment_payloads)} payloads")

        if not payment_payloads:
            _logger.error("No payment payloads provided")
            return PaymentResponse(status=PaymentStatus.ERROR, error_code="NO_PAYLOADS")

        try:
            # Get access token
            access_token = AccessBankHelper.get_access_token()

            if not access_token:
                _logger.error("Failed to get access token")
                return PaymentResponse(status=PaymentStatus.ERROR, error_code="TOKEN_FAILED")

            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

            # Create batch payload following the API structure
            entries = []
            for payment_payload in payment_payloads:
                _logger.info(f"Processing payment payload: {payment_payload}")
                wallet_number = payment_payload.beneficiary_phone_no
                if not wallet_number:
                    _logger.error(f"No wallet number found for payload {payment_payload.disbursement_id}")
                    continue

                entry = {
                    "referenceId": payment_payload.disbursement_id,
                    "walletNumber": wallet_number,
                    "amount": payment_payload.payment_amount,
                    "currency": payment_payload.remitting_account_currency,
                    "narration": payment_payload.disbursement_narrative
                    or f"Payment - {payment_payload.beneficiary_name or payment_payload.beneficiary_id}",
                }

                _logger.info(f"Created entry: {entry}")
                entries.append(entry)

            if not entries:
                _logger.error("No valid entries created from payment payloads")
                return PaymentResponse(status=PaymentStatus.ERROR, error_code="NO_VALID_ENTRIES")

            # Create batch payload
            batch_payload = {
                "batchId": disbursement_batch_control_id,
                "companyId": _config.access_bank_company_id,
                "callbackUrl": _config.disbursement_batch_control_callback_url,
                "entries": entries,
            }

            _logger.info(f"Sending batch payload to API: {batch_payload}")

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    _config.access_bank_wallet_payment_batch_url, json=batch_payload, headers=headers
                )

                _logger.info(f"Wallet payment API response status: {response.status_code}")
                _logger.info(f"Response body: {response.text}")

                if response.status_code == 202:
                    response_data = response.json()
                    if response_data.get("queued", False):
                        _logger.info(
                            f"Batch payment {disbursement_batch_control_id} queued successfully with {response_data.get('accepted', 0)} accepted entries"
                        )
                        return PaymentResponse(status=PaymentStatus.QUEUED, error_code="")
                    else:
                        _logger.error(f"Batch payment {disbursement_batch_control_id} failed to queue")
                        return PaymentResponse(status=PaymentStatus.ERROR, error_code="BATCH_QUEUE_FAILED")
                else:
                    _logger.error(f"API call failed with status {response.status_code}: {response.text}")
                    return PaymentResponse(
                        status=PaymentStatus.ERROR, error_code=f"API_ERROR: {response.status_code}"
                    )

        except Exception as e:
            _logger.error(f"Error initiating wallet payment: {str(e)}")
            return PaymentResponse(status=PaymentStatus.ERROR, error_code=f"API_ERROR: {str(e)}")

    def retrieve_reconciliation_id(
        self, bank_reference: str, customer_reference: str, narratives: str
    ) -> str:
        """Not implemented for Bank connector - passing for now."""
        _logger.info("retrieve_reconciliation_id not implemented for AccessBankConnector")
        return customer_reference

    def retrieve_beneficiary_name(self, narratives: str) -> str:
        """Not implemented for Bank connector - passing for now."""
        _logger.info("retrieve_beneficiary_name not implemented for AccessBankConnector")
        return ""

    def retrieve_reversal_reason(self, narratives: str) -> str:
        """Not implemented for Bank connector - passing for now."""
        _logger.info("retrieve_reversal_reason not implemented for AccessBankConnector")
        return ""
