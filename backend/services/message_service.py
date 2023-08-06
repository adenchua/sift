from typing import List

from database_connector.database_client import DatabaseClient
from utils import date_helper


class MessageService:
    __INDEX_NAME = "message"

    def __init__(self):
        self.database_client = DatabaseClient()

    def ingest_message(self, message, message_id):
        result = self.database_client.create(
            index_name=self.__INDEX_NAME, document=message, document_id=message_id
        )
        return result

    def get_messages(self, keywords_list: List[str], theme: str, iso_date=None):
        # if timestamp is not provided, send messages after today 0000hrs
        gte_datetime = (
            date_helper.get_today_iso_date() if iso_date is None else iso_date
        )
        query_string = self.database_client.build_query_string(keywords_list)
        query = {
            "bool": {
                "must": [
                    {"query_string": {"query": query_string}},
                    {"term": {"themes": {"value": theme}}},
                ],
                "filter": [{"range": {"timestamp": {"gte": gte_datetime}}}],
            }
        }

        result = self.database_client.read(index_name=self.__INDEX_NAME, query=query)
        return result
