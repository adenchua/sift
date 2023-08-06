from database_connector.database_client import DatabaseClient


class ChannelService:
    __INDEX_NAME = "channel"

    def __init__(self):
        self.database_client = DatabaseClient()

    def get_channels(self):
        result = self.database_client.read(
            index_name=self.__INDEX_NAME, query={"match_all": {}}
        )
        return result

    def update_channel_offset(self, channel_id, new_offset_id):
        result = self.database_client.update(
            index_name="channel",
            document_id=channel_id,
            update_body={"doc": {"offset_id": new_offset_id}},
        )

        return result
