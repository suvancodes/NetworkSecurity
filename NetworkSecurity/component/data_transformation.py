import sys
import os
from NetworkSecurity.Exciption.exciption import CustomException
import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer

from NetworkSecurity.constant.traning_pipeline import TERGET_COLUMN,DATA_TRANSFORMATION_IMPUTER_PARANS
from NetworkSecurity.entity.artifact_entity import DataTransformationArtifact,DataValidationArtifact
from NetworkSecurity.entity.config_entity import DataTransformationConfig
from NetworkSecurity.logging.logging import logging
from NetworkSecurity.Exciption.exciption import CustomException
from NetworkSecurity.utils.main_utils.utils import read_yaml_file,write_yaml_file,save_numpy_array_data,save_object,load_object
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder


class DataTransformation:
    def __init__(self, data_transformation_config: DataTransformationConfig,
                 data_validation_artifact: DataValidationArtifact):
        try:
            self.data_transformation_config = data_transformation_config
            self.data_validation_artifact = data_validation_artifact
        except Exception as e:
            raise CustomException(e, sys)
        
        
    def get_data_transformer_object(self) -> Pipeline:
        """
        IT initilize knn imputer obj using parameter in training_pipeline.py
        it return pipeline obj and knn imputre obj in the first stap 
        arg:
        cls : dataTrabsformation
        
        return: pipeline obj and knn imputer obj

        """
        logging.info("Entered the get_data_transformer_object method of Data_Transformation class")
        try:
            logging.info("Initiating data transformation object")

            imputer_params = dict(DATA_TRANSFORMATION_IMPUTER_PARANS)
            if "missing values" in imputer_params:
                imputer_params["missing_values"] = imputer_params.pop("missing values")

            knn_imputer: KNNImputer = KNNImputer(**imputer_params)
            processor: Pipeline = Pipeline([("imputer", knn_imputer)])
            return processor
        except Exception as e:
            raise CustomException(e, sys)
        
    


    def initiate_data_transformation(self) -> DataTransformationArtifact:
        try:
            logging.info("Initiating data transformation")

            train_df = pd.read_csv(self.data_validation_artifact.valid_train_file_path)
            test_df = pd.read_csv(self.data_validation_artifact.valid_test_file_path)

            logging.info("Splitting input and target features from train and test dataframe")
            input_feature_train_df = train_df.drop(columns=[TERGET_COLUMN], axis=1)
            target_feature_train_df = train_df[TERGET_COLUMN].replace(-1, 0)

            input_feature_test_df = test_df.drop(columns=[TERGET_COLUMN], axis=1)
            target_feature_test_df = test_df[TERGET_COLUMN].replace(-1, 0)

            preprocessor = self.get_data_transformer_object()
            preprocessor_object = preprocessor.fit(input_feature_train_df)

            logging.info("Applying preprocessing object on training and testing dataframe")
            input_feature_train_arr = preprocessor_object.transform(input_feature_train_df)
            input_feature_test_arr = preprocessor_object.transform(input_feature_test_df)

            train_arr = np.c_[input_feature_train_arr, np.array(target_feature_train_df)]
            test_arr = np.c_[input_feature_test_arr, np.array(target_feature_test_df)]

            save_numpy_array_data(self.data_transformation_config.transformed_train_dir, train_arr)
            save_numpy_array_data(self.data_transformation_config.transformed_test_dir, test_arr)
            save_object(self.data_transformation_config.preprocessed_object_file_path, preprocessor_object)

            data_transformation_artifact = DataTransformationArtifact(
                transformed_train_dir=self.data_transformation_config.transformed_train_dir,
                transformed_test_dir=self.data_transformation_config.transformed_test_dir,
                preprocessed_object_file_path=self.data_transformation_config.preprocessed_object_file_path,
            )

            return data_transformation_artifact

        except Exception as e:
            raise CustomException(e, sys)