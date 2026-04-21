import yaml
from NetworkSecurity.Exciption.exciption import CustomException
import sys
import os
import dill
import numpy as np
import pandas as pd
import pickle

def read_yaml_file(file_path:str)->dict:
    """
    Reads a YAML file and returns its contents as a dictionary.

    Args:
        file_path (str): The path to the YAML file.
    Returns:
        dict: The contents of the YAML file as a dictionary.
    Raises:
        CustomException: If there is an error reading the YAML file.
    """
    try:
        with open(file_path, 'r') as yaml_file:
            return yaml.safe_load(yaml_file)
    except Exception as e:
        raise CustomException(e, sys)
    
    
    
    
    
def write_yaml_file(file_path:str, content : object, replace: bool = False)->None:
    """
    Writes content to a YAML file.

    Args:
        file_path (str): The path to the YAML file.
        content (object): The content to write to the YAML file.
        replace (bool): Whether to replace the file if it already exists.
    Returns:
        None
    Raises:
        CustomException: If there is an error writing to the YAML file.
    """
    try:
        if replace:
            if os.path.exists(file_path):
                os.remove(file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as yaml_file:
            yaml.dump(content, yaml_file)
    except Exception as e:
        raise CustomException(e, sys)   