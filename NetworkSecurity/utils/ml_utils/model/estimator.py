from NetworkSecurity.constant.traning_pipeline import SAVE_MODEL_DIR, MODEL_FILE_NAME
from NetworkSecurity.Exciption.exciption import CustomException
from NetworkSecurity.logging.logging import logging
import sys 

class NetworkModel:
    def __init__(self,preprocessed,model):
        try:
            self.preprocessed = preprocessed
            self.model = model
        except Exception as e:
            raise CustomException(e, sys)
    def predict(self,X):
        try:
            return self.model.predict(X)
        except Exception as e:
            raise CustomException(e, sys)