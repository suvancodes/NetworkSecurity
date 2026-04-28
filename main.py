from NetworkSecurity.component.data_ingestion import DataIngestion
from NetworkSecurity.Exciption.exciption import CustomException
from NetworkSecurity.component.model_trainer import ModelTrainer
from NetworkSecurity.logging.logging import logging
import sys

from NetworkSecurity.entity.config_entity import (
    DataIngestionConfig,
    DataValidationConfig,
    ModelTrainerConfig,
    trainingPipelineConfig,
)
from NetworkSecurity.component.data_validation import DataValidation
from NetworkSecurity.component.data_transformation import DataTransformation, DataTransformationConfig


if __name__ == "__main__":
    try:
        training_pipeline_config = trainingPipelineConfig()

        data_ingestion_config = DataIngestionConfig(training_pipeline_config=training_pipeline_config)
        data_ingestion = DataIngestion(data_ingestion_config=data_ingestion_config)
        logging.info("Exporting collection data as dataframe")
        data_ingestion_artifact = data_ingestion.initiate_data_ingestion()
        logging.info("Data ingestion completed successfully")
        print(data_ingestion_artifact)

        data_validation_config = DataValidationConfig(training_pipeline_config=training_pipeline_config)
        data_validation = DataValidation(
            data_validation_config=data_validation_config,
            data_ingestion_artifact=data_ingestion_artifact
        )
        data_validation_artifact = data_validation.initiate_data_validation()
        print(data_validation_artifact)

        data_transformation_config = DataTransformationConfig(training_pipeline_config=training_pipeline_config)
        data_transformation = DataTransformation(
            data_transformation_config=data_transformation_config,
            data_validation_artifact=data_validation_artifact
        )
        logging.info("Initiating data transformation")
        data_transformation_artifact = data_transformation.initiate_data_transformation()
        print(data_transformation_artifact)
        logging.info("Data transformation completed successfully")

        logging.info("Model trainer component started")
        model_trainer_config = ModelTrainerConfig(training_pipeline_config=training_pipeline_config)
        model_trainer = ModelTrainer(
            model_trainer_config=model_trainer_config,
            data_transformation_artifact=data_transformation_artifact
        )
        model_trainer_artifact = model_trainer.initialize_model()
        logging.info("Model trainer component completed successfully")
        print(model_trainer_artifact)

    except Exception as e:
        raise CustomException(e, sys)