import yaml
from NetworkSecurity.Exciption.exciption import CustomException
import sys
import os
import pickle  # or dill, if save_object uses dill
from NetworkSecurity.Exciption.exciption import CustomException
import numpy as np
from NetworkSecurity.utils.ml_utils.matric.classification_matric import get_classification_score
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
        """Load a Python object from a file using dill.

    Returns:
        _type_: The Python object loaded from the file.
    """
        with open(file_path, "rb") as file_obj:
            return pickle.load(file_obj)
    except Exception as e:
        raise CustomException(e, sys)
    
    
    
def load_numpy_array_data(file_path: str) -> np.array:
    """
    Load a NumPy array from a binary file.

    Args:
        file_path (str): The path to the binary file.
    Returns:
        np.array: The NumPy array loaded from the file.
    Raises:
        CustomException: If there is an error loading the NumPy array.
    """
    try:
        with open(file_path, 'rb') as f:
            return np.load(f)
    except Exception as e:
        raise CustomException(e, sys)
    
    
    
    
def evaluate_model(X_train, y_train, X_test, y_test, models):
    """
    Evaluates multiple machine learning models and returns a report of their performance.

    Args:
        X_train: Training features.
        y_train: Training labels.
        X_test: Testing features.
        y_test: Testing labels.
        models: A dictionary of model names and their corresponding model instances.
    Returns:
        dict: A report containing the performance of each model.
    Raises:
        CustomException: If there is an error during model evaluation.  
    """
    try:
        report = {}
        for model_name, model in models.items():
            model.fit(X_train, y_train)
            y_train_pred = model.predict(X_train)
            y_test_pred = model.predict(X_test)
            train_f1_score = get_classification_score(y_train, y_train_pred).f1_score
            test_f1_score = get_classification_score(y_test, y_test_pred).f1_score
            report[model_name] = {
                "train_f1_score": train_f1_score,
                "test_f1_score": test_f1_score
            }
        return report
    except Exception as e:
        raise CustomException(e, sys)

    