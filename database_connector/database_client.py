import os
from typing import List, Optional

from opensearchpy import OpenSearch
import dotenv

from services.logging_service import LoggingService
from database_connector.database_exception import DatabaseException


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

    def document_exist(self, index_name: str, document_id: str):
        """
        checks if a document with the document_id exist in the index.

        Parameters:
        index_name - name of the index in the database to check the document

        document_id - id of the document in the database

        Raises:
        DatabaseException - when index name is invalid, document is malformed or an internal database error

        Returns:
        True if the document with the document_id exist, false otherwise
        """
        try:
            return self.client.exists(index=index_name, id=document_id)
        except Exception as error:
            self.logging_service.log_error(error_message=error)
            raise DatabaseException("something went wrong with the database")

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

    def read(self, index_name: str, query: dict):
        """
        Performs a search in the index based on the search query

        Parameters:
        index_name - index of the database to perform the search on

        query - internal database key value pairs to perform the search

        Raises:
        DatabaseException - when index name is invalid, document is malformed or an internal database error

        Returns:
        list of matching documents
        """
        try:
            response = self.client.search(
                index=index_name,
                body={"size": self.__MAX_QUERY_SIZE, "query": query},
            )

            self.logging_service.log_info(message=f"READ | index <{index_name}>")

            return self.__clean_hits_response(response)
        except Exception as error:
            self.logging_service.log_error(error_message=error)
            raise DatabaseException("Failed to read documents in index")

    def update(
        self,
        index_name: str,
        document_id: str,
        partial_doc: Optional[dict] = None,
        script_doc: Optional[dict] = None,
    ) -> None:
        """Updates a existing document in the database

        Parameters:
        index_name - index of the document to update

        document_id - id of the document to update

        partial_doc (optional) - dict of key/values in the document to update

        script_doc (optional) - uses the database internal script to update document

        Raises:
        DatabaseException - when index name is invalid, document is malformed or an internal database error

        Returns:
        True if the update operation is successful, False if the document does not exist
        """
        update_log_message = f"UPDATE | index <{index_name}>, document id <{document_id}>"

        document_exists = self.document_exist(index_name=index_name, document_id=document_id)

        if not document_exists:
            return False  # document does not exist, unable to perform update operation

        try:
            if partial_doc is not None:
                self.client.update(index=index_name, id=document_id, body={"doc": partial_doc})

                self.logging_service.log_info(message=update_log_message)

                return

            if script_doc is not None:
                self.client.update(index=index_name, id=document_id, body={"script": script_doc})

                self.logging_service.log_info(message=update_log_message)

                return
        except Exception as error:
            self.logging_service.log_error(error_message=error)
            raise DatabaseException("Failed to update document in index")

    def create(self, index_name: str, document: dict, document_id: Optional[str] = None):
        """Creates a new document in an index in the database


        Parameters:
        index_name - index of the database to add the document

        document - document to add in the index

        document_id (optional) - creates a document with this document_id. If a document already exist
        with this document_id, the document will not be created

        Raises:
        DatabaseException - when index name is invalid, document is malformed or an internal database error


        Returns:
        id of the newly created document, or None if the document is not created
        """
        try:
            if document_id is None:
                response = self.client.index(
                    index=index_name,
                    body=document,
                    refresh=True,  # force refresh of database shards for retrieval
                )

                new_document_id = response["_id"]

                self.logging_service.log_info(message=f"CREATE | index <{index_name}>, document id <{new_document_id}>")

                return new_document_id

            # document_id is given, need to check if document with the document_id already exists
            # if it exists, do not create the document
            document_exists = self.document_exist(index_name=index_name, document_id=document_id)
            if document_exists:
                return None

            self.client.create(index=index_name, body=document, refresh=True, id=document_id)

            self.logging_service.log_info(message=f"CREATE | index <{index_name}>, document id <{document_id}>")

            return document_id

        except Exception as error:
            self.logging_service.log_error(error_message=error)
            raise DatabaseException("Failed to create document in index")
