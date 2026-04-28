from dataclasses import dataclass
@dataclass
class DataIngestionArtifact:
    traning_file_path: str
    test_file_path: str
    
    
@dataclass
class DataValidationArtifact:
    validation_status:bool
    valid_train_file_path:str
    valid_test_file_path:str
    invalid_train_file_path:str
    invalid_test_file_path:str
    drift_report_file_path:str
    
    
@dataclass
class DataTransformationArtifact:
    transformed_train_dir:str
    transformed_test_dir:str
    preprocessed_object_file_path:str
    
    

@dataclass
class ClassificationMatrixArtifact:
    f1_score:float
    precision_score:float
    recall_score:float
    

@dataclass
class ModelTrainerArtifact:
    trained_model_file_path:str
    train_matrix_artifact:ClassificationMatrixArtifact
    test_matrix_artifact:ClassificationMatrixArtifact
