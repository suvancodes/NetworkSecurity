import os
import sys
import json

from dotenv import load_dotenv

# ✅ Force load .env
load_dotenv(dotenv_path=".env")

MONGO_DB_URL = os.getenv("MONGO_DB_URL")
print("ENV VALUE:", MONGO_DB_URL)  # debug

import certifi
ca = certifi.where()

import pandas as pd
import pymongo

from NetworkSecurity.Exciption.exciption import CustomException
from NetworkSecurity.logging.logging import logging


class NetworkDataExtract:
    def __init__(self):
        try:
            if MONGO_DB_URL is None:
                raise Exception("MongoDB URL is not set in .env file")

            print("Mongo URL Loaded Successfully ✅")

        except Exception as e:
            raise CustomException(e, sys)

    def csv_to_json_convertor(self, file_path):
        try:
            if not os.path.exists(file_path):
                raise Exception(f"File not found: {file_path}")

            data = pd.read_csv(file_path)
            data.reset_index(drop=True, inplace=True)

            records = list(json.loads(data.T.to_json()).values())

            print(f"CSV Loaded Successfully ✅ Rows: {len(records)}")
            return records

        except Exception as e:
            raise CustomException(e, sys)

    def insert_data_mongodb(self, records, database, collection):
        try:
            if not records:
                raise Exception("No records to insert")

            # ✅ MongoDB connection with TLS
            mongo_client = pymongo.MongoClient(
                MONGO_DB_URL,
                tls=True,
                tlsCAFile=ca
            )

            # ✅ Check connection
            mongo_client.admin.command('ping')
            print("MongoDB Connected Successfully ✅")

            db = mongo_client[database]
            col = db[collection]

            # ✅ Insert data
            result = col.insert_many(records)

            print(f"Inserted {len(result.inserted_ids)} records ✅")

            # ✅ Debug DB list
            print("Databases:", mongo_client.list_database_names())

            return len(result.inserted_ids)

        except Exception as e:
            raise CustomException(e, sys)


if __name__ == "__main__":
    try:
        FILE_PATH = os.path.join("Network_Data", "phisingData.csv")
        DATABASE = "KRISHAI"
        COLLECTION = "NetworkData"

        networkobj = NetworkDataExtract()

        # ✅ Convert CSV → JSON
        records = networkobj.csv_to_json_convertor(FILE_PATH)

        # ✅ Show sample only
        print("Sample Data:", records[:2])

        # ✅ Insert into MongoDB
        count = networkobj.insert_data_mongodb(
            records, DATABASE, COLLECTION
        )

        print(f"Final Insert Count: {count} 🚀")

    except Exception as e:
        raise CustomException(e, sys)