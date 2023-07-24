import os
from typing import List

from opensearchpy import OpenSearch
import dotenv

from utils import date_helper

dotenv.load_dotenv()
env_host = os.getenv("ENV_OS_HOST") or ""
env_port = os.getenv("ENV_OS_PORT") or 0
env_username = os.getenv("ENV_OS_USERNAME") or ""
env_password = os.getenv("ENV_OS_PASSWORD") or ""


class DatabaseClient:
    __MAX_QUERY_SIZE = 10_000  # elasticsearch max query size

    def __init__(self):
        self.client = OpenSearch(
            hosts=[{"host": env_host, "port": env_port}],
            http_compress=True,  # enables gzip compression for request bodies
            http_auth=(env_username, env_password),
            use_ssl=True,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )

    def __clean_hits_response(self, opensearch_response):
        """
        The default opensearch response for search query wraps the result with hits.hits
        and other verbose information such as _index and _score. This method takes in the
        opensearch search response, removes the unnecessary keys and flattens the object
        """
        result = []
        object_list = opensearch_response["hits"]["hits"]

        for object in object_list:
            temp = {**object["_source"], "id": object["_id"]}
            result.append(temp)

        return result

    def __build_query_string(self, query_string_list: List[str]):
        temp = []
        for query_string in query_string_list:
            if query_string.find(" ") != -1:
                transformed_query_string = query_string.replace(" ", " AND ")
                temp.append(f"({transformed_query_string})")
                continue
            temp.append(query_string)

        return (" OR ").join(temp)

    def ingest_message(self, document, document_id):
        response = self.client.index(
            index="message", body=document, id=document_id, refresh=True
        )
        print(response)

    def get_channels(self):
        query = {"size": self.__MAX_QUERY_SIZE, "query": {"match_all": {}}}
        response = self.client.search(index="channel", body=query)
        return self.__clean_hits_response(response)

    def get_users(self):
        query = {
            "size": self.__MAX_QUERY_SIZE,
            "query": {"term": {"is_subscribed": True}},
        }
        response = self.client.search(index="subscriber", body=query)
        return self.__clean_hits_response(response)

    def update_channel(self, channel_id, updated_fields):
        response = self.client.update(
            index="channel", id=channel_id, body={"doc": updated_fields}
        )
        print(response)

    def update_subscriber_theme_timestamp(self, subscriber_id: str, theme: str):
        response = self.client.update(
            index="subscriber",
            id=subscriber_id,
            body={
                "script": {
                    "lang": "painless",
                    "source": """for(int i=0;i<ctx._source.keywords.length;i++){
                if(ctx._source.keywords[i].theme == params.theme){ctx._source.keywords[i].last_crawl_timestamp = params.new_value;}
                }""",
                    "params": {
                        "theme": theme,
                        "new_value": date_helper.get_current_iso_datetime(),
                    },
                },
            },
        )
        print(response)

    def get_messages(self, query_string_list: List[str], theme: str, iso_date=None):
        # if timestamp is not provided, send messages after today 0000hrs
        gte_datetime = (
            date_helper.get_today_iso_date() if iso_date is None else iso_date
        )
        query_string = self.__build_query_string(query_string_list)
        query = {
            "size": self.__MAX_QUERY_SIZE,
            "query": {
                "bool": {
                    "must": [
                        {"query_string": {"query": query_string}},
                        {"term": {"themes": {"value": theme}}},
                    ],
                    "filter": [{"range": {"timestamp": {"gte": gte_datetime}}}],
                }
            },
        }

        response = self.client.search(index="message", body=query)
        return self.__clean_hits_response(response)


database_client = DatabaseClient()
