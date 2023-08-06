from database_connector.database_client import DatabaseClient
from utils import date_helper


class SubscriberService:
    __INDEX_NAME = "subscriber"

    def __init__(self):
        self.database_client = DatabaseClient()

    def get_subscribers(self):
        result = self.database_client.read(
            index_name=self.__INDEX_NAME,
            query={
                "term": {"is_subscribed": True},
            },
        )

        return result

    def update_subscriber_theme_timestamp(self, subscriber_id: str, theme: str):
        self.database_client.update(
            index_name=self.__INDEX_NAME,
            document_id=subscriber_id,
            update_body={
                "script": {
                    "lang": "painless",
                    "source": """for(int i=0;i<ctx._source.keywords.length;i++){
                if(ctx._source.keywords[i].theme == params.theme){ctx._source.keywords[i].last_crawl_timestamp = params.new_value;}
                }""",
                    "params": {
                        "theme": theme,
                        "new_value": date_helper.get_current_iso_datetime(),
                    },
                },
            },
        )

        # TODO: add in response message
