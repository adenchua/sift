from opensearchpy import OpenSearch
import dotenv
import os

dotenv.load_dotenv()
env_host = os.getenv("ENV_OS_HOST") or ""
env_port = os.getenv("ENV_OS_PORT") or 0
env_username = os.getenv("ENV_OS_USERNAME") or ""
env_password = os.getenv("ENV_OS_PASSWORD") or ""


class OpenSearchClient:
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

    def ingest_message(self, document, document_id):
        response = self.client.index(
            index="message", body=document, id=document_id, refresh=True
        )
        print(response)

    def get_channels(self):
        query = {"size": 10_000, "query": {"match_all": {}}}
        response = self.client.search(index="channel", body=query)
        return self.__clean_hits_response(response)

    def get_users(self):
        query = {"size": 10_000, "query": {"match_all": {}}}
        response = self.client.search(index="subscriber", body=query)
        return self.__clean_hits_response(response)

    def update_channel(self, channel_id, updated_fields):
        response = self.client.update(
            index="channel", id=channel_id, body={"doc": updated_fields}
        )
        print(response)


opensearch_client = OpenSearchClient()
