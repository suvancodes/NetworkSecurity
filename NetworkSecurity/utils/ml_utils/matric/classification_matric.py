from NetworkSecurity.entity.artifact_entity import ClassificationMatrixArtifact
from sklearn.metrics import f1_score,precision_score,recall_score
from NetworkSecurity.Exciption.exciption import CustomException
import sys
def get_classification_score(y_true, y_pred) -> ClassificationMatrixArtifact:
    try:
        f1 = f1_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred)
        recall = recall_score(y_true, y_pred)
        classification_matrix_artifact = ClassificationMatrixArtifact(f1_score=f1, precision_score=precision, recall_score=recall)
        return classification_matrix_artifact
    except Exception as e:
        raise CustomException(e, sys)