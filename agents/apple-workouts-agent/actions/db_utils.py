import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Configure logging at the module level (you can also configure this in the main script or a separate logger configuration file)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_mongo_database(mongo_user, mongo_password, mongo_host, mongo_db):
    """Create a MongoDB client and connect to the specified database.

    Args:
        - mongo_user: The username for authentication.
        - mongo_password: The password for authentication.
        - mongo_host: The host address of the MongoDB server.
        - mongo_db: The name of the database to connect to.

    Returns:
        - A `Database` object representing the specified database.

    Raises:
        - ConnectionFailure: If the connection to the MongoDB server fails.
    """
    uri = f"mongodb+srv://{mongo_user}:{mongo_password}@{mongo_host}/?retryWrites=true&w=majority"
    try:
        client = MongoClient(uri)
        db = client[mongo_db]
        client.admin.command('ismaster')
        logging.info(f"Successfully connected to MongoDB database: {mongo_db}")
        return db
    except ConnectionFailure as e:
        logging.error(f"Could not connect to MongoDB: {e}")
        raise
    

