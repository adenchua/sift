# Design Documentation

Last updated: 28 December 2023

The following section documents the design considerations for **Sift**.

## Sift System Design

### Description

Sift is a telegram notification system that sends you a message whenever certain telegram channels/groups mentions your keyword of interest.

### Telegram channels message extraction

Telegram channels are generally opened to public and maintained by channel administrators. Most channel administrators use bots to post messages at certain timing of the day. Usually, `1~2` posts will be sent out in the afternoon `10am/11am/12pm/1pm` and in the evening `6pm`. For channels maintained without use of bots, posting pattern is unpredictable and could reach `~10` messages a day

### Themes

Each telegram channel is assigned with 1 or more themes and it depends on the content of the channel. For example, a channel posting mostly food content will be assigned with `Food` theme. Subscribers may set keywords for a theme. If a message from channels with the same `Theme` matches, it will be sent to the subscriber as a notification

### Background service for message extraction and notification

TODO

### Use Case & Assumption

- Users can only interact with the application through a telegram bot
- Administrators can manage channels and users through a web interface
- A background service should run periodically to download messages from telegram `channels`
- A background serice should run periodically to notify `users` for any matched `messages`
- Users can unsubscribe/subscribe to the notification service anytime
- A telegram `channel` may be multi-themed
- The `themes` are configured from the start, subjected to the business need. However these `themes` can be modified by system administrators

### Requirements

- The telegram bot should have high availability
- The background service should have high availability
- The web interface for administrators should have high availability

### Users & Traffic Estimates

This is a small scale application designed for personal use. At max, `10 users` will subscribe to this application.

### Data Models

![System Data Model](/docs/sift-data-model.jpg)

#### Subscriber

|Key | Field | Type | Max field size | Explanation | Required |
|---|---|--|--|---|--|
|PK| id | string | 64  | telegram ID, unique to each phone number | Yes |
|| telegram_username | string | 64 | telegram handle used by administrators to easily identify accounts; telegram bot for personalised greeting | No |
|| is_subscribed | boolean | 2 | Defaults to `true`. Used by notification service to send notifications to a subscriber when flag is `true`. | Yes |
|FK | subscribed_themes | Subscribed_Theme[] ||  | No |

#### Subscribed Theme

|Key | Field | Type | Max field size | Explanation | Required |
|---|---|--|--|---|--|
|PK| theme | string | 64 | unique theme keyword | Yes |
|| keywords | string[] | | keywords to match messages with | No |
|| last_notified_timestamp | string |32| the latest timestamp when a subscriber was notified for this theme. | No |

#### Channel

|Key | Field | Type | Max field size | Explanation | Required |
|---|---|--|--|---|--|
|PK| id | string | 64 | unique `telegram` channel handle | Yes |
|| name | string | 64 | `telegram` channel name | Yes |
|| is_active | boolean | 2 | TODO: to be removed | Yes |
|| themes | string[] || a `telegram` channel may cover several themes | Yes |
|| offset_id | int | 8 | stores the latest message ID downloaded. Used by `Download Service` to download messages later than this offset | No |

#### Message

|Key | Field | Type | Max field size | Explanation | Required |
|---|---|--|--|---|--|
|PK| id | string |64| database generated unique identifier | Yes |
|| text | string |256| `telegram` message | Yes |
|| themes | string[] || determined from the channel's themes. Used by `Message Service` to match keywords and theme | Yes |
|FK| channel_id | string |64| Used by `Notification Service` to send message source | Yes |
|| timestamp | string |32| ISO timestamp when the message was created in `Telegram` | Yes |
|| deletion_timestamp |string|32| ISO timestamp when the message will be deleted by `Deletion Service`. Sets to be 6 months after the message is ingested in the database | Yes |

### Storage Requirements

TODO

## Service Definitions

### 1. Channel Service

#### Channel service methods

- addChannel(channel: Channel) -> void
- removeChannel(channelId: string) -> Channel
- getChannels(size: int) -> Channel[]
- getChannel(channelId: string) -> Channel
- updateChannelTheme(channelId: string, theme: Theme) -> void
- updateChannelOffset(channelId: string, offsetId: string | null) -> void

---

### 2. Message service

The message service retrieves filtered messages from the database

#### Message service methods

- getMatchedMessages(keywordsList: string[], dateFromISOString: string[] | null, theme: Theme) -> Messages[]
- createMessage(message: string) -> string (message ID)

---

### 3. Subscriber service

The subscriber service exposes definitions for the telegram bot client and administrators to manage subscribers

#### Subscriber service methods

- getSubscriber(subscriberId: string) -> Subscriber
- getSubscribers() -> Subscriber[]
- add_subscriber(subscriber: Subscriber) -> string (subscriber ID)
- subscribe(subscriber: Subscriber) -> void
- unsubscribe(subscriber: Subscriber) -> void
- updateSubscriberThemeKeywords(subscriberId: string, theme: Theme, updatedKeywords: string[]) -> void
- updateSubscriberThemeTimestamp(subscriberId: string, theme: Theme, timestampISOString: string | null) -> void

---

### 4. Download service

The download service crawl messages from Telegram `channels` and groups

#### Download service methods

- downloadMessagesFromChannel(channel: Channel, offsetId: string | null) -> Message[]

---

### 5. Notification service

The notification service exposes definitions to send messages through the Telegram Bot to the subscribers

#### Notification service methods

- sendMessage(message: Message, subscriber: Subscriber) -> void

---
