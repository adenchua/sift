from pydantic import BaseModel
from typing import List, Optional, Union

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
        """
        Retrieves all channels in the database, including inactive channels
        """
        try:
            result = self.database_client.read(index_name=self.__INDEX_NAME, query={"match_all": {}})
            return result
        except Exception as error:
            raise (error)

    def get_active_channels(self):
        """
        returns all active channels. Active channels refer to channels
        that are being crawled by the system periodically
        """
        try:
            result = self.database_client.read(index_name=self.__INDEX_NAME, query={"term": {"is_active": True}})
            return result
        except Exception as error:
            raise (error)

    def update_channel_offset(self, channel_id: str, new_offset_id: Union[str, None]):
        """
        Updates a channel's offset id
        """
        try:
            result = self.database_client.update(
                index_name="channel",
                document_id=channel_id,
                partial_doc={"offset_id": new_offset_id},
            )
            return result
        except Exception as error:
            raise (error)

    def add_channel(self, channel: Channel):
        """
        Adds a new channel to the database. A channel's is_active flag is set to True by default
        unless specified.
        """
        try:
            result = self.database_client.create(
                index_name=self.__INDEX_NAME,
                document={
                    "name": channel.channel_name,
                    "is_active": channel.is_active,
                    "offset_id": channel.offset_id,
                    "themes": channel.themes,
                },
                document_id=channel.channel_id,
            )
            return result
        except Exception as error:
            raise (error)

    def toggle_channel_activeness(self, channel_id: str, is_active: bool) -> bool:
        """
        Sets a channel is_active flag to the given is_active flag


        Parameters:
        channel_id - id of channel to toggle is_active flag

        is_active - flag to be used to set the channel is_active
        """
        try:
            self.database_client.update(
                index_name=self.__INDEX_NAME, document_id=channel_id, partial_doc={"is_active": is_active}
            )

        except Exception as error:
            raise error

    def update_channel_themes(self, channel_id: str, themes: List[str]):
        """
        Updates a channel's themes list

        Parameters:
        channel_id - id of the channel to update
        themes - list of themes to set this channel to. Messages crawled from this channel will inherit the themes
        """
        try:
            self.database_client.update(
                index_name=self.__INDEX_NAME, document_id=channel_id, partial_doc={"themes": themes}
            )

        except Exception as error:
            raise error
