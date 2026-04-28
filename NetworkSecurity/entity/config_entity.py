from datetime import datetime
from dataclasses import dataclass
import os

from bson import timestamp
from NetworkSecurity.constant import traning_pipeline


class trainingPipelineConfig:
    def __init__(self,timestamp: str = datetime.now()):
        timestamp = timestamp.strftime("%m-%d-%Y-%H-%M-%S")
        self.pipeline_name = traning_pipeline.PIPELINE_NAME
        self.artifact_name = traning_pipeline.ARTIFACT_DIR
        self.artifact_dir = os.path.join(traning_pipeline.ARTIFACT_DIR,timestamp)
        self.timestamp:str = timestamp
        
class DataIngestionConfig:
    def __init__(self,training_pipeline_config: trainingPipelineConfig):
        self.data_ingestion_dir:str = os.path.join(training_pipeline_config.artifact_dir, traning_pipeline.DATA_INGESTION_DIR_NAME)
        self.feature_store_dir:str = os.path.join(self.data_ingestion_dir, traning_pipeline.DATA_INGESTION_FEATURE_STORE_DIR, traning_pipeline.FILE_NAME)
        self.traning_file_path:str = os.path.join(self.data_ingestion_dir, traning_pipeline.DATA_INGESTION_INGESTED_DIR, traning_pipeline.TRANING_FILE_NAME)
        self.test_file_path:str = os.path.join(self.data_ingestion_dir, traning_pipeline.DATA_INGESTION_INGESTED_DIR, traning_pipeline.TEST_FILE_NAME)
        self.collection_name:str = traning_pipeline.DATA_INGESTION_COLLECTION_NAME
        self.database_name:str = traning_pipeline.DATA_INGESTION_DATABASE_NAME
        self.train_test_split_ratio:float = traning_pipeline.DATA_INGESTION_TRAIN_TEST_SPLIT_RATION
        self.feature_store_file_path: str = os.path.join(self.data_ingestion_dir,traning_pipeline.DATA_INGESTION_FEATURE_STORE_DIR,traning_pipeline.FILE_NAME)
        
        
        
class DataValidationConfig:
    def __init__(self,training_pipeline_config:trainingPipelineConfig):
        self.data_validation_dir:str = os.path.join(training_pipeline_config.artifact_dir,traning_pipeline.DATA_INGESTION_DIR_NAME)
        self.valid_data_dir:str = os.path.join(self.data_validation_dir,traning_pipeline.DATA_VALIDATION_VALID_DIR)
        self.invalid_data_dir:str = os.path.join(self.data_validation_dir,traning_pipeline.DATA_VALIDATION_INVALID_DIR)
        self.valid_train_path:str = os.path.join(self.data_validation_dir,traning_pipeline.DATA_VALIDATION_VALID_DIR,traning_pipeline.TRANING_FILE_NAME)
        self.valid_test_path:str = os.path.join(self.data_validation_dir,traning_pipeline.DATA_VALIDATION_VALID_DIR,traning_pipeline.TEST_FILE_NAME)
        self.invalid_train_file_path:str = os.path.join(self.data_validation_dir,traning_pipeline.DATA_VALIDATION_INVALID_DIR,traning_pipeline.TRANING_FILE_NAME)
        self.invalid_test_file_path:str = os.path.join(self.data_validation_dir,traning_pipeline.DATA_VALIDATION_INVALID_DIR,traning_pipeline.TEST_FILE_NAME)
        self.drift_report_file_path:str = os.path.join(self.data_validation_dir,traning_pipeline.DATA_VALIDATION_DRIFT_REPORT_DIR,traning_pipeline.DATA_VALIDATION_DRIFT_REPORT_FILE_NAME)

class DataTransformationConfig:
    def __init__(self,training_pipeline_config:trainingPipelineConfig):
        self.data_transformation_dir:str = os.path.join(training_pipeline_config.artifact_dir,traning_pipeline.DATA_TRANSFORMATION_DIR_NAME)
        self.transformed_train_dir:str = os.path.join(self.data_transformation_dir,traning_pipeline.DATA_TRANSFORMATION_TRANSFORMED_DIR,traning_pipeline.TRANING_FILE_NAME)
        self.transformed_test_dir:str = os.path.join(self.data_transformation_dir,traning_pipeline.DATA_TRANSFORMATION_TRANSFORMED_DIR,traning_pipeline.TEST_FILE_NAME)
        self.preprocessed_object_file_path:str = os.path.join(self.data_transformation_dir,traning_pipeline.DATA_TRANSFORMATION_PREPROCESSING_DIR,traning_pipeline.DATA_TRANSFORMATION_PREPROCESSING_OBJECT_FILE_NAME)
        
        
        
class ModelTrainerConfig:
    def __init__(self,training_pipeline_config:trainingPipelineConfig):
        self.model_trainer_dir:str = os.path.join(training_pipeline_config.artifact_dir,traning_pipeline.MODEL_TRAINER_DIR_NAME)
        self.trained_model_file_path:str = os.path.join(self.model_trainer_dir,traning_pipeline.MODEL_TRAINER_TRAINED_MODEL_FILE_NAME)
        self.expected_score:float = traning_pipeline.MODEL_TRAINER_EXPECTED_SCORE
        self.overfitting_underfitting_threshold:float = traning_pipeline.MODEL_TRAINER_OVERFITTING_UNDERFITTING_THRESHOLD