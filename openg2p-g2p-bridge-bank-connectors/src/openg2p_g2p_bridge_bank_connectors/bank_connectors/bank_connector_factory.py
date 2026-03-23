from openg2p_fastapi_common.service import BaseService

from ..bank_interface.bank_connector_interface import BankConnectorInterface
from ..config import Settings
from .access_bank_connector import AccessBankConnector
from .zambia_csv_connector import ZambiaCSVConnector

_config = Settings.get_config()


class BankConnectorFactory(BaseService):
    def get_bank_connector(self, sponsor_bank_code: str) -> BankConnectorInterface:
        if sponsor_bank_code == "ACCESS_BANK":
            return AccessBankConnector.get_component()
        elif sponsor_bank_code == "ZAMBIA_CSV":
            return ZambiaCSVConnector.get_component()
        else:
            raise ValueError(f"Unsupported bank code: {sponsor_bank_code}")
