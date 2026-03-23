import csv
import io
import logging
from datetime import datetime
from typing import List

import requests

from .bank_interface.bank_connector_interface import DisbursementPaymentPayload
from .config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class AccessBankHelper:
    """Utility class for Access Bank specific operations."""

    @staticmethod
    def get_access_token() -> str:
        """
        Retrieve access token from Access Bank API.

        Returns:
            Access token string
        """
        _logger.info("Retrieving access token from Access Bank API")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        payload = {
            "client_id": _config.access_bank_client_id,
            "client_secret": _config.access_bank_client_secret,
            "grant_type": _config.access_bank_grant_type,
        }

        res = requests.post(_config.access_bank_token_url, headers=headers, data=payload)

        if res.status_code == 200:
            token_data = res.json()
            access_token = token_data.get("access_token")
            if access_token:
                _logger.info("Successfully retrieved access token")
                return access_token
            else:
                _logger.error("Access token not found in response")
                raise ValueError("Access token not found in response")
        else:
            _logger.error(f"Failed to retrieve access token: {res.status_code} - {res.text}")
            raise Exception(f"Token request failed: {res.status_code}")


class ZambiaCSVHelper:
    """Utility class for CSV generation and filename utilities for Zambia connector."""

    @staticmethod
    def generate_filename(first_payload: DisbursementPaymentPayload) -> str:
        """
        Generate filename using narrative_2 and narrative_3 from the first payload.

        Args:
            first_payload: First payment payload to extract narratives from

        Returns:
            Generated filename string
        """
        # Use benefit_program_mnemonic (narrative_2) and cycle_code_mnemonic (narrative_3)
        narrative_2 = first_payload.benefit_program_mnemonic or "unknown_program"
        narrative_3 = first_payload.cycle_code_mnemonic or "unknown_cycle"

        # Add timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"{narrative_2}_{narrative_3}_{timestamp}.csv"
        _logger.info(f"Generated filename: {filename}")

        return filename

    @staticmethod
    def create_csv_content(payment_payloads: List[DisbursementPaymentPayload]) -> str:
        """
        Create CSV content with specified headers and data.

        Headers: Full Name, NRC, Phone, Total Days, Amount Due

        Args:
            payment_payloads: List of payment payloads to convert to CSV

        Returns:
            CSV content as string
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        headers = ["Full Name", "NRC", "Phone", "Total Days", "Amount Due"]
        writer.writerow(headers)

        # Write data rows
        for payload in payment_payloads:
            row = [
                payload.beneficiary_name or "-",  # Full Name
                payload.beneficiary_bank_code or "-",  # NRC
                payload.beneficiary_phone_no or "-",  # Phone
                (
                    payload.compute_elements.get("number_of_days", "-") if payload.compute_elements else "-"
                ),  # Total Days
                payload.payment_amount or "-",  # Amount Due
            ]
            writer.writerow(row)

        csv_content = output.getvalue()
        output.close()

        _logger.info(f"Generated CSV with {len(payment_payloads)} rows")
        return csv_content
