from pydantic import BaseModel
from typing import List, Optional

from database_connector.database_client import DatabaseClient


class Channel(BaseModel):
    channel_id: str
    channel_name: str
    themes: List[str]
    offset_id: Optional[int] = None
    is_active: Optional[bool] = True


class ChannelService:
    __INDEX_NAME = "channel"

    def __init__(self):
        self.database_client = DatabaseClient()

    def get_channels(self):
        result = self.database_client.read(
            index_name=self.__INDEX_NAME, query={"match_all": {}}
        )

        return result

    def get_active_channels(self):
        """
        returns all active channels. Active channels refer to channels
        that are being crawled by the system periodically
        """
        result = self.database_client.read(
            index_name=self.__INDEX_NAME, query={"term": {"is_active": True}}
        )

        return result

    def update_channel_offset(self, channel_id: str, new_offset_id: str):
        result = self.database_client.update(
            index_name="channel",
            document_id=channel_id,
            partial_doc={"offset_id": new_offset_id},
        )

        return result

    def add_channel(self, channel: Channel):
        channel_id = channel.channel_id
        channel_name = channel.channel_name
        is_active = channel.is_active
        offset_id = channel.offset_id
        themes = channel.themes

        result = self.database_client.create(
            index_name=self.__INDEX_NAME,
            document={
                "name": channel_name,
                "is_active": is_active,
                "offset_id": offset_id,
                "themes": themes,
            },
            document_id=channel_id,
        )

        return result
