
from math import e
from base_mongodb_service import BaseMongoDBService
import os
import json
import logging
import common_utils 
from pymongo.errors import PyMongoError
import shutil

class BaseIngestionService(BaseMongoDBService):
    
    # Configure the logger for this class
    logger = logging.getLogger(__name__+'.'+__qualname__)
    
    LOAD_METRICS_COLLECTION_NAME = "app_ingestion_load_metrics"
            
    def __init__(self, mongo_user, mongo_password, mongo_host, mongo_db):
        super().__init__(mongo_user, mongo_password, mongo_host, mongo_db)
        
    
        
    def process_apple_workout_files(self, workouts_dir, processed_dir, load_id, check_for_duplicates=True):
            """
            Ingests workout data from the specified directory and returns metrics about the ingested data.

            Parameters:
            workouts_dir (str): The directory containing the workout data.
            processed_dir (str): The directory where the processed workout data will be stored.
            load_id (str): The unique identifier for the data load.

            Returns:
            dict: A dictionary with metrics for each workout type.
            """
            
            ingest_details =  {
                "collections_load_metrics_summary": {},
                "duplicates_summary": {},
                "file_errors": {}
            }            
                
            if not workouts_dir or not os.path.exists(workouts_dir):
                if not os.path.exists(workouts_dir):
                    self.logger.error(f"Workouts directory {workouts_dir} does not exist")
                else:
                    self.logger.error(f"Workouts directory {workouts_dir} is empty")
                return ingest_details
                 
            try:
                # Returns a dictionary of workouts where key is the file name and the value a dict with a single key workouts and value is a list of workouts
                loaded_workouts_data = self._load_apple_health_export_json_files_from_dir(workouts_dir, ingest_details)              
                self.logger.info(f"{len(loaded_workouts_data)} workout files loaded from directory {workouts_dir}")
            except Exception as e:
                self.logger.error(f"Error loading workout files from {workouts_dir}: {e}")
                return ingest_details

            # Load the Apple Health Workouts data into the Health Datalake. 
            # The ingest details capture allows us to capture metrics and other details like duplicates and errors
            self._ingest_apple_health_workouts(loaded_workouts_data, ingest_details, workouts_dir, processed_dir, load_id, check_for_duplicates )

                 
            return ingest_details    
    
    
    def process_apple_health_metric_files(self, metrics_dir, processed_dir, load_id, check_for_duplicates=True) :
            """
            Ingests metrics data from the specified directory and returns metrics about the ingested data.

            Parameters:
            metrics_dir (str): The directory containing the metrics data.
            processed_dir (str): The directory where the processed files will be moved to.
            load_id (str): The ID of the current load.

            Returns:
            dict: A dictionary with metrics for each metric type.
            """
            
            ingest_details =  {
                "collections_load_metrics_summary": {},
                "duplicates_summary": {},
                "file_errors": {}
            }
            
            if not metrics_dir or not os.path.exists(metrics_dir):
                if not metrics_dir:
                    self.logger.info("Health-Metrics directory is not set. Skipping health-metrics ingestion")
                else:
                    self.logger.error(f"Health-Metrics directory {metrics_dir} does not exist")
                return ingest_details
                    
            try:
                # Returns a dictionary of metrics where key is the file name and the value a dict with a single key metrics and value is a list of metrics
                loaded_apple_health_metrics_data = self._load_apple_health_export_json_files_from_dir(metrics_dir, ingest_details)
                self.logger.info(f"{len(loaded_apple_health_metrics_data)} metric files loaded from directory {metrics_dir}")
            except Exception as e:
                self.logger.error(f"Error loading metric files from {metrics_dir}: {e}")
                return ingest_details

            # Load the Apple Health Workouts data into the Health Datalake.
            # complete_load_metrics_summary is a dictionary with 3 keys: collections_load_metrics_summary, duplicates_summary, file_errors. 
            # The collections_load_metrics_summary is a dictionary with the collection name as the key and the value is a dictionary with the metrics for the collection
            self._ingest_apple_health_metrics(loaded_apple_health_metrics_data, ingest_details, metrics_dir, processed_dir, load_id, check_for_duplicates)
        
            
            return ingest_details

 
    def _load_apple_health_export_json_files_from_dir(self, dir_path, ingest_details) -> dict:
        """
        Load Apple Health export JSON files from a directory.
        Args:
            dir_path (str): The path to the directory containing the JSON files.

        Returns:
            dict: A dictionary containing the loaded Apple Health data, where the keys are the filenames and the values are the data extracted from the files as json/dict
        """
        
        loaded_apple_health_data = {}

        if not dir_path or  not os.path.exists(dir_path):
            self.logger.error(f"Directory {dir_path} does not exist or is empty")
            return loaded_apple_health_data
             
       # Order the files by the date in their filename so we process the oldest files first
        new_files = [f for f in os.listdir(dir_path) if f.endswith('.json')]
        new_files = common_utils.sort_files_by_date(new_files)
  
        for filename in new_files:
            file_path = os.path.join(dir_path, filename)
            
            try:
                with open(file_path, 'r') as file:
                    # if, workouts, it is  is dict with key "workouts" and value is a list of workouts: {"data":{"workouts":[]}}
                    # if health metrics, it is  is dict with key "metrics" and value is a list of metrics: {"data":{"metrics":[]}}                    
                    health_data = json.load(file).get("data", [])
                    loaded_apple_health_data[filename] = health_data
            except Exception as e:
                error_msg = f"Failed to load {file_path} into a json: {e}"
                self.logger.error(error_msg)
                # Add the file errors to the ingest_details file_errors dictionary
                ingest_details["file_errors"].setdefault(filename, []).append(error_msg)
                continue
        return loaded_apple_health_data
    
    


    # Takes a dictionary of workouts where key is the file name and the value workouts dict
    def _ingest_apple_health_workouts(self, workouts_by_file_dict, ingest_details, landing_dir, processed_dir, load_id, check_for_duplicates=True):
               
                
        # workouts_dict_json: A dictionary containing the workout data. E.g: {filename : {workouts: [<workout>, <workout>, ...] }}
        # so workouts_dict is  asingle dict: {workouts: [ <workout>, <workout>, ...]}}
        for filename, workouts_dict in workouts_by_file_dict.items():
            
            self.logger.info(f"Processing file[ {filename}] of workouts for ingestion into the Health Datalake.")

            workouts_list = workouts_dict.get("workouts", [])
            if not workouts_list:
                # This means the the json has data element and workouts element but the list of workouts is empty
                empty_workouts_file_msg = f"No workouts found in file {filename} for load_id {load_id}. File looks like: {{\"data\":{{\"workouts\":[]}}}} "
                self.logger.info(empty_workouts_file_msg)
                # Use the file_errors dictionary to add the error message for the file that has no workouts
                ingest_details["file_errors"].setdefault(filename, []).append(empty_workouts_file_msg)
                continue # break out of the current file iteration and move to the next file
            
            # Group workouts by type (e.g: indoor_run, cycle, tennis, etc..). Note that work workouts_dict.get("workouts", []) is a list of workouts
            grouped_workouts = self._group_workouts_by_type(workouts_list)
            
            for workout_type, workouts in grouped_workouts.items():
                    
                collection_name = f"workouts_{workout_type.replace(' ', '_').lower()}"                
                new_load_details = self._process_and_insert_workouts(workouts, filename, collection_name, load_id, check_for_duplicates)

                self.logger.info(f"Collection: {collection_name}, Inserted: {new_load_details['inserted']}, Duplicates/Ignored: {new_load_details['duplicates']}")
                        
                self._aggregate_load_metrics(ingest_details["collections_load_metrics_summary"], collection_name, new_load_details)
                self._aggregate_duplicates(ingest_details["duplicates_summary"], new_load_details, filename)
        
            self._mark_file_as_processed(filename, landing_dir, processed_dir)
    
    
    # Takes a dictionary of workouts where key is the file name and the value workouts dict    
    def _ingest_apple_health_metrics(self, metrics_by_file_dict, ingest_details, landing_dir, processed_dir, load_id, check_for_duplicates=True):
        
        # metrics_by_file_dict: E.g: {filename : {"metrics":[<metric>, <metric>]}} }
        # so metrics_dict is  asingle dict: {"metrics":[<metric>, <metric>]}
        for filename, metrics_dict in metrics_by_file_dict.items():
            
            self.logger.info(f"Processing file[ {filename}] of health metrics for ingestion into the Health Datalake.")
            
            metrtics_list = metrics_dict.get("metrics", [])
            if not metrtics_list:
                # This means the the json has data element and metrics element but the list of metrics is empty
                empty_metrics_file_msg = f"No metrics found in file {filename} for load_id {load_id}. File looks like: {{\"data\":{{\"metrics\":[]}}}} "
                self.logger.info(empty_metrics_file_msg)
                # Use the file_errors dictionary to add the error message for the file that has no metrics
                ingest_details["file_errors"].setdefault(filename, []).append(empty_metrics_file_msg)
                continue # break out of the current file iteration and move to the next file
            
            for metric in metrtics_list:  
                collection_name = f"metric_{metric['name'].replace(' ', '_').lower()}"                
               
                load_details = self._process_and_insert_metric_data(metric, filename, collection_name, load_id, check_for_duplicates)
                
                self.logger.info(f"Collection: {collection_name}, Inserted: {load_details['inserted']}, Duplicates/Ignored: {load_details['duplicates']}")
                
                self._aggregate_load_metrics( ingest_details["collections_load_metrics_summary"], collection_name, load_details)
                self._aggregate_duplicates(ingest_details["duplicates_summary"], load_details, filename)
            
            self._mark_file_as_processed(filename, landing_dir, processed_dir)
            
    
    def _process_and_insert_workouts(self, workouts, filename, collection_name, load_id, check_for_duplicates=True):
        """
        Processes and inserts a list of workouts into MongoDB, avoiding duplicates.
        Updates the metrics summary with the count of new and duplicate records.
        Also, collects lists of duplicate and failed records.

        Parameters:
            workouts (list): A list of workout data dictionaries.
            filename (str): The name of the file being processed.
            collection_name (str): The MongoDB collection name.
            load_id (int): The ID of the current load.
            check_for_duplicates (bool, optional): Flag indicating whether to check for duplicates. Defaults to True.

        Returns:
            dict: Summary of the insertion process including min/max dates, count of new and duplicate records, and lists of duplicate and failed records.
        """
        if not workouts:
            return {'processed_file': filename, 'min_date': None, 'max_date': None, 'inserted': 0, 'duplicates': 0, 'duplicate_records': []}

        duplicate_workouts = []

        if check_for_duplicates:
            latest_end_date = self._get_latest_end_date(collection_name, "end")
            new_workouts = [workout for workout in workouts if workout["end"] > latest_end_date] if latest_end_date else workouts
            duplicate_workouts = self._find_workout_duplicates(workouts, collection_name, latest_end_date)
        else:
            new_workouts = workouts

        duplicate_count = len(duplicate_workouts)

        if new_workouts:
            min_start_date, max_end_date = self.get_workouts_date_range(new_workouts)  
            new_workouts = self._add_load_id_and_filename_to_workouts(load_id, filename, new_workouts)

            try:
                insert_result = self.mongo_health_lake[collection_name].insert_many(new_workouts)
                inserted_count = len(insert_result.inserted_ids)
            except Exception as e:
                self.logger.error(f"Error inserting workouts into collection {collection_name}: {e}")
                min_start_date, max_end_date, inserted_count = None, None, 0

        else:
            min_start_date, max_end_date, inserted_count = None, None, 0

        summary_metrics = {
            'processed_file': filename, 
            'min_date': min_start_date, 
            'max_date': max_end_date, 
            'inserted': inserted_count, 
            'duplicates': duplicate_count,
            'duplicate_records': duplicate_workouts
        }

        return summary_metrics

    def _find_workout_duplicates(self, workouts, collection_name, latest_end_date):
        duplicate_workouts = []
        if(latest_end_date):
            for workout in workouts:
                if workout["end"] <= latest_end_date:
                    workout_with_collection_name = {"collection_name": collection_name, **workout}  
                    duplicate_workouts.append(workout_with_collection_name)
        return duplicate_workouts

    def _find_health_metric_duplicates(self, metric, collection_name, latest_end_date):
        duplicate_metrics = []
        if(latest_end_date):
            for entry in metric["data"]:
                if entry["date"] <= latest_end_date:
                    entry_with_collection_name = {"collection_name": collection_name, **entry}  
                    duplicate_metrics.append(entry_with_collection_name)
        return duplicate_metrics

    def _process_and_insert_metric_data(self, metric, filename, collection_name, load_id, check_for_duplicates=True):
        """
        Processes and inserts metric data into MongoDB, avoiding duplicates.
        Updates the metrics summary with the count of new and duplicate records.
        Also, collects lists of duplicate and failed records.

        Parameters:
            metric (dict): The metric data.
            filename (str): The name of the file being processed.
            collection_name (str): The MongoDB collection name.
            load_id (int): The ID of the current load.
            check_for_duplicates (bool, optional): Flag indicating whether to check for duplicates. Defaults to True.

        Returns:
            dict: Summary of the insertion process including min/max dates, count of new and duplicate records, and lists of duplicate and failed records.
        """
        if not metric.get("data"):
            return {'processed_file': filename, 'min_date': None, 'max_date': None, 'inserted': 0, 'duplicates': 0, 'duplicate_records': []}

        duplicate_metrics = []

        if check_for_duplicates:
            latest_end_date = self._get_latest_end_date(collection_name, "date")
            new_health_metrics = [entry for entry in metric["data"] if entry["date"] > latest_end_date] if latest_end_date else metric["data"]
            duplicate_metrics = self._find_health_metric_duplicates(metric, collection_name, latest_end_date)
        else:
            new_health_metrics = metric["data"]

        duplicate_count = len(duplicate_metrics)

        if new_health_metrics:
            min_date, max_date = self.get_metrics_date_range(new_health_metrics)
            new_health_metrics = self._add_load_id_and_filename_to_metrics(load_id, filename, new_health_metrics)

            try:
                insert_result = self.mongo_health_lake[collection_name].insert_many(new_health_metrics)
                inserted_count = len(insert_result.inserted_ids)
            except Exception as e:
                self.logger.error(f"Error inserting metrics into collection {collection_name}: {e}")
                min_date, max_date, inserted_count = None, None, 0
        else:
            min_date, max_date, inserted_count = None, None, 0

        summary_metrics = {
            'processed_file': filename, 
            'min_date': min_date, 
            'max_date': max_date, 
            'inserted': inserted_count, 
            'duplicates': duplicate_count,
            'duplicate_records': duplicate_metrics        
        }

        return summary_metrics


    
    def get_workouts_date_range(self, new_workouts):
        if not new_workouts:
            return None, None  # Handle empty list

        min_start_date = min(workout["start"] for workout in new_workouts)
        max_end_date = max(workout["end"] for workout in new_workouts)

        return min_start_date, max_end_date

    def _add_load_id_and_filename_to_workouts(self, load_id, filename, new_workouts):
        return [{**workout, "processed_file": filename, "load_id": load_id } for workout in new_workouts]  

    def get_metrics_date_range(self, metrics):
        if not metrics:
            return None, None  # Handle empty list

        dates = [metric["date"] for metric in metrics]
        min_date = min(dates)
        max_date = max(dates)
        return min_date, max_date

    def _add_load_id_and_filename_to_metrics(self, load_id, filename, new_metrics):
        return [{**metric, "processed_file": filename, "load_id": load_id} for metric in new_metrics]


    def _mark_file_as_processed(self, filename, landing_dir, processed_dir):
        """
        Marks a file as processed by renaming it with a 'processed_' suffix.

        Args:
            filename (str): The filename to mark as processed.
            directory (str): The directory where the file is located.
        """
        original_file_path = os.path.join(landing_dir, filename)
        # update the filename to include current datatime suffix
        new_filename = f"{filename.split('.')[0]}_processed_{common_utils.current_time_local('%Y%m%d%H%M%S')}.json"
        processed_file_path = os.path.join(processed_dir, new_filename)

    
        shutil.move(original_file_path, processed_file_path)
        self.logger.info(f"Finished ingesting into Health Lake. Moved {filename} to processed directory: {processed_file_path}")


    def _get_latest_end_date(self, collection_name, date_element):
        """
        Retrieves the latest end date from the specified collection.

        Args:
            collection_name (str): The name of the collection.

        Returns:
            datetime: The latest end date in the collection.
        """
        collection = self.mongo_health_lake[collection_name]
        
        latest_record = collection.find_one(sort=[(date_element, -1)])
        return latest_record.get(date_element) if latest_record else None


    def _create_load_summary(self, load_type, workout_ingest_details, health_metrics_ingest_detals,  load_start_time, load_end_time, load_id):
        """
        Creates a summary of the load process.

        Args:
            load_type (str): The type of load ('initial' or 'incremental').
            load_metrics (dict): The metrics collected during the load.

        Returns:
            dict: A summary of the load process.
        """
       
        workout_files_set = set()
        health_metric_files_set = set()
        
        total_workouts_inserted=0
        total_workouts_duplicates=0
        total_health_metrics_inserted=0
        total_health_metrics_duplicates=0
        total_inserted=0
        total_duplicates=0
        
        # Get workout_ingest_metrics and related metrics
        if "collections_load_metrics_summary" in workout_ingest_details:
            workout_collections_metrics = workout_ingest_details["collections_load_metrics_summary"]
            if workout_collections_metrics:
                
                for collection_metrics in workout_collections_metrics.values():
                    for file_name in collection_metrics["processed_files"]:
                        workout_files_set.add(file_name)
               
                # Calculate totals across all collections for inserts and duplicates.
                total_workouts_inserted = sum(collection_metrics['inserted'] for collection_metrics in workout_collections_metrics.values())
                total_workouts_duplicates = sum(collection_metrics['duplicates'] for collection_metrics in workout_collections_metrics.values())

        # Get health_metrics and related metrics
        if "collections_load_metrics_summary" in health_metrics_ingest_detals:
            health_metric_collections_metrics = health_metrics_ingest_detals["collections_load_metrics_summary"]
            if health_metric_collections_metrics:
                for collection_metrics in health_metric_collections_metrics.values():
                    for file_name in collection_metrics["processed_files"]:
                        health_metric_files_set.add(file_name)
                        
                # Calculate totals across all collections for inserts and duplicates.
                total_health_metrics_inserted = sum(collection_metrics['inserted'] for collection_metrics in health_metric_collections_metrics.values())
                total_health_metrics_duplicates = sum(collection_metrics['duplicates'] for collection_metrics in health_metric_collections_metrics.values())        


        # Calculate overall totals
        total_inserted = total_workouts_inserted + total_health_metrics_inserted
        total_duplicates = total_workouts_duplicates + total_health_metrics_duplicates
       
        # Calculate the files processed for the entire load, workouts and health metrics
        all_processed_files_set = workout_files_set.union(health_metric_files_set)
        all_processed_files_str = ','.join(all_processed_files_set)
        all_workout_files_str = ','.join(workout_files_set)
        all_health_metric_files_str = ','.join(health_metric_files_set)

        

        return {
            'load_id': load_id, 
            'load_type': load_type,
            'load_start_datetime': load_start_time,
            'load_end_datetime': load_end_time,
            'total_inserted': total_inserted,
            'total_duplicates': total_duplicates,
            'processed_files': all_processed_files_str,
            'workout_metrics': {
                'processed_files': all_workout_files_str,
                'total_inserted': total_workouts_inserted,
                'total_duplicates': total_workouts_duplicates,
                **workout_collections_metrics

            },
            'health_metrics': {
                'processed_files': all_health_metric_files_str,
                'total_inserted': total_health_metrics_inserted,
                'total_duplicates': total_health_metrics_duplicates,
                **health_metric_collections_metrics
            }
        }

        
    def _store_load_summary(self, load_summary):
        """
        Stores the load summary into a MongoDB collection.

        Args:
            load_summary (dict): The load summary to store.
        """
        try:
            load_summary_collection = self.mongo_health_lake[self.LOAD_METRICS_COLLECTION_NAME]
            load_summary_collection.insert_one(load_summary)
            self.logger.info("Load summary successfully stored in MongoDB.")
        except PyMongoError as e:
            self.logger.error(f"Failed to store load summary in MongoDB: {e}")

    def get_workout_collections(self):
        workout_collections = [collection for collection in self.mongo_health_lake.list_collection_names() if collection.startswith("workouts")]
        return workout_collections

    def get_metric_collections(self):
        metric_collections = [collection for collection in self.mongo_health_lake.list_collection_names() if collection.startswith("metric")]
        return metric_collections   
    
 
    def _aggregate_load_metrics(self, collections_load_metrics_summary, collection_name, new_load_details):
        
        # Initialize collection entry if it doesn't exist
        if collection_name not in collections_load_metrics_summary:
            collections_load_metrics_summary[collection_name] = {
                "min_date": None,
                "max_date": None,
                "inserted": 0,
                "duplicates": 0,
                "processed_files":[]
            }

        min_date_metric = new_load_details["min_date"]   
        max_date_metric = new_load_details["max_date"]   
        inserted = new_load_details["inserted"]
        duplicates = new_load_details["duplicates"]
        processed_file = new_load_details["processed_file"]
        
        # Aggregate metrics
        collection_load_metrics = collections_load_metrics_summary[collection_name]
        
        if min_date_metric:
            collection_load_metrics["min_date"] = min(collection_load_metrics["min_date"], min_date_metric) if collection_load_metrics["min_date"] else min_date_metric
        
        if max_date_metric:
            collection_load_metrics["max_date"] = max(collection_load_metrics["max_date"], max_date_metric) if collection_load_metrics["max_date"] else max_date_metric
        
        collection_load_metrics["inserted"] += inserted
        collection_load_metrics["duplicates"] += duplicates
        # Want to add the processed file to the set of processed files for the collection. Using Set since we want the files to be unique
        collection_load_metrics["processed_files"].append(processed_file)

            
    def _aggregate_duplicates(self, duplicates_summary, new_load_details, filename):
        # Aggregrate duplicates key off the filename
        if new_load_details["duplicate_records"]:
            if filename not in duplicates_summary:
                duplicates_summary[filename] = []
            duplicates_summary[filename].extend(new_load_details["duplicate_records"])
            
    
    def _group_workouts_by_type(self, workouts):
        """
        Groups workouts by type.

        Parameters:
        workouts (list): A list of workout records.

        Returns:
        dict: A dictionary with workout types as keys and list of workouts as values.
        """
        grouped_workouts = {}
        for workout in workouts:
            workout_type = workout["name"]
            if workout_type not in grouped_workouts:
                grouped_workouts[workout_type] = []
            grouped_workouts[workout_type].append(workout)

        return grouped_workouts


    def _delete_all_collections(self, delete_load_metrics_collection=False):
        """
        Deletes all collections in the database except for the table that captures the load metrics unless specified.
        """
        if(delete_load_metrics_collection):
            self.mongo_health_lake.drop_collection(self.LOAD_METRICS_COLLECTION_NAME)
            self.logger.info(f"Deleted collection {self.LOAD_METRICS_COLLECTION_NAME}")
        
        workout_collections = self.get_workout_collections()
        for collection in workout_collections:
            self.mongo_health_lake.drop_collection(collection)
            self.logger.info(f"Deleted collection {collection}")

        metric_collections = self.get_metric_collections()
        for collection in metric_collections:
            self.mongo_health_lake.drop_collection(collection)
            self.logger.info(f"Deleted collection {collection}")

    class InitializationError(Exception):
        """Exception raised when initialization conditions are not met."""
        pass

    



