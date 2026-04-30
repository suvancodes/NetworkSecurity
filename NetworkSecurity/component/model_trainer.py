import os
import sys
import numpy as np
import pandas as pd
import glob
from numbers import Real

from sklearn.metrics import f1_score

from NetworkSecurity.Exciption.exciption import CustomException
from NetworkSecurity.entity.artifact_entity import DataTransformationArtifact, ModelTrainerArtifact
from NetworkSecurity.entity.config_entity import ModelTrainerConfig
from NetworkSecurity.logging.logging import logging
from NetworkSecurity.utils.main_utils.utils import save_object, load_object, load_numpy_array_data
from NetworkSecurity.utils.ml_utils.matric.classification_matric import get_classification_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from NetworkSecurity.utils.main_utils.utils import evaluate_model
from NetworkSecurity.utils.ml_utils.model.estimator import NetworkModel

import mlflow
import dagshub

dagshub.init(repo_owner='suvankarpayra12', repo_name='NetworkSecurity', mlflow=True)


# mlflow.set_tracking_uri("sqlite:///mlflow.db")
# mlflow.set_experiment("NetworkSecurity")

class ModelTrainer:
    def __init__(
        self,
        model_trainer_config: ModelTrainerConfig,
        data_transformation_artifact: DataTransformationArtifact,
    ):
        try:
            self.model_trainer_config = model_trainer_config
            self.data_transformation_artifact = data_transformation_artifact
        except Exception as e:
            raise CustomException(e, sys)
        
    def _resolve_existing_path(self, expected_path: str, kind: str) -> str:
        """
        Resolve transformed file path robustly.
        kind: 'train' or 'test'
        """
        try:
            candidates = [expected_path]

            root, ext = os.path.splitext(expected_path)
            if ext.lower() != ".npy":
                candidates.append(root + ".npy")
            if ext.lower() != ".csv":
                candidates.append(root + ".csv")

            # direct candidates
            for p in candidates:
                if os.path.exists(p):
                    return p

            # search inside same folder
            parent = os.path.dirname(expected_path)
            if os.path.isdir(parent):
                for pattern in [f"{kind}*.npy", f"{kind}*.csv", f"*{kind}*.npy", f"*{kind}*.csv"]:
                    hits = sorted(glob.glob(os.path.join(parent, pattern)))
                    if hits:
                        return hits[0]

            # search recursively under data_transformation folder for this run
            dt_root = os.path.dirname(parent) if parent else "."
            if os.path.isdir(dt_root):
                for pattern in [f"**/{kind}*.npy", f"**/{kind}*.csv", f"**/*{kind}*.npy", f"**/*{kind}*.csv"]:
                    hits = sorted(glob.glob(os.path.join(dt_root, pattern), recursive=True))
                    if hits:
                        return hits[0]

            raise FileNotFoundError(
                f"Transformed {kind} file not found. Expected: {expected_path}"
            )
        except Exception as e:
            raise CustomException(e, sys)

    def _load_transformed_array(self, file_path: str, kind: str) -> np.ndarray:
        """
        Supports both .npy and .csv transformed outputs.
        """
        try:
            resolved_path = self._resolve_existing_path(file_path, kind)
            ext = os.path.splitext(resolved_path)[1].lower()

            logging.info(f"Resolved {kind} transformed path: {resolved_path}")

            if ext == ".npy":
                return load_numpy_array_data(resolved_path)

            if ext == ".csv":
                return pd.read_csv(resolved_path).to_numpy()

            # fallback
            try:
                return load_numpy_array_data(resolved_path)
            except Exception:
                return pd.read_csv(resolved_path).to_numpy()

        except Exception as e:
            raise CustomException(e, sys)

    def _extract_numeric_score(self, value):
        """
        Extract a comparable numeric score from evaluate_model() output.
        Supports float/int or nested dict reports.
        """
        if isinstance(value, Real):
            return float(value)

        if isinstance(value, dict):
            # Preferred keys first
            for key in ["f1_score", "roc_auc_score", "accuracy", "test_score", "score"]:
                v = value.get(key)
                if isinstance(v, Real):
                    return float(v)

            # Recursive search in nested dicts
            for v in value.values():
                score = self._extract_numeric_score(v)
                if score is not None:
                    return score

        return None

    def _read_metric(self, metric_obj, field_name: str):
        """Read metric value from dict-like or object-like metric containers."""
        if metric_obj is None:
            return None
        if isinstance(metric_obj, dict):
            return metric_obj.get(field_name)
        return getattr(metric_obj, field_name, None)

    def tracking_mlflow(self, model, classification_train_metric, classification_test_metric, log_model: bool = False):
        with mlflow.start_run():
            train_f1_score = self._read_metric(classification_train_metric, "f1_score")
            train_precision_score = self._read_metric(classification_train_metric, "precision_score")
            train_recall_score = self._read_metric(classification_train_metric, "recall_score")

            test_f1_score = self._read_metric(classification_test_metric, "f1_score")
            test_precision_score = self._read_metric(classification_test_metric, "precision_score")
            test_recall_score = self._read_metric(classification_test_metric, "recall_score")

            if train_f1_score is not None:
                mlflow.log_metric("train_f1_score", float(train_f1_score))
            if train_precision_score is not None:
                mlflow.log_metric("train_precision_score", float(train_precision_score))
            if train_recall_score is not None:
                mlflow.log_metric("train_recall_score", float(train_recall_score))

            if test_f1_score is not None:
                mlflow.log_metric("test_f1_score", float(test_f1_score))
            if test_precision_score is not None:
                mlflow.log_metric("test_precision_score", float(test_precision_score))
            if test_recall_score is not None:
                mlflow.log_metric("test_recall_score", float(test_recall_score))

            if log_model:
                mlflow.sklearn.log_model(model, "model")

    def train_model(self, X_train, y_train, X_test, y_test) -> ModelTrainerArtifact:
        try:
            models = {
                "LogisticRegression": LogisticRegression(),
                "RandomForestClassifier": RandomForestClassifier(),
                "GradientBoostingClassifier": GradientBoostingClassifier(),
                "AdaBoostClassifier": AdaBoostClassifier(),
                "DecisionTreeClassifier": DecisionTreeClassifier(),
                "KNeighborsClassifier": KNeighborsClassifier(),
            }

            model_report = evaluate_model(X_train, y_train, X_test, y_test, models)

            if not isinstance(model_report, dict):
                raise ValueError(f"evaluate_model() must return dict, got: {type(model_report)}")

            comparable_scores = {}
            for model_name, report_value in model_report.items():
                score = self._extract_numeric_score(report_value)
                if score is not None:
                    comparable_scores[model_name] = score
                else:
                    logging.warning(f"Skipping model '{model_name}' due to non-numeric score: {report_value}")

            if not comparable_scores:
                raise ValueError(f"No numeric scores found in model_report: {model_report}")

            best_model_name = max(comparable_scores, key=comparable_scores.get)
            best_model_score = comparable_scores[best_model_name]
            best_model = models[best_model_name]

            # Ensure fitted
            best_model.fit(X_train, y_train)

            y_train_pred = best_model.predict(X_train)
            y_test_pred = best_model.predict(X_test)

            classification_train_metric = get_classification_score(y_train, y_train_pred)
            classification_test_metric = get_classification_score(y_test, y_test_pred)
            
            # Track MLflow
            self.tracking_mlflow(best_model, classification_train_metric, classification_test_metric, log_model=False)


            logging.info(
                f"Best model: {best_model_name} | Best score: {best_model_score} | "
                f"Train metric: {classification_train_metric} | Test metric: {classification_test_metric}"
            )

            preprocessor = load_object(self.data_transformation_artifact.preprocessed_object_file_path)

            trained_model_file_path = self.model_trainer_config.trained_model_file_path
            os.makedirs(os.path.dirname(trained_model_file_path), exist_ok=True)

            network_model = NetworkModel(preprocessor=preprocessor, model=best_model)
            save_object(trained_model_file_path, obj=network_model)
            save_object('final_model/model.pkl', obj=best_model)

            model_trainer_artifact = ModelTrainerArtifact(
                trained_model_file_path=trained_model_file_path,
                train_matrix_artifact=classification_train_metric,
                test_matrix_artifact=classification_test_metric,
            )

            logging.info(f"Model trainer artifact: {model_trainer_artifact}")
            return model_trainer_artifact

        except Exception as e:
            raise CustomException(e, sys)

    def initialize_model(self) -> ModelTrainerArtifact:
        try:
            train_file_path = self.data_transformation_artifact.transformed_train_dir
            test_file_path = self.data_transformation_artifact.transformed_test_dir

            train_array = self._load_transformed_array(train_file_path, kind="train")
            test_array = self._load_transformed_array(test_file_path, kind="test")

            X_train, y_train = train_array[:, :-1], train_array[:, -1]
            X_test, y_test = test_array[:, :-1], test_array[:, -1]

            model_trainer_artifact = self.train_model(X_train, y_train, X_test, y_test)
            return model_trainer_artifact

        except Exception as e:
            raise CustomException(e, sys)