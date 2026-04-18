import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from NetworkSecurity.Exciption.exciption import CustomException
from NetworkSecurity.logging.logging import logging
from NetworkSecurity.entity.config_entity import DataIngestionConfig, trainingPipelineConfig
import pandas as pd
from sklearn.model_selection import train_test_split
from dotenv import load_dotenv
import pymongo
import numpy as np

from NetworkSecurity.entity.artifact_entity import DataIngestionArtifact
# read data from mongodb
load_dotenv(dotenv_path=".env")
MONGO_DB_URL = os.getenv("MONGO_DB_URL")
print("Mongo URL Loaded Successfully ✅")


class DataIngestion:
    def __init__(self, data_ingestion_config: DataIngestionConfig):
        try:
            self.data_ingestion_config = data_ingestion_config
            logging.info(f"{'>>'*20} Data Ingestion {'<<'*20}")
            
        except Exception as e:
            raise CustomException(e, sys)
    
    def export_collection_as_dataframe(self):
        try:
            database_name = self.data_ingestion_config.database_name
            collection_name = self.data_ingestion_config.collection_name
            self.mongo_client = pymongo.MongoClient(MONGO_DB_URL)
            collection = self.mongo_client[database_name][collection_name]
            
            df = pd.DataFrame(list(collection.find()))
            if "_id" in df.columns.to_list():
                df = df.drop(columns=['_id'],axis=1)
                
            df = df.replace({'na':np.nan})
            return df
        except Exception as e:
            raise CustomException(e,sys)
        
    def export_data_into_featurestore(self,dataframe: pd.DataFrame):
        try:
            feature_store_file_path = self.data_ingestion_config.feature_store_file_path
            dir_path = os.path.dirname(feature_store_file_path)
            os.makedirs(dir_path,exist_ok=True)
            dataframe.to_csv(feature_store_file_path,index=False,header=True)
            return dataframe
            
            
        except Exception as e:
            raise CustomException(e,sys)
    
    
    def split_data_as_train_test(self,datafream):
        try:
            train_set,test_set = train_test_split(
                datafream,test_size= self.data_ingestion_config.train_test_split_ratio
            )
            logging.info('perfrom train test split successfully')
            logging.info("Exited split_data_as_train_test method of Data Ingestion class")
            
            dir_path = os.path.dirname(self.data_ingestion_config.traning_file_path)
            os.makedirs(dir_path,exist_ok=True)
            train_set.to_csv(self.data_ingestion_config.traning_file_path,index=False,header=True)
            test_set.to_csv(self.data_ingestion_config.test_file_path,index=False,header=True)
        except Exception as e:
            raise CustomException(e,sys)
    
    def initiate_data_ingestion(self):
        try:
            df = self.export_collection_as_dataframe()
            df = self.export_data_into_featurestore(df)
            self.split_data_as_train_test(df)
            data_ingestion_artifact = DataIngestionArtifact(
                traning_file_path=self.data_ingestion_config.traning_file_path,
                test_file_path=self.data_ingestion_config.test_file_path
            )
            return data_ingestion_artifact
            
            
            
        except Exception as e:
            raise CustomException(e,sys)