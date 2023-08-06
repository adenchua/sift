import os
from typing import List

from opensearchpy import OpenSearch
import dotenv

from services.logging_service import LoggingService


dotenv.load_dotenv()
env_host = os.getenv("ENV_OS_HOST") or ""
env_port = os.getenv("ENV_OS_PORT") or 0
env_username = os.getenv("ENV_OS_USERNAME") or ""
env_password = os.getenv("ENV_OS_PASSWORD") or ""


class DatabaseClient:
    __MAX_QUERY_SIZE = 10_000  # OpenSearch max query size

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

        self.logging_service = LoggingService()

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

    def build_query_string(self, query_string_list: List[str]):
        temp = []
        for query_string in query_string_list:
            if query_string.find(" ") != -1:
                transformed_query_string = query_string.replace(" ", " AND ")
                temp.append(f"({transformed_query_string})")
                continue
            temp.append(query_string)

        return (" OR ").join(temp)

    def read(self, index_name: str, query):
        response = self.client.search(
            index=index_name,
            body={"size": self.__MAX_QUERY_SIZE, "query": query},
        )

        self.logging_service.log_info(message=f"READ | index <{index_name}>")

        return self.__clean_hits_response(response)

    def update(self, index_name: str, document_id: str, update_body):
        self.client.update(index=index_name, id=document_id, body=update_body)

        self.logging_service.log_info(
            message=f"UPDATE | index <{index_name}>, document id <{document_id}>"
        )

        # TODO: add in response message

    def create(self, index_name, document, document_id):
        response = self.client.index(
            index=index_name, body=document, id=document_id, refresh=True
        )

        self.logging_service.log_info(
            message=f"CREATE | index <{index_name}>, document id <{document_id}>"
        )

        return response
