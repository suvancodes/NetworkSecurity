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