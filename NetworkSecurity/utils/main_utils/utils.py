import yaml
from NetworkSecurity.Exciption.exciption import CustomException
import sys
import os
import pickle  # or dill, if save_object uses dill
from NetworkSecurity.Exciption.exciption import CustomException
import numpy as np
import dill
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
    
    
    
    
    
def save_nampy_array_data(file_path:str, array: np.ndarray)->None:
    """
    Saves a NumPy array to a binary file.

    Args:
        file_path (str): The path to the binary file.
        array (np.ndarray): The NumPy array to save.
    Returns:
        None
    Raises:
        CustomException: If there is an error saving the NumPy array.
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as f:
            np.save(f, array)
    except Exception as e:
        raise CustomException(e, sys)
    
    
def save_object(file_path:str, obj:object)->None:
    """
    Saves a Python object to a file using dill.

    Args:
        file_path (str): The path to the file where the object will be saved.
        obj (object): The Python object to save.
    Returns:
        None
    Raises:
        CustomException: If there is an error saving the object.
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as f:
            dill.dump(obj, f)
    except Exception as e:
        raise CustomException(e, sys)
    
    
def save_numpy_array_data(file_path: str, array: np.array):
        """
        Save numpy array data to file
        file_path: str location of file to save
        array: np.array data to save
        """
        dir_path = os.path.dirname(file_path)
        os.makedirs(dir_path, exist_ok=True)
        np.save(file_path, array)

def load_object(file_path: str):
    try:
        with open(file_path, "rb") as file_obj:
            return pickle.load(file_obj)
    except Exception as e:
        raise CustomException(e, sys)