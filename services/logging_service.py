from utils import date_helper
from abc import ABC


class Logger(ABC):
    """
    abstract base class for logging methods
    """

    def log(self, module: str, message: str):
        pass


class InfoLogger(Logger):
    def log(self, module: str, message: str):
        current_date_time = date_helper.get_current_iso_datetime()
        print(f"{current_date_time} |INFO| app[{module}]: {message}")


class ErrorLogger(Logger):
    def log(self, module: str, message: str):
        current_date_time = date_helper.get_current_iso_datetime()
        print(f"{current_date_time} |ERROR| app[{module}]: {message}")


class LoggingService:
    def __init__(self) -> None:
        self.info_logger = InfoLogger()
        self.error_logger = ErrorLogger()

    def log_info(self, message: str, module="SYSTEM") -> None:
        self.info_logger.log(module=module, message=message)

    def log_error(self, message: str, module="SYSTEM") -> None:
        self.error_logger.log(module=module, message=message)
