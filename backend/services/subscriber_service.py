from database_connector.database_client import DatabaseClient


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

    def update_subscriber_theme_timestamp(
        self, subscriber_id: str, theme: str, iso_timestamp: str
    ):
        self.database_client.update(
            index_name=self.__INDEX_NAME,
            document_id=subscriber_id,
            update_body={
                "script": {
                    "lang": "painless",
                    "source": """for(int i=0;i<ctx._source.subscribed_themes.length;i++){
                if(ctx._source.subscribed_themes[i].theme == params.theme){ctx._source.subscribed_themes[i].last_crawl_timestamp = params.new_value;}
                }""",
                    "params": {
                        "theme": theme,
                        "new_value": iso_timestamp,
                    },
                },
            },
        )

        # TODO: add in response message
