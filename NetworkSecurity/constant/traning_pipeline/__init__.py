import os
import sys
import numpy as np
import pandas as pd

""" 
Data Ingestion releted consyant start with DATA_INJECTION VAR NAME
"""
DATA_INGESTION_COLLECTION_NAME: str = "NetworkData"
DATA_INGESTION_DATABASE_NAME: str = "KRISHAI"
DATA_INGESTION_DIR_NAME: str = "data_ingestion"
DATA_INGESTION_FEATURE_STORE_DIR: str = "feature_store"
DATA_INGESTION_INGESTED_DIR: str = "ingested"
DATA_INGESTION_TRAIN_TEST_SPLIT_RATION: float = 0.2


"""
DEFINING COMMON CONSTANTS FOR TRAINING PIPELINE
"""

TERGET_COLUMN: str = "Result"
PIPELINE_NAME: str = "NetworkSecurity"
ARTIFACT_DIR: str = "artifacts"
FILE_NAME: str = "phisingData.csv"
TRANING_FILE_NAME: str = "train.csv"
TEST_FILE_NAME: str = "test.csv"

