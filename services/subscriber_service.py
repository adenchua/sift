from typing import List, Optional, Union

from pydantic import BaseModel

from database_connector.database_client import DatabaseClient


class SubscriberExistsException(Exception):
    pass


class SubscribedTheme(BaseModel):
    theme: str
    keywords: List[str]
    last_notified_timestamp: Optional[str] = None


class Subscriber(BaseModel):
    telegram_id: str
    telegram_username: Optional[str] = None
    is_subscribed: Optional[bool] = True
    subscribed_themes: list[SubscribedTheme] = []


class SubscriberService:
    __INDEX_NAME = "subscriber"

    def __init__(self):
        self.database_client = DatabaseClient()

    def __toggle_subscription(self, subscriber_id: Union[str, int], is_subscribed: bool):
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

    def check_subscriber_exists(self, id: Union[str, int]):
        """Checks if a subscriber exist with a id.
        Returns true if exists, false otherwise"""
        return self.database_client.document_exist(index_name=self.__INDEX_NAME, document_id=str(id))

    def get_subscribers(self, is_subscribed: Optional[bool] = True):
        """Returns a list of users filtered by is_subscribed status"""
        result = self.database_client.read(
            index_name=self.__INDEX_NAME,
            query={
                "term": {"is_subscribed": is_subscribed},
            },
        )

        return result

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

    def update_subscriber_theme_timestamp(self, subscriber_id: Union[str, int], theme: str, iso_timestamp: str):
        """Updates a subscriber's theme last_notified_timestamp.
        If the theme does not exist, this operation does nothing
        """
        self.database_client.update(
            index_name=self.__INDEX_NAME,
            document_id=str(subscriber_id),
            script_doc={
                "lang": "painless",
                "source": """for(int i=0;i<ctx._source.subscribed_themes.length;i++){
                if(ctx._source.subscribed_themes[i].theme == params.theme){ctx._source.subscribed_themes[i].last_notified_timestamp = params.new_value;}
                }""",
                "params": {
                    "theme": theme,
                    "new_value": iso_timestamp,
                },
            },
        )

    def update_subscriber_theme_keywords(self, subscriber_id: Union[str, int], theme: str, new_keywords: List[str]):
        """
        Updates the keywords of a subscriber's theme.

        If the theme doesn't exist, a new theme with the keywords is added to the theme list
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
                    ctx._source.subscribed_themes.add(["theme": params.theme, "keywords": params.new_value, "last_notified_timestamp": null]);
                }
                """,
                "params": {
                    "theme": theme,
                    "new_value": new_keywords,
                },
            },
        )

    def unsubscribe(self, subscriber_id: Union[str, int]):
        """
        unsubscribes the user from receiving notifications.

        Sets the last_notified_timestamp of all themes to None.
        This prevents the subscriber from getting spammed with large volume of messages upon re-subscribing
        """
        self.__toggle_subscription(subscriber_id=subscriber_id, is_subscribed=False)
        self.database_client.update(
            index_name=self.__INDEX_NAME,
            document_id=str(subscriber_id),
            script_doc={
                "lang": "painless",
                "source": """for(int i=0;i<ctx._source.subscribed_themes.length;i++){
                ctx._source.subscribed_themes[i].last_notified_timestamp = null;
                }""",
            },
        )

    def subscribe(self, subscriber_id: Union[str, int]):
        """
        subscribes the user to receive notifications
        """
        self.__toggle_subscription(subscriber_id=subscriber_id, is_subscribed=True)
