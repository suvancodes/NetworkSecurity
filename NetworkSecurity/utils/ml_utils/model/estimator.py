from NetworkSecurity.constant.traning_pipeline import SAVE_MODEL_DIR, MODEL_FILE_NAME
from NetworkSecurity.Exciption.exciption import CustomException
from NetworkSecurity.logging.logging import logging
import sys 
import numpy as np

class NetworkModel:
    def __init__(self, model, preprocessor):
        self.model = model
        self.preprocessor = preprocessor

    def predict(self, df):
        try:
            logging.info(f"Input DataFrame shape: {df.shape}")
            logging.info(f"Input DataFrame columns: {df.columns.tolist()}")
            logging.info(f"Input DataFrame dtypes: {df.dtypes.to_dict()}")
            
            # Transform the data
            transformed_data = self.preprocessor.transform(df)
            
            logging.info(f"Transformed data type: {type(transformed_data)}")
            logging.info(f"Transformed data shape: {transformed_data.shape if hasattr(transformed_data, 'shape') else 'N/A'}")
            
            # Verify transformed_data is not a dictionary
            if isinstance(transformed_data, dict):
                raise ValueError("Preprocessor returned dict instead of array")
            
            # Make predictions
            y_pred = self.model.predict(transformed_data)
            logging.info(f"Predictions shape: {y_pred.shape}")
            return y_pred
            
        except Exception as e:
            logging.error(f"Prediction failed: {e}", exc_info=True)
            raise

