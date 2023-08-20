from fastapi import FastAPI, HTTPException
from typing import List
from pydantic import BaseModel

from services.subscriber_service import Subscriber, SubscriberService, SubscriptionException

app = FastAPI()


class SubscriberTheme(BaseModel):
    theme: str
    keywords: List[str]


@app.get("/")
async def root():
    return {"message": "connection to sift server successful!"}


@app.post("/subscriber", status_code=201)
async def add_new_subscriber(subscriber: Subscriber):
    subscriber_client = SubscriberService()
    subscriber_id = subscriber.telegram_id
    try:
        response = subscriber_client.add_subscriber(subscriber=subscriber)
        return {"message": f"New subscriber with id {response} created!"}
    except SubscriptionException:
        raise HTTPException(status_code=409, detail=f"Subscriber with id <{subscriber_id}> already exists")


@app.patch("/subscriber/{subscriber_id}/themes", status_code=204)
async def update_subscriber_theme_keywords(subscriber_id: str, theme: SubscriberTheme):
    subscriber_client = SubscriberService()

    subscriber_client.update_subscriber_keywords(
        subscriber_id=subscriber_id, theme=theme.theme, new_keywords=theme.keywords
    )


@app.post("/subscriber/{subscriber_id}/unsubscribe", status_code=204)
async def unsubscribe(subscriber_id: str):
    subscriber_client = SubscriberService()

    if not subscriber_client.check_subscriber_exists(subscriber_id):
        raise HTTPException(status_code=404, detail=f"Subscriber record not found")

    subscriber_client.toggle_subscription(subscriber_id=subscriber_id, is_subscribed=False)


@app.post("/subscriber/{subscriber_id}/subscribe", status_code=204)
async def subscribe(subscriber_id: str):
    subscriber_client = SubscriberService()

    if not subscriber_client.check_subscriber_exists(subscriber_id):
        raise HTTPException(status_code=404, detail=f"Subscriber record not found")

    subscriber_client.toggle_subscription(subscriber_id=subscriber_id, is_subscribed=True)
