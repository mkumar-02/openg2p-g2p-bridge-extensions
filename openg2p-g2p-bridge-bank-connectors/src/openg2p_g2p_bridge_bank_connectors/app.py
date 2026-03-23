# ruff: noqa: E402

import logging

from .config import Settings

_config = Settings.get_config()

from openg2p_fastapi_common.app import Initializer as BaseInitializer

from .bank_connectors import AccessBankConnector, BankConnectorFactory, ZambiaCSVConnector

_logger = logging.getLogger(_config.logging_default_logger_name)


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        BankConnectorFactory()
        ZambiaCSVConnector()
        AccessBankConnector()
