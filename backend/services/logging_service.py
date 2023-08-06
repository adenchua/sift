from utils import date_helper


class LoggingService:
    def __init__(self) -> None:
        pass

    def log_info(self, message: str) -> None:
        print(f"INFO | {date_helper.get_current_iso_datetime()} | {message}")
        pass

    def log_error(self, error_message: str) -> None:
        print(f"ERROR | {date_helper.get_current_iso_datetime()} | {error_message}")
