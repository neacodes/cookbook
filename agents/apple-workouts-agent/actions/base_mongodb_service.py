import db_utils
import logging
import logging.config


class BaseMongoDBService:
    
    # Configure logging
    logging.config.fileConfig('logging-prod.conf')
    logger = logging.getLogger(__name__)  # noqa: F821
    logger.setLevel(logging.INFO)
    
    def __init__(self, mongo_user, mongo_password, mongo_host, mongo_db):
        try:
            self.mongo_health_lake = db_utils.get_mongo_database(
                mongo_user=mongo_user,
                mongo_password=mongo_password,
                mongo_host=mongo_host,
                mongo_db=mongo_db)
            self.logger.info("Successfully connected to MongoDB.")
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            raise  
        
    def format_aggregation_value(self, float_value_to_format):
            """
            Formats a float value by rounding it to one decimal place if it is greater than zero.
            If the value is less than or equal to zero, it returns 0 as a float.

            Args:
                float_value_to_format (float): The float value to be formatted.

            Returns:
                float: The formatted float value.
            """
            return round(float_value_to_format, 1) if float_value_to_format > 0 else float(0)
    
    
 
        
      