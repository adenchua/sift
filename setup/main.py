import sys
import json

sys.path.append("..")

from database_connector.database_client import DatabaseClient


def setup_indices(db_client: DatabaseClient):
    with open("indices.json") as file:
        indices = json.load(file)
        for index in indices:
            print(index)
            create_index_response = db_client.add_database_index(index)
            print("\nCreating index:")
            print(create_index_response)


def setup_channels(db_client: DatabaseClient):
    with open("channels.json") as file:
        channels = json.load(file)
        for channel in channels:
            channel_id = channel["id"]
            channel_body = channel["document"]
            db_client.create(
                index_name="channel",
                document=channel_body,
                document_id=channel_id,
            )


# first time setup for new machines
# 1. loads the mapping for the indices
# 2. add basic channels
def main():
    db_client = DatabaseClient()
    setup_indices(db_client)
    setup_channels(db_client)


if __name__ == "__main__":
    main()
