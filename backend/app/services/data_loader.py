import pandas as pd
import os

def load_csv_data(filepath: str) -> pd.DataFrame:
    """
    Loads a CSV file into a pandas DataFrame.
    
    This function checks if the file exists before attempting to read it.
    It is a beginner-friendly utility that will be used later to load
    movie datasets into the application.
    
    Args:
        filepath (str): The absolute or relative path to the CSV file.
        
    Returns:
        pd.DataFrame: The loaded data as a pandas DataFrame.
        
    Raises:
        FileNotFoundError: If the provided filepath does not exist.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"The file {filepath} was not found.")
        
    # Read the CSV file using pandas
    data = pd.read_csv(filepath)
    
    return data
