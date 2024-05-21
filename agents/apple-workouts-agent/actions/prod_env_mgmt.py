
import logging
from workout_metrics_service import WorkoutMetricsService
from env_enum import EnvKeys
from env_config import prod_env
from bson import ObjectId


# Configure logging
logging.config.fileConfig('logging-prod.conf')
logger = logging.getLogger(__name__)  
logger.setLevel(logging.INFO) 


# #load_id of the initial load
# initial_load_id = "fb3df7e8-1c64-4c4d-8f73-9503b2cb83d3"
# num_of_docs_from_initial_load = env_mgmt_utils.get_total_docs_with_load_id("prod", initial_load_id) # 11,680,953



# #first incremental run
# first_incremental_load_id = "195815de-5915-4375-bbba-93473e8d6ebf"
# new_docs_from_first_incremental_run = env_mgmt_utils.get_total_docs_with_load_id("prod", first_incremental_load_id) # 39400


# total_current_docs = env_mgmt_utils.get_total_docs("prod") #11, 7203, 53

# Difference Services configured for Production
# workout_service: WorkoutMetricsService = prod_env[EnvKeys.WORKOUT_METRICS_SERVICE.value]    

# start_date = '2023-01-01 00:00:00'
# end_date = '2023-12-31 23:59:59'
# # Distance Metrics #
# # How many total miles did i run last year?"
# total_distance_running = workout_service.get_run_workout_performance("distance", "sum", start_date, end_date)
# print( f"Total running distnace in 2023 is {total_distance_running}")  


# last_n_run_workouts = workout_service.get_last_n_run_workout_details(10)
# last_n_run_workouts_formatted = json.dumps(last_n_run_workouts, default=common_utils.datetime_converter, indent=4)
# print(f"Last 10 run workouts: {last_n_run_workouts_formatted}")

# load_metrics_service: IngestionLoadMetricsService = prod_env[EnvKeys.LOAD_METRICS_SERVICE.value]
# load_id_kicked_off_by_gpt = "4b1d809a-82f6-42cb-a0cb-1f802f85b927"
# new_workout_docs = load_metrics_service.get_documents_by_load_id(load_id_kicked_off_by_gpt)
# print(f" {len(new_workout_docs)} new workout documents were ingested by the load_id {load_id_kicked_off_by_gpt}: {new_workout_docs}")

# total_docs_before_reset = env_mgmt_utils.get_total_docs("prod")

# docs_deleted = env_mgmt_utils.delete_docs_with_load_id("prod", load_id_kicked_off_by_gpt)

# total_docs_after_reset = env_mgmt_utils.get_total_docs("prod")

# *********** Loading FHR Files ****************************

# fhir_files = ["Health Records 2014-01-01-2024-03-02.json"]
# env_mgmt_utils.load_fhir_medical_records("prod", fhir_files, delete_existing_fhir_collections=True)

# *********** Loading FHR Files ****************************


# *********** Reset Workout and Health-Metrics to Previous Inremental Load Point  ****************************

# 3/5/24: Reset Health Data Lake to an incremental load_id of b8d5ce24-549d-4387-8917-163aed0b3eb2 to recreate GPT prompting the user to load instead of automatically loadint eh data
# incremental_load_id_to_reset = "b8d5ce24-549d-4387-8917-163aed0b3eb2"
# env_mgmt_utils.reset_health_data_lake_to_incremental_run("prod", incremental_load_id_to_reset)

# *********** Reset Workout and Health-Metrics to Previous Inremental Load Point  ****************************

        
# current_medications = fhir_medication_service.get_current_medications()
# print("\n")
# print(f"Total number of current medications: {len(current_medications)}")
# print("\n")
# current_medication_summaries = create_medication_summaries(current_medications)
# pretty_printed_medications = json.dumps(current_medication_summaries, indent=4, default=common_utils.datetime_converter)
# print(f"Current medications: \n {pretty_printed_medications}")
# # convert json to compact string
# current_medications_json_string = json.dumps(current_medications, default=common_utils.datetime_converter)
# #print(f"Current medications: \n {current_medications_json_string}")

# pretty_preinted_medications = json.dumps(current_medications, indent=4, default=common_utils.datetime_converter)    
# logger.info(f"Current medications: \n {pretty_preinted_medications}")

# second_medication = current_medications[1]
# # pretty print json
# second_medication_json_pretty = json.dumps(second_medication, indent=4, default=common_utils.datetime_converter)
# print(f"Second medication in the collection: \n {second_medication_json_pretty}")


# For a specific document in fhir_medications collection, update any reference of dosage quantity to a new value (channging 5 mg to 10 mg), the reference to 5 needs to be updated to 10
# def update_dosage_for_medication():
#     #fhrid_id = "et40ZzkjRZVKw5lEEecZRmBZw8c0MUV1E2RULl8weckY3"
#     #doc_id = ObjectId("65e8e435bbaba839f891cd2e")
#     doc_id = ObjectId("6605e812483b67f7e37a7fe7")
    
    
                       
