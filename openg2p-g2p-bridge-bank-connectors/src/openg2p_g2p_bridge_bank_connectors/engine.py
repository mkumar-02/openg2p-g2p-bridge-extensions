import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from .config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


def construct_db_datasource(db_driver, db_username, db_password, db_hostname, db_port, db_dbname) -> str:
    datasource = ""
    if db_driver:
        datasource += f"{db_driver}://"
    if db_username:
        datasource += f"{db_username}:{db_password}@"
    if db_hostname:
        datasource += db_hostname
    if db_port:
        datasource += f":{db_port}"
    if db_dbname:
        datasource += f"/{db_dbname}"
    return datasource


def get_registry_engine():
    db_datasource_registry = construct_db_datasource(
        _config.db_driver_registry,
        _config.db_username_registry,
        _config.db_password_registry,
        _config.db_hostname_registry,
        _config.db_port_registry,
        _config.db_dbname_registry,
    )
    db_engine_registry = create_engine(db_datasource_registry)
    return db_engine_registry


def get_district_from_registry(beneficiary_id: str) -> str:
    """
    Query the g2p_registry_worker view to get the district_name for a beneficiary.

    Args:
        beneficiary_id: The beneficiary ID to query

    Returns:
        The district name or "-" if not found
    """
    try:
        engine = get_registry_engine()
        Session = sessionmaker(bind=engine)
        session = Session()

        query = text("SELECT district_name FROM g2p_registry_worker WHERE link_registry_id = :beneficiary_id")
        result = session.execute(query, {"beneficiary_id": beneficiary_id}).fetchone()

        session.close()

        if result and result[0]:
            return result[0]
        else:
            _logger.warning(f"No district found for beneficiary_id: {beneficiary_id}")
            return "-"

    except Exception as e:
        _logger.error(f"Error querying registry for beneficiary_id {beneficiary_id}: {str(e)}")
        return "-"


def get_tasks_from_attendance(beneficiary_id: str) -> str:
    """
    Query the g2p_registry_monthly_attendance view to get the tasks for a beneficiary.

    Args:
        beneficiary_id: The beneficiary ID to query

    Returns:
        The tasks as comma-separated string or "-" if not found
    """
    try:
        engine = get_registry_engine()
        Session = sessionmaker(bind=engine)
        session = Session()

        query = text(
            "SELECT tasks FROM g2p_registry_monthly_attendance WHERE link_registry_id = :beneficiary_id LIMIT 1"
        )
        result = session.execute(query, {"beneficiary_id": beneficiary_id}).fetchone()

        session.close()

        if result and result[0]:
            # Convert array to comma-separated string
            if isinstance(result[0], list):
                return ", ".join(result[0])
            else:
                return str(result[0])
        else:
            _logger.warning(f"No tasks found for beneficiary_id: {beneficiary_id}")
            return "-"

    except Exception as e:
        _logger.error(f"Error querying attendance for beneficiary_id {beneficiary_id}: {str(e)}")
        return "-"
