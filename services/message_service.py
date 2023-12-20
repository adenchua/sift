from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from database_connector.database_client import DatabaseClient
from utils import date_helper


class Message(BaseModel):
    text: Optional[str] = None
    themes: List[str]
    channel_id: str
    timestamp: datetime
    message_id: str


class MessageService:
    __INDEX_NAME = "message"

    def __init__(self):
        self.database_client = DatabaseClient()

    def create_message(self, message: Message):
        """
        ingest a message into the database
        """
        result = self.database_client.create(
            index_name=self.__INDEX_NAME,
            document={
                "text": message.text,
                "themes": message.themes,
                "channel_id": message.channel_id,
                "timestamp": message.timestamp,
            },
            document_id=message.message_id,
        )
        return result

    def get_matched_messages(self, keywords_list: List[str], theme: str, iso_date_from: Optional[str] = None):
        """
        retrieves matched messages from the database filtered from the theme keywords and a datetime.

        If the datetime is not provided, it will be set to today at 0000hrs.
        """
        # if timestamp is not provided, send messages after today 0000hrs
        # This prevents new subscribers from getting spammed with messages from the dawn of time
        from_datetime = date_helper.get_today_iso_date() if iso_date_from is None else iso_date_from
        query_string = self.database_client.build_query_string(keywords_list)
        query = {
            "bool": {
                "must": [
                    {"query_string": {"query": query_string}},
                    {"term": {"themes": {"value": theme}}},
                ],
                "filter": [{"range": {"timestamp": {"gt": from_datetime}}}],
            }
        }

        result = self.database_client.read(index_name=self.__INDEX_NAME, query=query)
        return result
