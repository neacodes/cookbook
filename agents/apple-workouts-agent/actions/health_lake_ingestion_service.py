import json
from base_ingestion_service import BaseIngestionService 

import logging

import common_utils 
from s3_utils import S3Utils
import shutil
import os



class HealthLakeIngestionService(BaseIngestionService):
    
    # Configure the logger for this class
    logger = logging.getLogger(__name__+'.'+__qualname__)
                
    def __init__(self, mongo_user, mongo_password, mongo_host, mongo_db, s3_bucket=None, 
                 s3_workout_source_prefix=None, s3_workout_processed_prefix=None,
                 s3_health_metrics_source_prefix=None, s3_health_metrics_processed_prefix=None):
        
        super().__init__(mongo_user, mongo_password, mongo_host, mongo_db)
        
        self.s3_bucket = s3_bucket
        self.s3_workout_source_prefix = s3_workout_source_prefix
        self.s3_workout_processed_prefix = s3_workout_processed_prefix
        self.s3_health_metrics_source_prefix = s3_health_metrics_source_prefix
        self.s3_health_metrics_processed_prefix = s3_health_metrics_processed_prefix
        
        if self.s3_bucket:
            self.s3_utils = S3Utils()
            self.logger.info(f"Configured S3 client for bucket {self.s3_bucket}")   
        else:
            self.s3_utils = None
        
        

  
    def ingest_apple_health_data_initial_load(self, workouts_dir=None, metrics_dir=None, 
                                              workouts_processed_dir= None, health_metrics_processed_dir = None, 
                                              workouts_duplicate_dir = None, health_metrics_duplicate_dir = None,
                                              workouts_error_dir = None, health_metrics_error_dir = None,
                                              delete_all_collections = False, source_type="FILE"):
        """
        Performs the initial load of Apple Health data into the Health Datalake.

        Args:
            workouts_dir (str): Directory containing workout data.
            metrics_dir (str): Directory containing metrics data.

        Returns:
            dict: A dictionary containing the metrics of the loaded data.

        Raises:
            InitializationError: If the data lake already contains collections or directories are invalid.
        """
        
        if source_type == "S3"  and not self.s3_utils:
            error_message = "S3 client is not configured. Cannot download files from S3."
            self.logger.error(error_message)
            raise self.InitializationError(error_message)
        
        
        if delete_all_collections:
            self.logger.info("Deleting all collections in the database before starting the initial load.")
            self._delete_all_collections(True)
        
        elif self.get_workout_collections() or self.get_metric_collections():
            error_message = "Collections already exist in the database. Skipping initial load."
            self.logger.error(error_message)
            raise self.InitializationError(error_message)

        
        # Capture Start Time of Load
        load_start_time = common_utils.current_time_local()
       
        # create a unique identifier id for load
        load_id = common_utils.generate_unique_load_id()
        
        self.logger.info(f"******************* Starting Initial Load with load_id[{load_id}] at {load_start_time} *******************")
        
        # Download the files from S3 if source_type is S3
        if source_type == "S3":
            self._download_apple_health_feeds(workouts_dir, metrics_dir)
            

        # Ingest the files with workout data. Since it is initial load, we don't worry about duplicates or out of order data. 
        self.logger.info(" ********* Starting Processing the workout files - Initial Load ********************** ")
        workout_ingest_details = self.process_apple_workout_files(workouts_dir, workouts_processed_dir, load_id, check_for_duplicates=False )
        self.logger.info(" ********* Finished Processing the workout files - Initial Load  ********************** ")    
        
        # Ingest the files with health metrics. Since it is initial load, we don't worry about duplicates or out of order data.
        self.logger.info(" ********* Starting Processing the health-metric files - Initial Load  ********************** ")
        health_metrics_ingest_details =  self.process_apple_health_metric_files(metrics_dir, health_metrics_processed_dir, load_id, check_for_duplicates=False )
        self.logger.info(" ********* Finished Processing the health-metric files - Initial Load ********************** ") 
        
        self.save_duplicates_and_errors(workout_ingest_details, health_metrics_ingest_details, 
                                        workouts_duplicate_dir, health_metrics_duplicate_dir, 
                                        workouts_error_dir, health_metrics_error_dir, 
                                        workouts_dir, metrics_dir,load_id)
                
        if source_type == "S3":
            # Move the S3 stwo source files to their respective s3_processed_prefix locations in S3
            # We only move if workouts_dir or metrics_dir are not None. If it was none, it indicates that that caller didnt' want to process them
            if(workouts_dir):
                self._mark_workout_files_as_processed()
            if(metrics_dir):
                self._mark_health_metric_files_as_processed()

            
        # Capture Completioon time of load
        load_end_time = common_utils.current_time_local()
        
        # Calcuilate the load metrics and persist into into the load_summaries collection
        load_summary = self._create_load_summary("initial",  workout_ingest_details, health_metrics_ingest_details, load_start_time, load_end_time, load_id)
        self._store_load_summary(load_summary)
        
    
        self.logger.info(f"Finished Initial Load with load_id[{load_id}] at {load_end_time}")
        
        initial_load_metrics_formatted = json.dumps(load_summary, default=common_utils.datetime_converter, indent=4)
        self.logger.info(f"Initial Load Metrics Summary: \n{initial_load_metrics_formatted}")
                         
        

        return load_summary


    
    
    def ingest_apple_health_data_incremental_load(self, workouts_dir=None, metrics_dir=None, 
                                                  workouts_processed_dir= None, health_metrics_processed_dir = None, 
                                                  workouts_duplicate_dir = None, health_metrics_duplicate_dir = None,
                                                  workouts_error_dir = None, health_metrics_error_dir = None,
                                                  source_type="FILE"):
        """
        Performs the incremental load of Apple Health data into the Health Datalake.

        Args:
            workouts_dir (str): Directory containing workout data.
            metrics_dir (str): Directory containing metrics data.
            workouts_processed_dir (str): Directory to store processed workout data.
            health_metrics_processed_dir (str): Directory to store processed health metrics data.
            workouts_error_dir (str): Directory to store error records for workout data.
            health_metrics_error_dir (str): Directory to store error records for health metrics data.
            workouts_duplicate_dir (str): Directory to store duplicate records for workout data.
            health_metrics_duplicate_dir (str): Directory to store duplicate records for health metrics data.
            source_type (str): Type of data source. Can be "FILE" or "S3".

        Returns:
            dict: A dictionary containing the metrics of the loaded data.

        Raises:
            InitializationError: If the data lake does not contain collections or directories are invalid.
        """
        
        if source_type == "S3"  and not self.s3_utils:
            error_message = "S3 client is not configured. Cannot download files from S3."
            self.logger.error(error_message)
            raise self.InitializationError(error_message)
        
        
        # Check if collections exist in the database
        if not self.get_workout_collections() or not self.get_metric_collections():
            error_message = "Collections do not exist in the database. Skipping incremental load."
            self.logger.error(error_message)
            raise self.InitializationError(error_message)


        # Capture Start Time of Load
        load_start_time = common_utils.current_time_local()
        
        # create a unique identifier id for the incremental load
        load_id = common_utils.generate_unique_load_id()
        
        if source_type == "S3":
            self._download_apple_health_feeds(workouts_dir, metrics_dir)


            
        self.logger.info(f"********* Starting Incremental Load with load_id[{load_id}] at {load_start_time} **********************")
        
        # Ingest the files with workout data
        self.logger.info(" ********* Starting Processing the workout files  ********************** ")
        workout_ingest_details = self.process_apple_workout_files(workouts_dir, workouts_processed_dir, load_id, check_for_duplicates=True) 
        self.logger.info(" ********* Finished Processing the workout files  ********************** ")    

        # Ingest the health metrics data
        self.logger.info(" ********* Starting Processing the health-metric files  ********************** ")
        health_metrics_ingest_details = self.process_apple_health_metric_files(metrics_dir, health_metrics_processed_dir, load_id, check_for_duplicates=True)   
        self.logger.info(" ********* Finished Processing the health-metric files  ********************** ")    

        
                 
        self.save_duplicates_and_errors(workout_ingest_details, health_metrics_ingest_details, 
                                        workouts_duplicate_dir, health_metrics_duplicate_dir, 
                                        workouts_error_dir, health_metrics_error_dir, 
                                        workouts_dir, metrics_dir, load_id)
                        
        if source_type == "S3":
            # Move the S3 stwo source files to their respective s3_processed_prefix locations in S3
            # We only move if workouts_dir or metrics_dir are not None. If it was none, it indicates that that caller didnt' want to process them
            if(workouts_dir):
                self._mark_workout_files_as_processed()
            if(metrics_dir):
                self._mark_health_metric_files_as_processed()
            
        # Capture completion of time of load
        load_end_time = common_utils.current_time_local()

        # calculate the load metrics and persist into the load_summaries collection
        load_summary = self._create_load_summary("incremental", workout_ingest_details, health_metrics_ingest_details, load_start_time, load_end_time, load_id)
        
        self._store_load_summary(load_summary)


        self.logger.info(f"********* Finished Incremental Load with load_id[{load_id}] at {load_end_time} **********************")
        
        incremental_load_metrics_formatted = json.dumps(load_summary, default=common_utils.datetime_converter, indent=4)
        self.logger.info(f"Incremental Load Metrics Summary: \n{incremental_load_metrics_formatted}")
                         

        return load_summary

               
    def _download_apple_health_feeds(self, workouts_dir, metrics_dir):
        if workouts_dir:
            self.s3_utils.download_files_from_s3(self.s3_bucket, self.s3_workout_source_prefix, workouts_dir, '.json')
        if metrics_dir:
            self.s3_utils.download_files_from_s3(self.s3_bucket, self.s3_health_metrics_source_prefix, metrics_dir, '.json')


    def _mark_workout_files_as_processed(self):
        self.s3_utils.move_files_in_s3(self.s3_bucket, self.s3_bucket, self.s3_workout_source_prefix, self.s3_workout_processed_prefix, ".json")
     
    def _mark_health_metric_files_as_processed(self):
        self.s3_utils.move_files_in_s3(self.s3_bucket, self.s3_bucket, self.s3_health_metrics_source_prefix, self.s3_health_metrics_processed_prefix, '.json')
     
                
    def save_duplicates_and_errors(self, workout_ingest_details, health_metrics_ingest_details,
                                   workouts_duplicate_dir, health_metrics_duplicate_dir, 
                                   workouts_error_dir, health_metrics_error_dir, 
                                   workouts_dir, metrics_dir, load_id):
        if "duplicates_summary" in workout_ingest_details:
            self.save_duplicates(workout_ingest_details["duplicates_summary"], workouts_duplicate_dir, load_id)      
            
        if "duplicates_summary" in health_metrics_ingest_details:
            self.save_duplicates(health_metrics_ingest_details["duplicates_summary"], health_metrics_duplicate_dir, load_id)
            
        if "file_errors" in workout_ingest_details:
            self.save_errors(workout_ingest_details["file_errors"], workouts_dir, workouts_error_dir, load_id)
            
        if "file_errors" in health_metrics_ingest_details:
            self.save_errors(health_metrics_ingest_details["file_errors"], metrics_dir, health_metrics_error_dir, load_id)
    
    def save_duplicates(self, duplicates_summary, duplicate_dir, load_id):
        if not duplicates_summary:
            return
        
        for file_name, duplicates in duplicates_summary.items():
            # strip the file extension
            file_name = file_name.split('.')[0]
            file_path = f"{duplicate_dir}/{file_name}_duplicates_{load_id}.json"
            with open(file_path, 'w') as file:
                self.logger.info(f"Saving {len(duplicates)} duplicate records in file {file_name} to {file_path}")
                json.dump(duplicates, file, default=common_utils.datetime_converter, indent=4)   
    
    
    # file_errors is a dictionary with file_name as key and list of string errors as value
    # For each file_name using the source_dir, lets move it to the error_dir and add to the existing contents of the  json file the list of errors and name the file as file_name_errors_load_id.json
    def save_errors(self, file_errors, source_dir, error_dir, load_id):
        if not file_errors:
            return

        for file_name, error_list in file_errors.items():
            base_file_name = file_name.split('.')[0]
            source_file_path = os.path.join(source_dir, file_name)
            error_file_path = os.path.join(error_dir, f"{base_file_name}_errors_{load_id}.json")

            # Attempt to load JSON data, fallback to raw text on failure
            try:
                if os.path.exists(source_file_path):
                    with open(source_file_path, 'r') as file:
                        file_data = json.load(file)
                else:
                    file_data = {}
            except json.JSONDecodeError:
                # If JSON is invalid, read the file as a string
                with open(source_file_path, 'r') as file:
                    file_data = file.read()

            # Append errors to file data
            if isinstance(file_data, dict):
                file_data["errors"] = error_list
            else:
                file_data += "\nErrors:\n" + "\n".join(error_list)

            # Write updated data or string to error file
            with open(error_file_path, 'w') as file:
                if isinstance(file_data, dict):
                    json.dump(file_data, file, default=common_utils.datetime_converter, indent=4)
                else:
                    file.write(file_data)

            # Move the file from source_dir to error_dir
            if os.path.exists(source_file_path):
                shutil.move(source_file_path, os.path.join(error_dir, file_name))
                self.logger.info(f"Moved file {source_file_path} to {error_dir}")

    
   
    def post_process_fhir_data_after_load(self):
        """ 
        Perform post processing of FHIR data after the initial load. 
        """
        
        self.logger.info("Starting Post Processing of FHIR Lab Results after Load")
        self.post_process_fhir_lab_results_after_load()
        self.logger.info("Finished Post Processing of FHIR Lab Results after Load")

    def post_process_fhir_lab_results_after_load(self):
        """
        Perform post processing of FHIR Lab Results after the initial load.
        """
        self.lab_results_service.normalize_loinc_codes()    
        self.lab_results_service.add_missing_loinc_codes()

    
  