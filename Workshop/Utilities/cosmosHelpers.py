import logging
import json
import re
import azure.functions as func
import os
from azure.cosmos import CosmosClient, PartitionKey
import urllib
import numpy as np
import uuid
import copy
from datetime import datetime, timedelta


from Utilities import cogSearchHelpers



class SCCosmosClient():

    def __init__(self, url=COSMOS_URI, credential=COSMOS_KEY, db_name=COSMOS_DB_NAME, container_name=COSMOS_CONTAINER_NAME):
        
        self.all_fields = [f.name for f in cogsearch_helpers.fields]

        try:
            self.client = CosmosClient(url=url, credential=credential)
            self.partitionKeyPath = PartitionKey(path="/categoryId")
            self.database = self.client.create_database_if_not_exists(id=db_name)

            indexing_policy={ "includedPaths":[{ "path":"/*"}], "excludedPaths":[{ "path":"/\"_etag\"/?"}]}
            
            try:
                self.container = self.database.create_container_if_not_exists(id=container_name, partition_key=self.partitionKeyPath,indexing_policy=indexing_policy)
            except:
                try:
                    self.container = self.database.create_container_if_not_exists(id=container_name, partition_key=self.partitionKeyPath,indexing_policy=indexing_policy)

                except Exception as e:
                    logging.error(f"Encountered error {e} while creating the container")
                    print(f"Encountered error {e} while creating the container")
            
        except:
            print("Failed to initialize Cosmos DB container")
            logging.error("Failed to initialize Cosmos DB container")



    def get_document_by_id(self, doc_id, category_id = COSMOS_CATEGORYID):
        query = "SELECT * FROM documents p WHERE p.categoryId = @categoryId AND p.id = @id"
        params = [dict(name="@categoryId", value=category_id), dict(name="@id", value=doc_id)]

        results = self.container.query_items(query=query, parameters=params, enable_cross_partition_query=False)

        try:
            document = results.next()
            return self.clean_document(document)

        except Exception as e:
            print(f"Cosmos Get Documnet by ID Exception: ID not found {e}")
            logging.warning(f"Cosmos Get Documnet by ID Exception: ID not found {e}")
            return None


    def delete_document(self, doc_id, category_id = COSMOS_CATEGORYID):
        try:
            return self.container.delete_item(doc_id, partition_key=category_id)
        except Exception as e:
            logging.error(f"Cosmos Delete Document Exception: {e}")
            print(f"CosmosDelete Document Exception: {e}")


    def clean_document(self, document):
        document = copy.deepcopy(document)
        for k in list(document.keys()):
            if k not in self.all_fields:
                del document[k]

        return document


    def upsert_document(self, document, category_id = COSMOS_CATEGORYID):

        try:
            document["categoryId"] = category_id
            return self.container.upsert_item(document)
        except Exception as e:
            logging.error(f"Upsert Document Exception: {e}")
            print(f"Upsert Document Exception: {e}")
            return None

