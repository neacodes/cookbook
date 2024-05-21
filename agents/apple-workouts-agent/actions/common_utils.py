from datetime import datetime
import uuid
from datetime import datetime
from dateutil import tz
from bson.objectid import ObjectId


# Function to convert query date string to datetime in CST
def convert_query_date_to_cst(date_string):
    # Parse the query date string (assuming midnight)
    date = datetime.strptime(date_string, '%Y-%m-%d')

    # Set the timezone to CST
    cst_timezone = tz.gettz('America/Chicago')
    date_with_cst = date.astimezone(cst_timezone)

    # Format the date to match the collection's format
    formatted_date = date_with_cst.strftime('%Y-%m-%d %H:%M:%S %z')
    return formatted_date


def datetime_converter(o):
    if isinstance(o, datetime):
        return o.__str__()

def object_id_converter(o):
    if isinstance(o, ObjectId):
        return o.__str__()


def current_time_local(format='%Y-%m-%d %H:%M:%S'):
    """
    Returns the current time in the local timezone as a formatted string.

    Returns:
        str: The current time in the local timezone.
    """
    local_tz = datetime.now().astimezone().tzinfo
    return datetime.now(local_tz).strftime(format)

# All files will having naming conention of HealthAutoExport-YYYY-MM-DD, we can sort ascening alphabettical order
def sort_files_by_date(files):
    new_files = sorted(files)
    return new_files


def generate_unique_load_id():
    """
    Generates a unique identifier for a load.

    Returns:
        str: A unique identifier for a load.
    """
    return str(uuid.uuid4())