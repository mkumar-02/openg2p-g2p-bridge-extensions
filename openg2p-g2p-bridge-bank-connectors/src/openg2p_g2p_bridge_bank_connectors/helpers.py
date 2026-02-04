import csv
import io
import logging
from datetime import datetime
from typing import List

from .bank_interface.bank_connector_interface import DisbursementPaymentPayload
from .config import Settings
from .engine import get_district_from_registry, get_tasks_from_attendance

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


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
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")

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
        headers = [
            "Full Name",
            "NRC",
            "Phone",
            "Local Authority",
            "Name of Sites",
            "Total Days",
            "Amount Due",
        ]
        writer.writerow(headers)

        # Write data rows
        for payload in payment_payloads:
            # Get Local Authority (district) from registry database
            local_authority = "-"
            name_of_sites = "-"

            if payload.beneficiary_id:
                local_authority = get_district_from_registry(payload.beneficiary_id)
                name_of_sites = get_tasks_from_attendance(payload.beneficiary_id)

            row = [
                payload.beneficiary_name or "-",  # Full Name
                payload.beneficiary_bank_code or "-",  # NRC
                payload.beneficiary_phone_no or "-",  # Phone
                local_authority,  # Local Authority (from g2p_registry_worker)
                name_of_sites,  # Name of Sites (from g2p_registry_monthly_attendance)
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
