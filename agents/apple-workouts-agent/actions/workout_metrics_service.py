import json

from  base_mongodb_service import BaseMongoDBService
import logging

import common_utils

class WorkoutMetricsService(BaseMongoDBService):
    
    logger = logging.getLogger(__name__+'.'+__qualname__)
    
    def __init__(self, mongo_user, mongo_password, mongo_host, mongo_db):
        super().__init__(mongo_user, mongo_password, mongo_host, mongo_db)

    
    def aggregate_workout_metrics(self, metric, aggregation_type, start_date, end_date, collections):
        """
        Generic method to aggregate workout metrics across specified collections.
        """
        
        # Convert string dates to datetime objects with time and timezone
        # start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S %z")
        # end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S %z")
        # start_date = datetime.datetime.fromisoformat(start_date)
        # end_date = datetime.datetime.fromisoformat(end_date)    
        
        start_date = common_utils.convert_query_date_to_cst(start_date)
        end_date = common_utils.convert_query_date_to_cst(end_date)
        

        if metric in ['heartRateRecovery']:
            
            # Map the metric to what it is called in the Document
            json_metric = metric

            #  Since heartRateRecovery is an array for each workout, we need to unwind it first and calculate the average
            aggregation_metric = "avgHeartRateRecovery"
            
            aggregation_op = {
                'average': {'$avg': f"${aggregation_metric}"},
                'max': {'$max': f"${aggregation_metric}"},
                'min': {'$min': f"${aggregation_metric}"},
            }.get(aggregation_type, {'$avg': f"${aggregation_metric}"})


            # 0./ Filter for recorfds within our date range
            # 1./ Unwind heartRateRecovery array: First unwide the heartRateRecovery' Array. This will create new doc for each element in heartRateRecovery array
            # 2./ Group by document_id: Then we group by the _id and  then average the qty field of heartRateRecovery heartRateRecovery.qty field. CAll the sume avgHeartRateRecovery
            # 3./ Perform another grouping without specifying the id, to calculate the the aggregation of the new field called avgHeartRateRecovery obtained in previous step
            pipeline = [
                {"$match": {"start": {"$gte": start_date, "$lt": end_date}}},
                {"$unwind": f"${json_metric}"},
                {"$group": {"_id": "$_id", aggregation_metric: {"$avg": f"${json_metric}.qty"}}}, 
                {"$group": {"_id": None, "result": aggregation_op}}
            ]
        else:
            # Map the metric to what it is called in the Document (distance, heartRate, duration)
            json_metric = {
                "distance": "distance.qty",
                "calorie": "activeEnergy.qty",
                "heartRate": "maxHeartRate.qty" if aggregation_type in ['max'] else "avgHeartRate.qty",
            }.get(metric, metric)            
                        
            aggregation_op = {
                'sum': {'$sum': f"${json_metric}"},
                'average': {'$avg': f"${json_metric}"},
                'max': {'$max': f"${json_metric}"},
                'min': {'$min': f"${json_metric}"},
                'count': {'$sum': 1}
            }[aggregation_type]

  
            pipeline = [
                {"$match": {"start": {"$gte": start_date, "$lt": end_date}}},
                {"$group": {"_id": None, "result": aggregation_op}}
            ]
    

        # Execute the pipeline for each relevant collection
        total_metric_value = float(0) if aggregation_type in ['sum', 'count'] else []
        total_count = 0  # For calculating average

        for collection_name in collections:
            collection = self.mongo_health_lake[collection_name]
        
            # Perform the aggregation query on the collection
            aggregation_result = collection.aggregate(pipeline)

            # Retrieve the first result from the aggregation query, or an empty dictionary if no results are returned
            first_result = next(aggregation_result, {})

            # Retrieve the value associated with the key 'result' from the first result
            result = first_result.get('result')
        
            if result is not None:
                if aggregation_type in ['average', 'max', 'min']:
                    total_metric_value.append(result)
                    total_count += 1
                else:
                    total_metric_value += result

        # Final calculation for average, max, and min
        if aggregation_type == 'average':
            return self.format_aggregation_value(float(sum(total_metric_value) / total_count)) if total_count > 0 else float(0)
        elif aggregation_type == 'max':
            return self.format_aggregation_value(float(max(total_metric_value))) if total_metric_value else float(0)
        elif aggregation_type == 'min':
            return self.format_aggregation_value(float(min(total_metric_value))) if total_metric_value else float(0)
        else:
            return self.format_aggregation_value(float(total_metric_value))


    # Performance Details on Running workouts # 
    def get_run_workout_performance(self, metric: str, aggregation_type: str, start_date: str, end_date: str ) -> float:
        """
        Calculate various running performance metrics within a specified time period across different running workouts.

        Args:
            metric (str): The running performance metric to aggregate. Supported metrics include 'distance', 'duration',
                        'heartRate', 'heartRateRecovery' and 'calorie'.
            aggregation_type (str): Type of aggregation to perform. Supported types are 'sum', 'average', 'max', 'min', 
                                    and 'count'.
            start_date (str): The start date for data aggregation in 'YYYY-MM-DD' format.
            end_date (str): The end date for data aggregation in 'YYYY-MM-DD' format.

        Returns:
            float: The result of the specified aggregation on the running metric.

        Description:
            This function aggregates running performance data based on the specified metric and aggregation type
            within a given date range. It accesses MongoDB collections related to running activities, such as
            indoor runs, outdoor runs, and general runs. The function handles various data types and structures,
            ensuring accurate computations for each metric.

        Examples:
            - To calculate the total running distance for January 2023, call 
            get_run_workout_performance('distance', 'sum', '2023-01-01', '2023-02-01').
            - To find out the average heart rate during runs in 2023, use 
            get_run_workout_performance('heartRate', 'average', '2023-01-01', '2024-01-01').
            - To find out the total calorie burned during runs in 2023, use
            get_run_workout_performance('calorie', 'sum', '2023-01-01', '2024-01-01').

        Note:
            - The function supports different metrics and aggregation types, adapting to the data structure of each.
            - Ensure MongoDB database is properly configured and accessible for data retrieval.
        """
        
        run_workout_collections = ['workouts_indoor_run', 'workouts_outdoor_run', 'workouts_run']
        return self.aggregate_workout_metrics( metric, aggregation_type, start_date, end_date, run_workout_collections) 
  

    # Performance Details on Cycling workouts # 
    def get_cycle_workout_performance(self, metric: str, aggregation_type: str, start_date: str, end_date: str ) -> float:
        """
        Calculate various cycling performance metrics within a specified time period across different cycling workouts.

        Args:
            metric (str): The running performance metric to aggregate. Supported metrics include 'distance', 'duration',
                        'heartRate', 'heartRateRecovery' and 'calorie'.
            aggregation_type (str): Type of aggregation to perform. Supported types are 'sum', 'average', 'max', 'min', 
                                    and 'count'.
            start_date (str): The start date for data aggregation in 'YYYY-MM-DD' format.
            end_date (str): The end date for data aggregation in 'YYYY-MM-DD' format.

        Returns:
            float: The result of the specified aggregation on the cycling metric.

        Description:
            This function aggregates cycling performance data based on the specified metric and aggregation type
            within a given date range. It accesses MongoDB collections related to cycling activities, such as
            outdoor cycling, outdoor cycling, and general cycling workouts. The function handles various data types and structures,
            ensuring accurate computations for each metric.

        Examples:
            - To calculate the total cyling distance for January 2023, call 
            get_cycle_workout_performance('distance', 'sum', '2023-01-01', '2023-02-01').
            - To find out the average heart rate during cycling in 2023, use 
            get_cycle_workout_performance('heartRate', 'average', '2023-01-01', '2024-01-01').
            - To find out the total calorie burned during cycling in 2023, use
            get_cycle_workout_performance('calorie', 'sum', '2023-01-01', '2024-01-01').

        Note:
            - The function supports different metrics and aggregation types, adapting to the data structure of each.
            - Ensure MongoDB database is properly configured and accessible for data retrieval.
        """
        
        cycling_workout_collections = ['workouts_indoor_cycling', 'workouts_outdoor_cycling', 'workouts_cycling']
        return self.aggregate_workout_metrics( metric, aggregation_type, start_date, end_date, cycling_workout_collections) 


    # Performance Details on Walking workouts # 
    def get_walk_workout_performance(self, metric: str, aggregation_type: str, start_date: str, end_date: str ) -> float:
        """
        Calculate various walking performance metrics within a specified time period across different walking workouts.

        Args:
            metric (str): The running performance metric to aggregate. Supported metrics include 'distance', 'duration',
                        'heartRate', 'heartRateRecovery' and 'calorie'.
            aggregation_type (str): Type of aggregation to perform. Supported types are 'sum', 'average', 'max', 'min', 
                                    and 'count'.
            start_date (str): The start date for data aggregation in 'YYYY-MM-DD' format.
            end_date (str): The end date for data aggregation in 'YYYY-MM-DD' format.

        Returns:
            float: The result of the specified aggregation on the walking metric.

        Description:
            This function aggregates walking performance data based on the specified metric and aggregation type
            within a given date range. It accesses MongoDB collections related to walking activities, such as
            outdoor walking, indoor walking, and general walking workouts. The function handles various data types and structures,
            ensuring accurate computations for each metric.

        Examples:
            - To calculate the total walking distance for January 2023, call 
            get_walk_workout_performance('distance', 'sum', '2023-01-01', '2023-02-01' ).
            - To find out the average heart rate during walking in 2023, use 
            get_walk_workout_performance('heartRate', 'average', '2023-01-01', '2024-01-01').
            - To find out the total calorie burned during walking in 2023, use
            get_walk_workout_performance('calorie', 'sum', '2023-01-01', '2024-01-01').

        Note:
            - The function supports different metrics and aggregation types, adapting to the data structure of each.
            - Ensure MongoDB database is properly configured and accessible for data retrieval.
        """
        
        walking_workout_collections = ['workouts_indoor_walk', 'workouts_outdoor_walk', 'workouts_walk']
        return self.aggregate_workout_metrics( metric, aggregation_type, start_date, end_date, walking_workout_collections) 

   # Performance Details on Hiking workouts # 
    def get_hike_workout_performance(self, metric: str, aggregation_type: str, start_date: str, end_date: str ) -> float:
        """
        Calculate various hiking performance metrics within a specified time period across different hiking workouts.

        Args:
            metric (str): The running performance metric to aggregate. Supported metrics include 'distance', 'duration',
                        'heartRate', 'heartRateRecovery' and 'calorie'.
            aggregation_type (str): Type of aggregation to perform. Supported types are 'sum', 'average', 'max', 'min', 
                                    and 'count'.
            start_date (str): The start date for data aggregation in 'YYYY-MM-DD' format.
            end_date (str): The end date for data aggregation in 'YYYY-MM-DD' format.

        Returns:
            float: The result of the specified aggregation on the hiking metric.

        Description:
            This function aggregates hiking performance data based on the specified metric and aggregation type
            within a given date range. It accesses MongoDB collections related to hiking activities, such as
            outdoor hiking, indoor hiking, and general hiking workouts. The function handles various data types and structures,
            ensuring accurate computations for each metric.

        Examples:
            - To calculate the total hiking distance for January 2023, call 
            get_hike_workout_performance('distance', 'sum', '2023-01-01', '2023-02-01' ).
            - To find out the average heart rate during hiking in 2023, use 
            get_hike_workout_performance('heartRate', 'average', '2023-01-01', '2024-01-01').
            - To find out the total calorie burned during hiking in 2023, use
            get_hike_workout_performance('calorie', 'sum', '2023-01-01', '2024-01-01').

        Note:
            - The function supports different metrics and aggregation types, adapting to the data structure of each.
            - Ensure MongoDB database is properly configured and accessible for data retrieval.
        """
        
        hiking_workout_collections = ['workouts_hiking']
        return self.aggregate_workout_metrics( metric, aggregation_type, start_date, end_date, hiking_workout_collections) 

    # Performance Details on Tennis workouts # 
    def get_tennis_workout_performance(self, metric: str, aggregation_type: str, start_date: str, end_date: str ) -> float:
        """
        Calculate various tennis performance metrics within a specified time period across different tennis workouts.

        Args:
            metric (str): The running performance metric to aggregate. Supported metrics include 'distance', 'duration',
                        'heartRate', 'heartRateRecovery' and 'calorie'.
            aggregation_type (str): Type of aggregation to perform. Supported types are 'sum', 'average', 'max', 'min', 
                                    and 'count'.
            start_date (str): The start date for data aggregation in 'YYYY-MM-DD' format.
            end_date (str): The end date for data aggregation in 'YYYY-MM-DD' format.

        Returns:
            float: The result of the specified aggregation on the tennis metric.

        Description:
            This function aggregates tennis performance data based on the specified metric and aggregation type
            within a given date range. It accesses MongoDB collections related to tennis activities, such as
            outdoor tennis, indoor tennis, and general tennis workouts. The function handles various data types and structures,
            ensuring accurate computations for each metric.

        Examples:
            - To calculate the total tennis distance for January 2023, call 
            get_tennis_workout_performance('distance', 'sum', '2023-01-01', '2023-02-01' ).
            - To find out the average heart rate during tennis in 2023, use 
            get_tennis_workout_performance('heartRate', 'average', '2023-01-01', '2024-01-01').
            - To find out the total calorie burned during tennis in 2023, use
            get_tennis_workout_performance('calorie', 'sum', '2023-01-01', '2024-01-01').

        Note:
            - The function supports different metrics and aggregation types, adapting to the data structure of each.
            - Ensure MongoDB database is properly configured and accessible for data retrieval.
        """
        
        tennis_workout_collections = ['workouts_tennis']
        return self.aggregate_workout_metrics( metric, aggregation_type, start_date, end_date, tennis_workout_collections) 

    # Performance Detals on Core workouts # 
    def get_core_workout_performance(self, metric: str, aggregation_type: str, start_date: str, end_date: str ) -> float:
        """
        Calculate various core performance metrics within a specified time period across different core workouts.

        Args:
            metric (str): The running performance metric to aggregate. Supported metrics include 'distance', 'duration',
                        'heartRate', 'heartRateRecovery' and 'calorie'.
            aggregation_type (str): Type of aggregation to perform. Supported types are 'sum', 'average', 'max', 'min', 
                                    and 'count'.
            start_date (str): The start date for data aggregation in 'YYYY-MM-DD' format.
            end_date (str): The end date for data aggregation in 'YYYY-MM-DD' format.

        Returns:
            float: The result of the specified aggregation on the core metric.

        Description:
            This function aggregates core performance data based on the specified metric and aggregation type
            within a given date range. It accesses MongoDB collections related to core activities, such as
            core workouts, abs workouts, and plank workouts. The function handles various data types and structures,
            ensuring accurate computations for each metric.

        Examples:
            - To calculate the total core distance for January 2023, call 
            get_core_workout_performance('distance', 'sum', '2023-01-01', '2023-02-01' ).
            - To find out the average heart rate during core workouts in 2023, use 
            get_core_workout_performance('heartRate', 'average', '2023-01-01', '2024-01-01').
            - To find out the total calorie burned during core workouts in 2023, use
            get_core_workout_performance('calorie', 'sum', '2023-01-01', '2024-01-01').

        Note:
            - The function supports different metrics and aggregation types, adapting to the data structure of each.
            - Ensure MongoDB database is properly configured and accessible for data retrieval.
        """
        
        core_workout_collections = ['workouts_core_training']
        return self.aggregate_workout_metrics( metric, aggregation_type, start_date, end_date, core_workout_collections) 


    def get_last_n_run_workout_details(self, n: int) -> str:
        """
        Retrieves details for the last n run workouts from the MongoDB collections related to running activities
        and returns the information as a JSON string.

        Args:
            n (int): The number of run workouts to retrieve details for.

        Returns:
            str: A JSON string representing a list of dictionaries, each containing details for a specific run workout.
                The details include:
                - start (datetime): The start time of the workout.
                - end (datetime): The end time of the workout.
                - duration (int): The duration of the workout in minutes.
                - distance.qty (float): The distance covered during the workout in kilometers.
                - avgHeartRate (int): The average heart rate during the workout.
                - maxHeartRate (int): The maximum heart rate during the workout.
                - activeEnergy.qty (float): The total calories burned during the workout.

        Description:
            This function queries the MongoDB collections for running activities, including indoor runs, outdoor runs,
            and general run workouts. It compiles a list of the last n workouts, sorted by their start time, and extracts
            key performance metrics for each workout. This data is then serialized into a JSON string, which can be easily
            loaded back into a JSON object for analysis, reporting, or display purposes.

        Examples:
            - To get details for the last 5 run workouts and load them back into JSON for processing:
            json_string = get_last_n_run_workout_details(5)
            workout_details = json.loads(json_string)

            - To retrieve details for the last 10 run workouts and process the data:
            json_string = get_last_n_run_workout_details(10)
            workout_details = json.loads(json_string)
        """
        run_workout_collections = ['workouts_indoor_run', 'workouts_outdoor_run', 'workouts_run']
        
        last_n_workouts = []
        
        # Iterate through each collection to get the last n records, returning specified fields for each workout
        for collection_name in run_workout_collections:
            collection = self.mongo_health_lake[collection_name]
            workouts = collection.find({}, {"start": 1, "end": 1, "duration": 1, "distance.qty": 1, "avgHeartRate": 1, "maxHeartRate":1, "activeEnergy.qty":1 }).sort([("start", -1)]).limit(n)
            last_n_workouts.extend(list(workouts))
           
        return json.dumps(last_n_workouts, default=common_utils.datetime_converter)

        
