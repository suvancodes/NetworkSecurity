import os
import sys
from NetworkSecurity.Exciption.exciption import CustomException
from NetworkSecurity.entity.artifact_entity import DataTransformationArtifact,DataValidationArtifact
from NetworkSecurity.entity.config_entity import DataTransformationConfig,trainingPipelineConfig,DataValidationConfig,DataIngestionConfig,ModelTrainerConfig
from NetworkSecurity.logging.logging import logging
from NetworkSecurity.Exciption.exciption import CustomException
from NetworkSecurity.component.model_trainer import ModelTrainer
from NetworkSecurity.component.data_transformation import DataTransformation
from NetworkSecurity.component.data_validation import DataValidation
from NetworkSecurity.component.data_ingestion import DataIngestion
from NetworkSecurity.entity.artifact_entity import DataIngestionArtifact
from NetworkSecurity.entity.artifact_entity import DataValidationArtifact
from NetworkSecurity.entity.artifact_entity import ModelTrainerArtifact,DataTransformationArtifact

class TrainPipeline:
    def __init__(self):
        try:
            self.training_pipeline_config = trainingPipelineConfig()
        except Exception as e:
            raise CustomException(e, sys)
        
    def start_data_ingestion(self) -> DataIngestionArtifact:
        try:
            logging.info("Starting data ingestion")
            data_ingestion_config = DataIngestionConfig(training_pipeline_config=self.training_pipeline_config)
            data_ingestion = DataIngestion(data_ingestion_config=data_ingestion_config)
            data_ingestion_artifact = data_ingestion.initiate_data_ingestion()
            logging.info("Completed data ingestion")
            return data_ingestion_artifact
        except Exception as e:
            raise CustomException(e, sys)
        
        
    def start_data_validation(self, data_ingestion_artifact: DataIngestionArtifact) -> DataValidationArtifact:
        try:
            logging.info("Starting data validation")
            data_validation_config = DataValidationConfig(training_pipeline_config=self.training_pipeline_config)
            data_validation = DataValidation(data_validation_config=data_validation_config, data_ingestion_artifact=data_ingestion_artifact)
            data_validation_artifact = data_validation.initiate_data_validation()
            logging.info("Completed data validation")
            return data_validation_artifact
        except Exception as e:
            raise CustomException(e, sys)
        
        
    def start_data_transformation(self, data_validation_artifact: DataValidationArtifact) -> DataTransformationArtifact:
        try:
            logging.info("Starting data transformation")
            data_transformation_config = DataTransformationConfig(training_pipeline_config=self.training_pipeline_config)
            data_transformation = DataTransformation(data_transformation_config=data_transformation_config, data_validation_artifact=data_validation_artifact)
            data_transformation_artifact = data_transformation.initiate_data_transformation()
            logging.info("Completed data transformation")
            return data_transformation_artifact
        except Exception as e:
            raise CustomException(e, sys)
        
    def start_model_trainer(self, data_transformation_artifact: DataTransformationArtifact) -> ModelTrainerArtifact:
        try:
            logging.info("Starting model trainer")
            model_trainer_config = ModelTrainerConfig(training_pipeline_config=self.training_pipeline_config)
            model_trainer = ModelTrainer(model_trainer_config=model_trainer_config, data_transformation_artifact=data_transformation_artifact)
            model_trainer_artifact = model_trainer.initialize_model()
            logging.info("Completed model trainer")
            return model_trainer_artifact
        except Exception as e:
            raise CustomException(e, sys)
        
    def run_pipeline(self):
        try:
            data_ingestion_artifact = self.start_data_ingestion()
            data_validation_artifact = self.start_data_validation(data_ingestion_artifact=data_ingestion_artifact)
            data_transformation_artifact = self.start_data_transformation(data_validation_artifact=data_validation_artifact)
            model_trainer_artifact = self.start_model_trainer(data_transformation_artifact=data_transformation_artifact)
            return model_trainer_artifact
        except Exception as e:
            raise CustomException(e, sys)
