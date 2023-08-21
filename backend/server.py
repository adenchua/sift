from fastapi import FastAPI, HTTPException
from typing import List
from pydantic import BaseModel

from services.subscriber_service import (
    Subscriber,
    SubscriberService,
    SubscriptionException,
)
from services.channel_service import Channel, ChannelService

app = FastAPI()


class SubscriberTheme(BaseModel):
    theme: str
    keywords: List[str]


@app.get("/")
async def root():
    return {"message": "connection to sift server successful!"}


@app.post("/subscriber", status_code=201)
async def add_new_subscriber(subscriber: Subscriber):
    subscriber_service = SubscriberService()
    subscriber_id = subscriber.telegram_id
    try:
        response = subscriber_service.add_subscriber(subscriber=subscriber)
        return {"message": f"New subscriber with id {response} created!"}
    except SubscriptionException:
        raise HTTPException(
            status_code=409,
            detail=f"Subscriber with id <{subscriber_id}> already exists",
        )


@app.patch("/subscriber/{subscriber_id}/themes", status_code=204)
async def update_subscriber_theme_keywords(subscriber_id: str, theme: SubscriberTheme):
    subscriber_service = SubscriberService()

    subscriber_service.update_subscriber_keywords(
        subscriber_id=subscriber_id, theme=theme.theme, new_keywords=theme.keywords
    )


@app.post("/subscriber/{subscriber_id}/unsubscribe", status_code=204)
async def unsubscribe(subscriber_id: str):
    subscriber_service = SubscriberService()

    if not subscriber_service.check_subscriber_exists(subscriber_id):
        raise HTTPException(status_code=404, detail=f"Subscriber record not found")

    subscriber_service.toggle_subscription(subscriber_id=subscriber_id, is_subscribed=False)


@app.post("/subscriber/{subscriber_id}/subscribe", status_code=204)
async def subscribe(subscriber_id: str):
    subscriber_service = SubscriberService()

    if not subscriber_service.check_subscriber_exists(subscriber_id):
        raise HTTPException(status_code=404, detail=f"Subscriber record not found")

    subscriber_service.toggle_subscription(subscriber_id=subscriber_id, is_subscribed=True)


@app.post("/channels", status_code=201)
async def add_channel(channel: Channel):
    channel_service = ChannelService()
    channel_id = channel.channel_id

    try:
        response = channel_service.add_channel(channel=channel)
        return {"message": f"New channel with id {response} created!"}
    except SubscriptionException:
        raise HTTPException(
            status_code=409,
            detail=f"Channel with id <{channel_id}> already exists",
        )