#     medications_collection = fhir_medication_service.mongo_health_lake["fhir_medications"] 

#     # Define the new values
#     old_numerica_value = 5
#     new_numeric_value = 10  # Replace with the new numeric value
    
#     old_text_value = "5 MG"
#     new_text_value = "10 MG"  # Replace with the new text value
    


#     # Update the numeric value and text references in the document
#     update_result_numeric = medications_collection.update_one(
#         {'_id': doc_id},
#         {'$set': {
#             'contained.0.ingredient.0.strength.numerator.value': new_numeric_value,
#             'contained.0.ingredient.0.strength.denominator.value': new_numeric_value,
#         }}
#     )
    
#     update_result_text = None
#     document = medications_collection.find_one({'_id': doc_id})
#     if document:
#         # Perform text replacements
#         document['contained'][0]['ingredient'][0]['itemCodeableConcept']['text'] = document['contained'][0]['ingredient'][0]['itemCodeableConcept']['text'].replace("nebivolol 5 MG Tabs", "nebivolol 10 MG Tabs")
#         document['medicationReference']['display'] = document['medicationReference']['display'].replace("nebivolol 5 MG Tabs", "nebivolol 10 MG Tabs")
#         document['dosageInstruction'][0]['patientInstruction'] = document['dosageInstruction'][0]['patientInstruction'].replace("Take 1 tablet (5 mg total) by mouth daily. TAKE 1 TABLET(5 MG) BY MOUTH EVERY DAY", "Take 1 tablet (10 mg total) by mouth daily. TAKE 1 TABLET(10 MG) BY MOUTH EVERY DAY")
#         document['dosageInstruction'][0]['text'] = document['dosageInstruction'][0]['text'].replace("Take 1 tablet (5 mg total) by mouth daily. TAKE 1 TABLET(5 MG) BY MOUTH EVERY DAY, Normal, Disp-90 tablet, R-3", "Take 1 tablet (10 mg total) by mouth daily. TAKE 1 TABLET(10 MG) BY MOUTH EVERY DAY, Normal, Disp-90 tablet, R-3")
#         document['displayName'] = document['displayName'].replace("nebivolol 5 MG Tabs", "nebivolol 10 MG Tabs")

#         # Update the document with new text values
#         update_result_text = medications_collection.update_one({'_id': doc_id}, {'$set': {
#             'contained.0.ingredient.0.itemCodeableConcept.text': document['contained'][0]['ingredient'][0]['itemCodeableConcept']['text'],
#             'medicationReference.display': document['medicationReference']['display'],
#             'dosageInstruction.0.patientInstruction': document['dosageInstruction'][0]['patientInstruction'],
#             'dosageInstruction.0.text': document['dosageInstruction'][0]['text'],
#             'displayName': document['displayName']
#         }})
#     return update_result_numeric, update_result_text
            
            
# update_result_dosage = update_dosage_for_medication()  
# print(f"Matched for numeric: {update_result_dosage[0].matched_count}")
# print(f"Modified for numeric: {update_result_dosage[0].modified_count}")
# print(f"Matched for text: {update_result_dosage[1].matched_count}")
# print(f"Modified fotr text: {update_result_dosage[1].modified_count}")



# def update_dates_for_medication():
    
#     #fhrid_id = "et40ZzkjRZVKw5lEEecZRmBZw8c0MUV1E2RULl8weckY3"
#     #doc_id = ObjectId("65e8e435bbaba839f891cd2e")
#     doc_id = ObjectId("6605e812483b67f7e37a7fe7")
    
#     medications_collection = fhir_medication_service.mongo_health_lake["fhir_medications"] 

    
#     old_start_date_string = "2023-04-30"
#     new_start_date_string = "2023-12-30"
    

    
#     # Update the start date
#     update_start_date_result = medications_collection.update_one(
#         {'_id': doc_id},
#         {'$set': {
#             'dispenseRequest.validityPeriod.start': new_start_date_string,
#         }}
#     )
    
#     old_end_date_string = "2023-04-28"
#     new_end_date_string = "2023-12-29"
    
#     #fhrid_id = "eI3WUdZwCWDkTMvnFeDrlQCEP1ierc72HofODRX8GRpI3"
#     #doc_id_previous_refill = ObjectId("65e8e435bbaba839f891cd18")
#     doc_id_previous_refill = ObjectId("6605e812483b67f7e37a7fd1")
    
    
    
#     # Update the end date of the previous refill for Bystolic/Nebvivolol
#     update_end_date_result = medications_collection.update_one(
#         {'_id': doc_id_previous_refill},
#         {'$set': {
#             'dispenseRequest.validityPeriod.end': new_end_date_string,
#         }}
#     )

   
#     return update_start_date_result, update_end_date_result

# update_result_date = update_dates_for_medication()
# print(f"Matched for date: {update_result_date[0].matched_count}")
# print(f"Modified for date: {update_result_date[0].modified_count}")

