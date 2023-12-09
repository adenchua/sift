from pydantic import BaseModel
from typing import Optional, List
from typing import Union

from database_connector.database_client import DatabaseClient


class SubscriberExistsException(Exception):
    pass


class SubscribedTheme(BaseModel):
    theme: str
    keywords: List[str]
    last_crawl_timestamp: Optional[str] = None


class Subscriber(BaseModel):
    telegram_id: str
    telegram_username: Optional[str] = None
    is_subscribed: Optional[bool] = True
    subscribed_themes: list[SubscribedTheme] = []


class SubscriberService:
    __INDEX_NAME = "subscriber"

    def __init__(self):
        self.database_client = DatabaseClient()

    def check_subscriber_exists(self, id: Union[str, int]):
        """Checks if a subscriber exist with a id.
        Returns true if exists, false otherwise"""
        return self.database_client.document_exist(index_name=self.__INDEX_NAME, document_id=str(id))

    def get_subscribers(self, is_subscribed=True):
        """Gets all users in the database
        Returns a list of users
        """
        result = self.database_client.read(
            index_name=self.__INDEX_NAME,
            query={
                "term": {"is_subscribed": is_subscribed},
            },
        )

        return result

    def update_subscriber_theme_timestamp(self, subscriber_id: Union[str, int], theme: str, iso_timestamp: str):
        self.database_client.update(
            index_name=self.__INDEX_NAME,
            document_id=str(subscriber_id),
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

    def add_subscriber(self, subscriber: Subscriber) -> str:
        """adds a subscriber with a telegram id to the database

        Parameters:
        subscriber - subscriber to add into the database

        Raises:
        SubscriptionException - if there is a existing subscriber with the subscriber id
        """
        subscribed_themes = [subscribed_theme.model_dump() for subscribed_theme in subscriber.subscribed_themes]
        telegram_id = subscriber.telegram_id

        subscriber_exists = self.check_subscriber_exists(telegram_id)
        if subscriber_exists:
            raise SubscriberExistsException(f"Subscriber with {telegram_id} already exists")

        response = self.database_client.create(
            index_name=self.__INDEX_NAME,
            document={
                "is_subscribed": subscriber.is_subscribed,
                "subscribed_themes": subscribed_themes,
                "telegram_username": subscriber.telegram_username,
            },
            document_id=telegram_id,
        )

        return response

    def toggle_subscription(self, subscriber_id: Union[str, int], is_subscribed: bool):
        """changes a subscriber is_subscribed flag


        Parameters:
        subscriber_id - id of subscriber to update the is_subscribed status

        is_subscribed - boolean flag to change to
        """
        self.database_client.update(
            index_name=self.__INDEX_NAME,
            document_id=str(subscriber_id),
            partial_doc={"is_subscribed": is_subscribed},
        )

    def update_subscriber_keywords(self, subscriber_id: Union[str, int], theme: str, new_keywords: List[str]):
        """
        Updates the keywords of a subscriber's theme.

        If the theme doesn't exist, it adds it to the subscribed themes list
        """
        self.database_client.update(
            index_name=self.__INDEX_NAME,
            document_id=str(subscriber_id),
            script_doc={
                "lang": "painless",
                "source": """
                boolean newTheme = true;
                for(int i=0;i<ctx._source.subscribed_themes.length;i++){
                    if(ctx._source.subscribed_themes[i].theme == params.theme){
                        ctx._source.subscribed_themes[i].keywords = params.new_value;
                        newTheme = false;
                        break;
                    }
                }
                if(newTheme){
                    ctx._source.subscribed_themes.add(["theme": params.theme, "keywords": params.new_value, "last_crawl_timestamp": null]);
                }
                """,
                "params": {
                    "theme": theme,
                    "new_value": new_keywords,
                },
            },
        )
