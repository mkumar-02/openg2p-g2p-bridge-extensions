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
    MobileMoneyBatchDisbursementPaymentPayload,
    MobileMoneySingleDisbursementPaymentPayload,
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
            payment_payloads: List of DisbursementPaymentPayload objects

        Returns:
            PaymentResponse indicating success, queued, or failure status
        """
        _logger.info(f"Initiating async wallet payment for {len(payment_payloads)} payloads")

        if not payment_payloads:
            _logger.error("No payment payloads provided")
            return PaymentResponse(status=PaymentStatus.ERROR, error_code="NO_PAYLOADS")

        try:
            # transform DisbursementPaymentPayload to MobileMoneySingleDisbursementPaymentPayload
            mobile_money_single_disbursement_payment_payloads: List[
                MobileMoneySingleDisbursementPaymentPayload
            ] = []
            for payment_payload in payment_payloads:
                _logger.info("Processing payment payload: {payment_payload}")
                wallet_number = payment_payload.beneficiary_phone_no
                if not wallet_number:
                    _logger.error(f"No wallet number found for payload {payment_payload.disbursement_id}")
                    continue

                mobile_money_single_disbursement_payment_payload = (
                    MobileMoneySingleDisbursementPaymentPayload(
                        referenceId=payment_payload.disbursement_id,
                        walletNumber=wallet_number,
                        amount=payment_payload.payment_amount,
                        currency=payment_payload.remitting_account_currency,
                        narration=payment_payload.disbursement_narrative
                        or f"Payment - {payment_payload.beneficiary_name or payment_payload.beneficiary_id}",
                    )
                )

                _logger.info(
                    f"Created single payload: {mobile_money_single_disbursement_payment_payload.model_dump()}"
                )
                mobile_money_single_disbursement_payment_payloads.append(
                    mobile_money_single_disbursement_payment_payload
                )

                _logger.info(
                    f"Created MobileMoneySingleDisbursementPaymentPayload for disbursement ID: {payment_payload.disbursement_id}"
                )
            _logger.debug(
                f"MobileMoneySingleDisbursementPaymentPayload: {mobile_money_single_disbursement_payment_payloads}"
            )

            if not mobile_money_single_disbursement_payment_payloads:
                _logger.error("No valid entries created from payment payloads")
                return PaymentResponse(status=PaymentStatus.ERROR, error_code="NO_VALID_ENTRIES")

            # Optional callback URL - the application using this library can provide it
            batch_payload = MobileMoneyBatchDisbursementPaymentPayload(
                batchId=disbursement_batch_control_id,
                companyId=_config.access_bank_company_id,
                callbackUrl=_config.disbursement_batch_control_callback_url,
                entries=mobile_money_single_disbursement_payment_payloads,
            )

            _logger.debug(f"Constructed MobileMoneyBatchDisbursementPaymentPayload: {batch_payload}")

            # Make API call to Access Bank
            access_token = AccessBankHelper.get_access_token()

            if not access_token:
                _logger.error("Failed to get access token")
                return {}

            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}

            # Convert payload to dict for JSON serialization
            payload_dict = batch_payload.model_dump(exclude_none=True)

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    _config.access_bank_wallet_payment_batch_url, json=payload_dict, headers=headers
                )

                _logger.info(f"Wallet payment API response status: {response.status_code}")

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
