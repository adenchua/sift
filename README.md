# Sift

## General information

Sift is a telegram notification system that sends you a message whenever certain telegram channels/groups mentions your keyword of interest.

This is a personal project to solve a first-world problem; There are plenty of curators on telegram channels/groups that post good (food, travel etc) deals daily, yet reading through these messages to look for specific deals take too much time. I developed this application that takes in a list of user input keywords and if it matches any messages, it sends a notification to the subscriber.

## Technology stack

| Technology  | Explanation |
| ------------- | ------------- |
| FastAPI  | Api server to manage channels and subscribers |
| OpenSearch  | Database which allow powerful search queries and tokenization features |

The backend is written in `Python 3.9.6`

## Setup

### Installation for usage using Docker

- Docker is required to run this application
- Telegram API keys are needed to download messages from channels

Create an `.env` file at the root level with reference from the provided `.env.template`

Simply run `docker-compose up --build -d` at the root folder. This sets up following:

- `opensearch` database at port `9200`
- `kibana` dashboard to visualise data and manage indices at port `5601`
- `FastAPI` server running at port `8080`

Create database indices in `opensearch` using the mappings found in `/backend/database_connector/mappings`

You may access all the available api at `http://0.0.0.0:8080/docs`

## System design

![System architecture](/docs/sift-system-architecture.jpg)

- The database client acts as an interface between the database and the services. It performs logging and data cleaning for read operations.
- The notification service retrieves all active subscribers and performs a keyword search on telegram messages sent after a timestamp. Any matched messages will be sent to
the subscriber.
- The message crawl service retrieves all the channels from the database, downloads messages from telegram and ingest them to the database.

## Future enhancements

- A client facing frontend web page to manage subscribers and channels
- A notification queue system to better manage notifications
- A channel discovery feature to discover more channels and groups
- Message crawling from Telegram groups
- Better logging and analytic features for usage and monitoring
- Deletion service to cleanup old messages
