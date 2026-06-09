from __future__ import annotations

import json
from typing import Any

import numpy as np

try:
    import shap
except ImportError:
    shap = None

try:
    import lime
    from lime.lime_tabular import LimeTabularExplainer
except ImportError:
    lime = None
    LimeTabularExplainer = None


class SHAPExplainer:
    def __init__(
        self,
        model: Any,
        background_data: np.ndarray | None = None,
        feature_names: list[str] | None = None,
    ):
        self.model = model
        self.background_data = background_data
        self.feature_names = feature_names or []
        self.explainer = None

    def initialize(self) -> None:
        if shap is None:
            raise ImportError("SHAP is required for SHAPExplainer")

        if hasattr(self.model, "predict_proba"):
            self.explainer = shap.KernelExplainer(
                self.model.predict_proba,
                self.background_data,
            )
        elif hasattr(self.model, "predict"):
            self.explainer = shap.KernelExplainer(
                self.model.predict,
                self.background_data,
            )
        else:
            raise ValueError("Model must have predict or predict_proba method")

    def explain(
        self,
        instance: np.ndarray,
        num_features: int = 10,
    ) -> dict[str, Any]:
        if self.explainer is None:
            self.initialize()

        shap_values = self.explainer.shap_values(instance)

        if isinstance(shap_values, list):
            shap_values = shap_values[0]

        feature_importance = {}
        if self.feature_names and len(self.feature_names) == len(shap_values[0]):
            for i, name in enumerate(self.feature_names):
                feature_importance[name] = float(shap_values[0][i])
        else:
            for i, value in enumerate(shap_values[0]):
                feature_importance[f"feature_{i}"] = float(value)

        sorted_importance = dict(
            sorted(feature_importance.items(), key=lambda x: abs(x[1]), reverse=True)[:num_features]
        )

        return {
            "shap_values": shap_values.tolist(),
            "feature_importance": sorted_importance,
            "base_value": float(self.explainer.expected_value[0]) if isinstance(self.explainer.expected_value, list) else float(self.explainer.expected_value),
            "num_features": num_features,
        }

    def explain_batch(
        self,
        instances: np.ndarray,
        num_features: int = 10,
    ) -> list[dict[str, Any]]:
        results = []
        for i in range(len(instances)):
            results.append(self.explain(instances[i:i + 1], num_features))
        return results

    def get_feature_importance_summary(
        self,
        instances: np.ndarray,
    ) -> dict[str, float]:
        all_importance = {}

        for i in range(len(instances)):
            result = self.explain(instances[i:i + 1])
            for feature, importance in result["feature_importance"].items():
                if feature not in all_importance:
                    all_importance[feature] = []
                all_importance[feature].append(importance)

        return {
            feature: float(np.mean(importances))
            for feature, importances in all_importance.items()
        }


class LIMEExplainer:
    def __init__(
        self,
        model: Any,
        training_data: np.ndarray,
        feature_names: list[str] | None = None,
        class_names: list[str] | None = None,
        mode: str = "classification",
    ):
        self.model = model
        self.training_data = training_data
        self.feature_names = feature_names or []
        self.class_names = class_names or []
        self.mode = mode
        self.explainer = None

    def initialize(self) -> None:
        if LimeTabularExplainer is None:
            raise ImportError("LIME is required for LIMEExplainer")

        self.explainer = LimeTabularExplainer(
            training_data=self.training_data,
            feature_names=self.feature_names,
            class_names=self.class_names,
            mode=self.mode,
            discretize_continuous=True,
        )

    def explain(
        self,
        instance: np.ndarray,
        num_features: int = 10,
        num_samples: int = 5000,
    ) -> dict[str, Any]:
        if self.explainer is None:
            self.initialize()

        prediction = self.model.predict(instance.reshape(1, -1))[0]

        def predict_fn(x):
            return self.model.predict_proba(x) if hasattr(self.model, "predict_proba") else self.model.predict(x)

        explanation = self.explainer.explain_instance(
            instance.flatten(),
            predict_fn,
            num_features=num_features,
            num_samples=num_samples,
        )

        feature_importance = {}
        for feature_idx, importance in explanation.as_list():
            if self.feature_names and feature_idx < len(self.feature_names):
                feature_name = self.feature_names[feature_idx]
            else:
                feature_name = f"feature_{feature_idx}"
            feature_importance[feature_name] = float(importance)

        return {
            "prediction": int(prediction) if self.mode == "classification" else float(prediction),
            "feature_importance": feature_importance,
            "intercept": float(explanation.intercept[0]) if hasattr(explanation, 'intercept') and explanation.intercept else 0.0,
            "local_pred": float(explanation.local_pred[0]) if hasattr(explanation, 'local_pred') and explanation.local_pred else 0.0,
            "score": float(explanation.score) if hasattr(explanation, 'score') else 0.0,
            "num_features": num_features,
        }

    def explain_batch(
        self,
        instances: np.ndarray,
        num_features: int = 10,
    ) -> list[dict[str, Any]]:
        results = []
        for i in range(len(instances)):
            results.append(self.explain(instances[i], num_features))
        return results

    def get_feature_importance_summary(
        self,
        instances: np.ndarray,
    ) -> dict[str, float]:
        all_importance = {}

        for i in range(len(instances)):
            result = self.explain(instances[i])
            for feature, importance in result["feature_importance"].items():
                if feature not in all_importance:
                    all_importance[feature] = []
                all_importance[feature].append(importance)

        return {
            feature: float(np.mean(importances))
            for feature, importances in all_importance.items()
        }


def create_shap_explainer(
    model: Any,
    background_data: np.ndarray | None = None,
    feature_names: list[str] | None = None,
) -> SHAPExplainer:
    explainer = SHAPExplainer(model, background_data, feature_names)
    explainer.initialize()
    return explainer


def create_lime_explainer(
    model: Any,
    training_data: np.ndarray,
    feature_names: list[str] | None = None,
    class_names: list[str] | None = None,
    mode: str = "classification",
) -> LIMEExplainer:
    explainer = LIMEExplainer(model, training_data, feature_names, class_names, mode)
    explainer.initialize()
    return explainer


def explain_prediction(
    model: Any,
    instance: np.ndarray,
    background_data: np.ndarray | None = None,
    training_data: np.ndarray | None = None,
    feature_names: list[str] | None = None,
    method: str = "shap",
) -> dict[str, Any]:
    if method == "shap":
        explainer = create_shap_explainer(model, background_data, feature_names)
        return explainer.explain(instance)
    elif method == "lime":
        if training_data is None:
            raise ValueError("Training data is required for LIME")
        explainer = create_lime_explainer(model, training_data, feature_names)
        return explainer.explain(instance)
    else:
        raise ValueError(f"Unknown explanation method: {method}")
