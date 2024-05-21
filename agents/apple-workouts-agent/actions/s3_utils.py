import logging
import os
import boto3

class S3Utils:
    """
    A class to interact with AWS S3.
    """

    # Configure the logger for this class
    logger = logging.getLogger(__name__+'.'+__qualname__)

    
    def __init__(self, s3_client=None):
        
        self.s3_client = boto3.client('s3')        
        
    
    def list_files_in_s3_folder(self, bucket_name, s3_folder_prefix, file_type_filter=None):
        """
        Lists files in a specific folder in an S3 bucket.

        Args:
            bucket_name (str): The name of the S3 bucket.
            s3_folder_prefix (str): The prefix of the folder in the S3 bucket.
            file_type_filter (str, optional): Filter for file types. Only files with the specified file extension will be included. Defaults to None.

        Returns:
            list: A list of file paths in the specified S3 folder.
        """
        response = self.s3_client.list_objects_v2(Bucket=bucket_name, Prefix=s3_folder_prefix)
        if 'Contents' not in response:
            return []
        
        filter_files = []
        for file in  [content['Key'] for content in response['Contents']]:
            if not file.endswith('/') and (file_type_filter is None or file.endswith(file_type_filter)):
                filter_files.append(file)    
        return filter_files

    def download_files_from_s3(self, s3_bucket_name, s3_source_folder_prefix, local_folder_dest_path, filter_for_files=None):

        files_to_download = self.list_files_in_s3_folder(s3_bucket_name, s3_source_folder_prefix, filter_for_files)
           
        self.logger.info(f"About to start {len(files_to_download)} downloading files from S3  bucket {s3_bucket_name} location {s3_source_folder_prefix} to {local_folder_dest_path}")   
            
        for file in files_to_download:
            file_name = file.split('/')[-1]
            destination_path = os.path.join(local_folder_dest_path, file_name)
            self.s3_client.download_file(s3_bucket_name, file,  destination_path)

        self.logger.info(f"Finished  downloading {len(files_to_download)} files from S3  bucket {s3_bucket_name} location {s3_source_folder_prefix} to {local_folder_dest_path}")  
        
    def upload_files_to_s3(self, s3_bucket_name, s3_dest_folder_prefix, local_folder_source_path, file_type_filter=None):
        """
        Upload files from a local folder to an S3 bucket with the specified folder prefix.
        
        Args:
            s3_bucket_name (str): The name of the S3 bucket.
            s3_dest_folder_prefix (str): The prefix of the destination folder in the S3 bucket.
            local_folder_source_path (str): The path to the local folder containing the files to upload.
        
        Returns:
            None
        """
        # If file_type_filter is not specified, upload all files in the local folder
        if file_type_filter is None:
            files_to_upload = [os.path.join(local_folder_source_path, file) for file in os.listdir(local_folder_source_path)]
        else:   
            files_to_upload = [os.path.join(local_folder_source_path, file) for file in os.listdir(local_folder_source_path) if file.endswith(file_type_filter)]    
        
        self.logger.info(f"About to start {len(files_to_upload)} uploading files from {local_folder_source_path} to S3 bucket {s3_bucket_name}, location {s3_dest_folder_prefix}")   
        for file in files_to_upload:
            file_name = file.split('/')[-1]
            s3_key = os.path.join(s3_dest_folder_prefix, file_name)
            self.s3_client.upload_file(file, s3_bucket_name, s3_key)
        self.logger.info(f"Finished uploading {len(files_to_upload)} files from {local_folder_source_path} to S3 bucket {s3_bucket_name}, location {s3_dest_folder_prefix}")
    
    def delete_files_in_s3_folder(self, bucket_name, s3_folder_prefix, file_type_filter=None):
        """
        Deletes the files in the S3 bucket with the specified folder prefix.
        
        Returns:
            None
        """
        files = self.list_files_in_s3_folder(bucket_name, s3_folder_prefix)
        if file_type_filter is not None:
            files = [file for file in files if file.endswith(file_type_filter)] 
        for file in files:
            self.s3_client.delete_object(Bucket=bucket_name, Key=file)
        self.logger.info(f"Deleted {len(files)} files from S3 bucket {bucket_name}, location {s3_folder_prefix}")
        
        
    # Deletes the files in the list provider in the S3 bucket with the specified folder prefix.
    def delete_list_of_files_in_s3(self, bucket_name, folder_prefix, files_to_delete):
        for file in files_to_delete:
            self.s3_client.delete_object(Bucket=bucket_name, Key=folder_prefix + file)
        self.logger.info(f"Deleted {len(files_to_delete)} files from S3 bucket {bucket_name}, location {folder_prefix}")
        
    def copy_files_in_s3(self, s3_source_bucket, s3_dest_bucket, s3_source_folder_prefix, s3_dest_folder_prefix, file_type_filter=None):
        """
        Copy files from one S3 bucket to another with the specified folder prefixes. 
        The source files are not deleted after the copy.
        
        Args:
            s3_source_bucket (str): The name of the source S3 bucket.
            s3_dest_bucket (str): The name of the destination S3 bucket.
            s3_source_folder_prefix (str): The prefix of the source folder in the S3 bucket.
            s3_dest_folder_prefix (str): The prefix of the destination folder in the S3 bucket.

        Returns:
            None
        """
        files_to_copy = self.list_files_in_s3_folder(s3_source_bucket, s3_source_folder_prefix, file_type_filter)
        
        self.logger.info(f"About to start copying {len(files_to_copy)} files from S3 bucket {s3_source_bucket} location {s3_source_folder_prefix} to {s3_dest_bucket}, location {s3_dest_folder_prefix}")   
        for file_key in files_to_copy:
            new_key = file_key.replace(s3_source_folder_prefix, s3_dest_folder_prefix)
            self.s3_client.copy_object(CopySource={'Bucket': s3_source_bucket, 'Key': file_key}, Bucket=s3_dest_bucket, Key=new_key)
        self.logger.info(f"Finished copying {len(files_to_copy)} files from S3 bucket {s3_source_bucket} location {s3_source_folder_prefix} to {s3_dest_bucket}, location {s3_dest_folder_prefix}") 

    def move_files_in_s3(self, s3_source_bucket, s3_dest_bucket, s3_source_folder_prefix, s3_dest_folder_prefix, file_type_filter=None):
        """
        Move files from one S3 bucket to another with the specified folder prefixes. 
        The source files are deleted after the move.
        
        Args:
            s3_source_bucket (str): The name of the source S3 bucket.
            s3_dest_bucket (str): The name of the destination S3 bucket.
            s3_source_folder_prefix (str): The prefix of the source folder in the S3 bucket.
            s3_dest_folder_prefix (str): The prefix of the destination folder in the S3 bucket.

        Returns:
            None
        """
        self.copy_files_in_s3(s3_source_bucket, s3_dest_bucket, s3_source_folder_prefix, s3_dest_folder_prefix, file_type_filter)
        self.delete_files_in_s3_folder(s3_source_bucket, s3_source_folder_prefix, file_type_filter)
    

    
    
