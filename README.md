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
- `FastAPI` server running at port `8080`
- background service that starts up a recurring download and notification script
- telegram bot service for client app interaction

Administrators may access all the available api to manage channels and subscribers at `http://0.0.0.0:8080/docs`

## System design

You may refer to the initial system design considerations [here](docs/system-design.md)
