from pydantic import BaseModel
from typing import Optional, List

from database_connector.database_client import DatabaseClient


class SubscribedTheme(BaseModel):
    theme: str
    keywords: List[str]
    last_crawl_timestamp: Optional[str] = None


class Subscriber(BaseModel):
    telegram_id: str
    is_subscribed: Optional[bool] = True
    subscribed_themes: list[SubscribedTheme] = []


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

    def update_subscriber_theme_timestamp(self, subscriber_id: str, theme: str, iso_timestamp: str):
        self.database_client.update(
            index_name=self.__INDEX_NAME,
            document_id=subscriber_id,
            script_doc={
                "lang": "painless",
                "source": """for(int i=0;i<ctx._source.subscribed_themes.length;i++){
                if(ctx._source.subscribed_themes[i].theme == params.theme){ctx._source.subscribed_themes[i].last_crawl_timestamp = params.new_value;}
                }""",
                "params": {
                    "theme": theme,
                    "new_value": iso_timestamp,
                },
            },
        )

    def add_subscriber(self, subscriber: Subscriber):
        """adds a subscriber to the database"""
        subscribed_themes = [subscribed_theme.model_dump() for subscribed_theme in subscriber.subscribed_themes]

        self.database_client.create(
            index_name=self.__INDEX_NAME,
            document={"is_subscribed": subscriber.is_subscribed, "subscribed_themes": subscribed_themes},
            document_id=subscriber.telegram_id,
        )

    def toggle_subscription(self, subscriber_id: str, is_subscribed: bool):
        """changes a subscriber is_subscribed flag


        Parameters:
        subscriber_id - id of subscriber to update the is_subscribed status

        is_subscribed - boolean flag to change to
        """
        self.database_client.update(
            index_name=self.__INDEX_NAME, document_id=subscriber_id, partial_doc={"is_subscribed": is_subscribed}
        )

    def update_subscriber_keywords(self, subscriber_id: str, theme: str, new_keywords: List[str]):
        """
        Updates the keywords of a subscriber's theme.
        """
        self.database_client.update(
            index_name=self.__INDEX_NAME,
            document_id=subscriber_id,
            script_doc={
                "lang": "painless",
                "source": """for(int i=0;i<ctx._source.subscribed_themes.length;i++){
                if(ctx._source.subscribed_themes[i].theme == params.theme){ctx._source.subscribed_themes[i].keywords = params.new_value;}
                }""",
                "params": {
                    "theme": theme,
                    "new_value": new_keywords,
                },
            },
        )
