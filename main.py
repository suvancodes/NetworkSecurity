from NetworkSecurity.component.data_ingestion import DataIngestion
from NetworkSecurity.Exciption.exciption import CustomException
from NetworkSecurity.logging.logging import logging
import sys
import os
from NetworkSecurity.entity.config_entity import DataIngestionConfig, DataValidationConfig, trainingPipelineConfig
from NetworkSecurity.component.data_validation import DataValidation
from NetworkSecurity.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact
if __name__ == "__main__":
    try:
        trainin_pipeline_config = trainingPipelineConfig()
        data_ingestion_config = DataIngestionConfig(training_pipeline_config=trainin_pipeline_config)
        data_ingestion = DataIngestion(data_ingestion_config=data_ingestion_config)
        logging.info("Exporting collection data as dataframe")
        data_ingestion_artifact = data_ingestion.initiate_data_ingestion()
        logging.info("Data ingestion completed successfully")
        print(data_ingestion_artifact)

        data_validation_config = DataValidationConfig(training_pipeline_config=trainin_pipeline_config)
        data_validation = DataValidation(data_validation_config=data_validation_config, data_ingestion_artifact=data_ingestion_artifact)
        data_validation_artifact = data_validation.initiate_data_validation()
        print(data_validation_artifact)

    except Exception as e:
        raise CustomException(e, sys)