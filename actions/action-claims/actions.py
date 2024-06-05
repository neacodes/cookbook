"""A simple AI Action to pull Claim Settelemnt
"""


from sema4ai.actions import action
import pandas as pd
import random

@action
def get_claims() -> str:
    """Select random rows from Claim Requests CSV and return as string.

    Reads the CSV file, picks 3-10 random rows, and returns them with columns: Social ID, Full Name, Amount, and Description.

    Args:
        None

    Returns:
        str: A string with selected claim details.
    """
    # Read the CSV file
    df = pd.read_csv("Worker_Claim_Settlement_Data_with_Social_ID.csv")

    # Select a random number of rows between 3 and 10
    num_rows = random.randint(3, 10)
    random_rows = df.sample(n=num_rows)
    
    # Select relevant columns
    selected_data = random_rows[['Social ID', 'Full Name', 'Amount', 'Description']]
    
    # Return the DataFrame as a string
    return selected_data.to_string(index=False)
