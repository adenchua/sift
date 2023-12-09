import sys

sys.path.append("..")

from fastapi import FastAPI, HTTPException
from typing import List
from pydantic import BaseModel

from services.subscriber_service import (
    Subscriber,
    SubscriberService,
    SubscriberExistsException,
)
from services.channel_service import Channel, ChannelService

app = FastAPI()


class SubscriberTheme(BaseModel):
    theme: str
    keywords: List[str]


class ChannelTheme(BaseModel):
    themes: List[str]


@app.get("/")
async def root():
    return {"message": "connection to sift server successful!"}


@app.get("/subscribers")
async def get_subscribers():
    subscriber_service = SubscriberService()
    try:
        non_subscribers = subscriber_service.get_subscribers(is_subscribed=False)
        subscribers = subscriber_service.get_subscribers(is_subscribed=True)
        return {"data": [*non_subscribers, *subscribers]}
    except SubscriberExistsException:
        raise HTTPException(
            status_code=500,
            detail="Something went wrong",
        )


@app.post("/subscribers", status_code=201)
async def add_new_subscriber(subscriber: Subscriber):
    subscriber_service = SubscriberService()
    subscriber_id = subscriber.telegram_id
    try:
        response = subscriber_service.add_subscriber(subscriber=subscriber)
        return {"message": f"New subscriber with id {response} created!"}
    except SubscriberExistsException:
        raise HTTPException(
            status_code=409,
            detail=f"Subscriber with id <{subscriber_id}> already exists",
        )


@app.patch("/subscribers/{subscriber_id}/themes", status_code=204)
async def update_subscriber_theme_keywords(subscriber_id: str, theme: SubscriberTheme):
    subscriber_service = SubscriberService()

    subscriber_service.update_subscriber_keywords(
        subscriber_id=subscriber_id, theme=theme.theme, new_keywords=theme.keywords
    )


@app.post("/subscribers/{subscriber_id}/unsubscribe", status_code=204)
async def unsubscribe(subscriber_id: str):
    subscriber_service = SubscriberService()

    if not subscriber_service.check_subscriber_exists(subscriber_id):
        raise HTTPException(status_code=404, detail=f"Subscriber not found")

    subscriber_service.toggle_subscription(subscriber_id=subscriber_id, is_subscribed=False)


@app.post("/subscribers/{subscriber_id}/subscribe", status_code=204)
async def subscribe(subscriber_id: str):
    subscriber_service = SubscriberService()

    if not subscriber_service.check_subscriber_exists(subscriber_id):
        raise HTTPException(status_code=404, detail=f"Subscriber not found")

    subscriber_service.toggle_subscription(subscriber_id=subscriber_id, is_subscribed=True)


@app.get("/channels")
async def get_channels():
    channel_service = ChannelService()
    try:
        response = channel_service.get_channels()
        return {"data": response}
    except SubscriberExistsException:
        raise HTTPException(
            status_code=500,
            detail="Something went wrong",
        )


@app.post("/channels", status_code=201)
async def add_channel(channel: Channel):
    channel_service = ChannelService()
    channel_id = channel.channel_id

    try:
        response = channel_service.add_channel(channel=channel)
        return {"message": f"New channel with id {response} created!"}
    except SubscriberExistsException:
        raise HTTPException(
            status_code=409,
            detail=f"Channel with id <{channel_id}> already exists",
        )


@app.post("/channels/{channel_id}/set-inactive", status_code=204)
async def set_channel_inactive(channel_id: str):
    channel_service = ChannelService()

    if not channel_service.check_channel_exists(channel_id=channel_id):
        raise HTTPException(status_code=404, detail=f"Channel not found")

    channel_service.toggle_channel_activeness(channel_id=channel_id, is_active=False)


@app.post("/channels/{channel_id}/set-active", status_code=204)
async def set_channel_active(channel_id: str):
    channel_service = ChannelService()

    if not channel_service.check_channel_exists(channel_id=channel_id):
        raise HTTPException(status_code=404, detail=f"Channel not found")

    channel_service.toggle_channel_activeness(channel_id=channel_id, is_active=True)


@app.patch("/channels/{channel_id}/themes", status_code=204)
async def update_channel_themes(channel_id: str, themes: ChannelTheme):
    channel_service = ChannelService()

    if not channel_service.check_channel_exists(channel_id=channel_id):
        raise HTTPException(status_code=404, detail=f"Channel not found")

    channel_service.update_channel_themes(channel_id=channel_id, themes=themes.themes)
