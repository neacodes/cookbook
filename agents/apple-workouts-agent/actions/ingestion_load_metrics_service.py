
from requests import delete
from base_mongodb_service import BaseMongoDBService
import logging
from pymongo.errors import PyMongoError


class IngestionLoadMetricsService(BaseMongoDBService):
    
    LOAD_METRICS_COLLECTION_NAME = "app_ingestion_load_metrics"
    
    # Configure the logger for this class
    logger = logging.getLogger(__name__+'.'+__qualname__)
    
    def __init__(self, mongo_user, mongo_password, mongo_host, mongo_db):
        super().__init__(mongo_user, mongo_password, mongo_host, mongo_db)
        
        
    def get_last_run(self):
        """
        Returns the last run of the ingestion load metrics.
        
        Returns:
            dict: The last run of the ingestion load metrics.
        """
        try:
            
            latest_run = self.mongo_health_lake[self.LOAD_METRICS_COLLECTION_NAME].find_one(sort=[('load_end_datetime', -1)])
            return latest_run
        except PyMongoError as e:
            self.logger.error(f"Error getting latest run of ingestion load metrics: {e}")
            return None
   
   
    def get_load_metrics_by_load_id(self, load_id):
        """
        Returns the load metrics with the specified load_id
        
        Args:
            load_id (str): The load_id to query.
            
        Returns:
            dict: The load metrics with the specified load_id
        """
        try:
            load_metrics = self.mongo_health_lake[self.LOAD_METRICS_COLLECTION_NAME].find_one({"load_id": load_id})
            return load_metrics
        except PyMongoError as e:
            self.logger.info(f"Error getting load metrics by load_id: {e}")
            return None
   
    def get_documents_by_load_id(self, load_id, collection_name = None ):
        """
        Returns the documents in the collection with the specified load_id
        
        Args:
            collection_name (str): The name of the collection to query.
            load_id (str): The load_id to query.
            
        Returns:
            list: The documents in the collection with the specified load_id
        """
        try:
            documents = []
            if collection_name is None:
                # Iterate through all the collections in the Health Data Lake and get the documents with the specified load_id
                for collection in self.mongo_health_lake.list_collection_names():
                    if collection != self.LOAD_METRICS_COLLECTION_NAME:
                        documents.extend(self.mongo_health_lake[collection].find({"load_id": load_id}))    
            else:
                documents = self.mongo_health_lake[collection_name].find({"load_id": load_id})
            return list(documents)
        except PyMongoError as e:
            self.logger.info(f"Error getting documents by load_id in collection {collection_name}: {e}")
            return []
        
    
    def get_total_num_of_docs_in_health_data_lake_by_load_id(self, load_id):
        """Returns the total number of documents across all the collections in the Health Data Lake except for the ingestion load metrics collection."""
        try:
            total_docs = 0
            for collection in self.mongo_health_lake.list_collection_names():
                if collection != self.LOAD_METRICS_COLLECTION_NAME:
                    total_docs += self.mongo_health_lake[collection].count_documents({"load_id": load_id})
            return total_docs
        except PyMongoError as e:
            self.logger.error(f"Error getting total number of documents in Health Data Lake: {e}")
            return 0
        
    def get_total_num_of_docs_in_health_data_lake(self):
        """Returns the total number of documents across all the collections across all loads in the Health Data Lake except for the ingestion load metrics collection."""
        try:
            total_docs = 0
            for collection in self.mongo_health_lake.list_collection_names():
                if collection != self.LOAD_METRICS_COLLECTION_NAME:
                    total_docs += self.mongo_health_lake[collection].count_documents({})
            return total_docs
        except PyMongoError as e:
            self.logger.error(f"Error getting total number of documents in Health Data Lake: {e}")
            return 0    

        
        
    def delete_health_data_docs_by_load_id(self, load_id):
        """Deletes all the documents in the Health Data Lake with the specified load_id. and returns the number of documents deleted."""
        deleted_docs = 0
        try:
            for collection in self.mongo_health_lake.list_collection_names():
                if collection != self.LOAD_METRICS_COLLECTION_NAME:
                    deleted_docs += self.mongo_health_lake[collection].delete_many({"load_id": load_id}).deleted_count
        except PyMongoError as e:
            self.logger.error(f"Error deleting health data documents by load_id: {e}")
            
        return deleted_docs
        
    def reset_health_data_lake_to_initial_load(self, load_id_of_inital_load):
        """Deletes all the documents in the Health Data Lake except for the  specified load_id of the initial load."""
        
        # First check if load_id exists and the load is an initial load. If not, return 0
        incremental_load_details = self.mongo_health_lake[self.LOAD_METRICS_COLLECTION_NAME].find_one({"load_id": load_id_of_inital_load})
        if incremental_load_details is None or incremental_load_details["load_type"] != "initial":
            raise ValueError(f"Error resetting health data lake to initial run: The load_id {load_id_of_inital_load} is not an incremental load.")
        
        deleted_docs = 0
        try:
            for collection in self.mongo_health_lake.list_collection_names():
                if collection != self.LOAD_METRICS_COLLECTION_NAME:
                    deleted_docs += self.mongo_health_lake[collection].delete_many({"load_id": {"$ne": load_id_of_inital_load}}).deleted_count
            self.logger.info(f"Deleted {deleted_docs} documents from Health Data Lake based on reset initial load id[{load_id_of_inital_load}]")    
        except PyMongoError as e:
            self.logger.error(f"Error resetting health data lake to initial load: {e}")
            
        return deleted_docs

    def reset_health_data_lake_to_incremental_run(self, incremental_load_id):
        "Deletes all the documents in the Health Data Lake for all load_ids whose load_start_datetime is greater than the load_start_datetime of the incremental_load_id"
        
        # First check if load_id exists and the load is an incremental load. If not, return 0
        incremental_load_details = self.mongo_health_lake[self.LOAD_METRICS_COLLECTION_NAME].find_one({"load_id": incremental_load_id})
        if incremental_load_details is None or incremental_load_details["load_type"] != "incremental":
            raise ValueError(f"Error resetting health data lake to incremental run: The load_id {incremental_load_id} is not an incremental load.")

        # First find all load_ids whose load_start_datetime is greater than the load_start_datetime of the incremental_load_id and then for each of these load_ids, delete all the documents in the Health Data Lake with that load_id.
        deleted_docs = 0
        try:
            # find the load_details of the incremental_load_id and get its load_start_datetime
            incremental_load_start_datetime = incremental_load_details["load_start_datetime"]
            # get all load_ids whose load_start_datetime is greater than the load_start_datetime of the incremental_load_id and then for each of these load_ids, delete all the documents in the Health Data Lake with that load_id.
            
            load_ids_to_delete = self.mongo_health_lake[self.LOAD_METRICS_COLLECTION_NAME].find({"load_start_datetime": {"$gt": incremental_load_start_datetime}}, {"load_id": 1})
            load_ids_to_delete_count = self.mongo_health_lake[self.LOAD_METRICS_COLLECTION_NAME].count_documents({"load_start_datetime": {"$gt": incremental_load_start_datetime}})
            self.logger.info(f"{load_ids_to_delete_count} incremental loads of data to be be deleted based on reset incremental load id[{incremental_load_id}]")
            
            for load_id in load_ids_to_delete:
                deleted_docs += self.delete_health_data_docs_by_load_id(load_id["load_id"]) 
        except PyMongoError as e:
            self.logger.error(f"Error resetting health data lake to incremental run: {e}")
            
        return deleted_docs
    