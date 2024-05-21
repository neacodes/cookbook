from enum import Enum


class EnvKeys(Enum):
    MONGO_USER = 'MONGO_USER'
    MONGO_PASSWORD = 'MONGO_PASSWORD'
    MONGO_HOST = 'MONGO_HOST'
    MONGO_DB_NAME = 'MONGO_DB_NAME'
    
    S3_BUCKET_NAME = 'S3_BUCKET_NAME'
    S3_METRICS_LANDING_ZONE = 'S3_METRICS_LANDING_ZONE'
    S3_METRICS_PROCESSED_ZONE = 'S3_METRICS_PROCESSED_ZONE'
    S3_WORKOUT_LANDING_ZONE = 'S3_WORKOUT_LANDING_ZONE'
    S3_WORKOUT_PROCESSED_ZONE = 'S3_WORKOUT_PROCESSED_ZONE'
    
    LOCAL_LANDING_ZONE_WORKOUTS_DIR = 'LANDING_ZONE_WORKOUTS_DIR'
    LOCAL_LANDING_ZONE_METRICS_DIR = 'LANDING_ZONE_METRICS_DIR',
    LOCAL_PROCESSED_ZONE_WORKOUTS_DIR = 'PROCESSED_ZONE_WORKOUTS_DIR'
    LOCAL_PROCESSED_ZONE_METRICS_DIR = 'PROCESSED_ZONE_METRICS_DIR'
    LOCAL_DUPICATES_ZONE_WORKOUTS_DIR = 'DUPLICATES_ZONE_WORKOUTS_DIR'
    LOCAL_DUPICATES_ZONE_METRICS_DIR = 'DUPLICATES_ZONE_METRICS_DIR'
    LOCAL_ERRORS_ZONE_WORKOUTS_DIR = 'ERRORS_ZONE_WORKOUTS_DIR'
    LOCAL_ERRORS_ZONE_METRICS_DIR = 'ERRORS_ZONE_METRICS_DIR'
    
    INCREMENTAL_S3_BASE_DIR = 'INCREMENTAL_S3_BASE_DIR'

    SOURCE_DIRECTORY_FOR_FHIR = 'SOURCE_FHIR_DIR'
    FHIR_ZONE = 'FHIR_ZONE'
    
    LOAD_METRICS_SERVICE = 'LOAD_METRICS_SERVICE'
    WORKOUT_METRICS_SERVICE = 'WORKOUT_METRICS_SERVICE'
    HEALTH_LAKE_INGESTION_SERVICE = 'HEALTH_LAKE_INGESTION_SERVICE'
    FHIR_MEDICATION_SERVICE = 'FHIR_MEDICATION_SERVICE'

    SOURCE_DIRECTORY_FOR_WORKOUTS = 'SOURCE_WORKOUTS_DIR'
    PROCESSED_ZONE_FOR_WORKOUTS = 'PROCESSED_ZONE_WORKOUTS_DIR'
    DUPLICATES_ZONE_FOR_WORKOUTS = 'DUPLICATES_ZONE_WORKOUTS_DIR'
    ERRORS_ZONE_FOR_WORKOUTS = 'ERRORS_ZONE_WORKOUTS_DIR'

    SOURCE_DIRECTORY_FOR_HEALTH_METRICS = 'SOURCE_METRICS_DIR'
    PROCESSED_ZONE_FOR_HEALTH_METRICS = 'PROCESSED_ZONE_METRICS_DIR'    
    DUPLICATES_ZONE_FOR_HEALTH_METRICS = 'DUPLICATES_ZONE_METRICS_DIR'   
    ERRORS_ZONE_FOR_HEALTH_METRICS = 'ERRORS_ZONE_METRICS_DIR'  
