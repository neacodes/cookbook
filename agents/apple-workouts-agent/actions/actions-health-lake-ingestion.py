

import json
from sema4ai.actions import action
from health_lake_ingestion_service import HealthLakeIngestionService
import common_utils
from env_enum import EnvKeys
from env_config import prod_env
import logging

logger = logging.getLogger(__name__)
              
health_lake_ingestion_service = HealthLakeIngestionService(prod_env[EnvKeys.MONGO_USER.value], 
                                                           prod_env[EnvKeys.MONGO_PASSWORD.value],
                                                           prod_env[EnvKeys.MONGO_HOST.value],
                                                           prod_env[EnvKeys.MONGO_DB_NAME.value],
                                                           prod_env[EnvKeys.S3_BUCKET_NAME.value],
                                                           prod_env[EnvKeys.S3_WORKOUT_LANDING_ZONE.value],
                                                           prod_env[EnvKeys.S3_WORKOUT_PROCESSED_ZONE.value],
                                                           prod_env[EnvKeys.S3_METRICS_LANDING_ZONE.value],
                                                           prod_env[EnvKeys.S3_METRICS_PROCESSED_ZONE.value])



                                
@action(is_consequential=True)
def load_new_workout_data_from_apple_health() -> str:
    """
    Uploads the latest workout data from the Apple Health app to the Health DataLake. 
    Before calling this function, explicitly ask the user's consent to see if they want the workout data to be updated

    Returns:
        A JSON string containing a summary of the data load, including the number of new workouts added and details of each workout.

    Usage:
        - Call this function when up-to-date workout data is required for user queries. 
        - However before calling this function, explicitly ask the user's consent to see if they want the workout data to be updated. 
        - After calling, parse the returned JSON load summary to understand the specifics of the update and decide on subsequent queries.
    """
    
    workouts_dir = prod_env[EnvKeys.LOCAL_LANDING_ZONE_WORKOUTS_DIR.value]
    metrics_dir = None
    print(f"workouts_dir: {workouts_dir}")
    
    workouts_processed_dir = prod_env[EnvKeys.LOCAL_PROCESSED_ZONE_WORKOUTS_DIR.value]    
    health_metrics_processed_dir = None
    
    workouts_duplicate_dir = prod_env[EnvKeys.LOCAL_DUPICATES_ZONE_WORKOUTS_DIR.value] 
    health_metrics_duplicate_dir = None

    workouts_error_dir = prod_env[EnvKeys.LOCAL_ERRORS_ZONE_WORKOUTS_DIR.value] 
    health_metrics_error_dir= None

    load_summary = health_lake_ingestion_service.ingest_apple_health_data_incremental_load(workouts_dir, metrics_dir,
                                                                               workouts_processed_dir, health_metrics_processed_dir,
                                                                               workouts_duplicate_dir, health_metrics_duplicate_dir,
                                                                               workouts_error_dir, health_metrics_error_dir,
                                                                               source_type="S3")
    logger.info(f"Load summary : {load_summary}")
    workout_load_metrics = load_summary.get("workout_metrics", [])
    load_summary_string = json.dumps(workout_load_metrics, default=common_utils.datetime_converter)
    return load_summary_string

