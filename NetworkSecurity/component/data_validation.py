from NetworkSecurity.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact
from NetworkSecurity.entity.config_entity import DataValidationConfig
from NetworkSecurity.Exciption.exciption import CustomException
from NetworkSecurity.logging.logging import logging
from scipy.stats import ks_2samp
import pandas as pd
import os,sys

from NetworkSecurity.constant.traning_pipeline import SCHEMA_FILE_PATH

from NetworkSecurity.utils.main_utils.utils import read_yaml_file,write_yaml_file

class DataValidation:
    def __init__(self, data_validation_config: DataValidationConfig,
                 data_ingestion_artifact: DataIngestionArtifact):
        try:
            self.data_validation_config = data_validation_config
            self.data_ingestion_artifact = data_ingestion_artifact
            self.schema_config = read_yaml_file(SCHEMA_FILE_PATH)
        except Exception as e:
            raise CustomException(e, sys)
    
    def validate_number_of_columns(self, dataframe: pd.DataFrame) -> bool:
        try:
            number_of_columns = len(self.schema_config['columns'])
            logging.info(f"Required number of columns: {number_of_columns}")
            logging.info(f"Dataframe has columns: {dataframe.columns}")
            if len(dataframe.columns) == number_of_columns:
                return True
            return False
        except Exception as e:
            raise CustomException(e, sys)
        
    def detect_dataset_drift(self, base_df: pd.DataFrame, current_df: pd.DataFrame, threshold: float = 0.05) -> bool:
        try:
            status = True
            report = {}
            for column in base_df.columns:
                base_data = base_df[column].dropna()
                current_data = current_df[column].dropna()
                is_sample_dist = ks_2samp(base_data, current_data)
                if threshold <= is_sample_dist.pvalue:
                    is_found = False
                else:
                    is_found = True
                    status = False
                report.update({column: {
                    "p_value": float(is_sample_dist.pvalue),
                    "drift_status": is_found
                }})
                drift_report_file_path = self.data_validation_config.drift_report_file_path
                dir_path = os.path.dirname(drift_report_file_path)
                os.makedirs(dir_path, exist_ok=True)
                write_yaml_file(file_path=drift_report_file_path, content=report, replace=True)
            return status

        except Exception as e:
            raise CustomException(e, sys)
    
    def initiate_data_validation(self) -> DataValidationArtifact:
        try:
            logging.info("Starting data validation")
            train_file_path = self.data_ingestion_artifact.traning_file_path
            test_file_path = self.data_ingestion_artifact.test_file_path
            train_df = pd.read_csv(train_file_path)
            test_df = pd.read_csv(test_file_path)

            # Validate number of columns for both train and test dataframes
            is_valid_train = self.validate_number_of_columns(train_df)
            is_valid_test = self.validate_number_of_columns(test_df)

            if not is_valid_train or not is_valid_test:
                raise CustomException("Data validation failed: Incorrect number of columns.", sys)
            # Detect dataset drift between train and test dataframes
            is_drift_detected = self.detect_dataset_drift(train_df, test_df)
            dirtory_path = os.path.dirname(self.data_validation_config.valid_train_path)
            os.makedirs(dirtory_path, exist_ok=True)
            train_df.to_csv(self.data_validation_config.valid_train_path, index=False, header=True)
            test_df.to_csv(self.data_validation_config.valid_test_path, index=False, header=True)
            data_validation_artifact = DataValidationArtifact(
                validation_status=is_drift_detected,
                valid_train_file_path=self.data_validation_config.valid_train_path,
                valid_test_file_path=self.data_validation_config.valid_test_path,
                invalid_train_file_path=self.data_validation_config.invalid_train_file_path,
                invalid_test_file_path=self.data_validation_config.invalid_test_file_path,
                drift_report_file_path=self.data_validation_config.drift_report_file_path
            )
            return data_validation_artifact
            logging.info("Data validation completed successfully")
        except Exception as e:
            raise CustomException(e, sys)
        
    