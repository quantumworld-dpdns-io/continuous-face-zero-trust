from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from prometheus_client import Counter, Gauge, Histogram


DATASET_VERSION_COUNTER = Counter(
    "dataset_version_total",
    "Total number of dataset versions",
    labelnames=["dataset_name", "status"],
)

DATASET_VERSION_SIZE = Gauge(
    "dataset_version_size",
    "Size of dataset version",
    labelnames=["dataset_name", "version"],
)

DATASET_VERSION_HASH = Gauge(
    "dataset_version_hash",
    "Hash of dataset version",
    labelnames=["dataset_name", "version"],
)

DATASET_VERSION_CHECKS = Counter(
    "dataset_version_checks_total",
    "Total number of dataset version checks",
    labelnames=["dataset_name", "status"],
)

DATASET_VERSION_LATENCY = Histogram(
    "dataset_version_latency_seconds",
    "Latency of dataset version operations",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    labelnames=["dataset_name"],
)


class DatasetVersionManager:
    def __init__(self):
        self.datasets: dict[str, dict[str, Any]] = {}
        self.versions: dict[str, dict[str, dict[str, Any]]] = {}

    def create_dataset(
        self,
        name: str,
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        if name not in self.datasets:
            self.datasets[name] = {
                "name": name,
                "description": description,
                "created_at": time.time(),
                "updated_at": time.time(),
                "latest_version": None,
            }
            self.versions[name] = {}

        return name

    def create_version(
        self,
        dataset_name: str,
        data: list[dict[str, Any]],
        description: str = "",
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> str:
        if dataset_name not in self.datasets:
            self.create_dataset(dataset_name)

        data_hash = self._calculate_hash(data)
        version_number = len(self.versions[dataset_name]) + 1
        version_id = f"v{version_number}"

        self.versions[dataset_name][version_id] = {
            "id": version_id,
            "dataset_name": dataset_name,
            "version_number": version_number,
            "description": description,
            "metadata": metadata or {},
            "tags": tags or [],
            "data_hash": data_hash,
            "size": len(data),
            "created_at": time.time(),
            "data": data,
        }

        self.datasets[dataset_name]["latest_version"] = version_id
        self.datasets[dataset_name]["updated_at"] = time.time()

        DATASET_VERSION_COUNTER.labels(
            dataset_name=dataset_name,
            status="created",
        ).inc()

        DATASET_VERSION_SIZE.labels(
            dataset_name=dataset_name,
            version=version_id,
        ).set(len(data))

        DATASET_VERSION_HASH.labels(
            dataset_name=dataset_name,
            version=version_id,
        ).set(hash(data_hash) % (2 ** 31))

        return version_id

    def get_version(
        self,
        dataset_name: str,
        version_id: str,
    ) -> dict[str, Any] | None:
        if dataset_name not in self.versions:
            return None
        return self.versions[dataset_name].get(version_id)

    def get_latest_version(
        self,
        dataset_name: str,
    ) -> dict[str, Any] | None:
        if dataset_name not in self.datasets:
            return None

        latest_version_id = self.datasets[dataset_name]["latest_version"]
        if not latest_version_id:
            return None

        return self.get_version(dataset_name, latest_version_id)

    def list_versions(
        self,
        dataset_name: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if dataset_name not in self.versions:
            return []

        versions = list(self.versions[dataset_name].values())
        versions.sort(key=lambda x: x["version_number"], reverse=True)

        return [
            {
                "id": v["id"],
                "version_number": v["version_number"],
                "description": v["description"],
                "data_hash": v["data_hash"],
                "size": v["size"],
                "created_at": v["created_at"],
                "tags": v["tags"],
            }
            for v in versions[:limit]
        ]

    def compare_versions(
        self,
        dataset_name: str,
        version_a: str,
        version_b: str,
    ) -> dict[str, Any]:
        v_a = self.get_version(dataset_name, version_a)
        v_b = self.get_version(dataset_name, version_b)

        if not v_a or not v_b:
            return {"error": "Version not found"}

        hash_match = v_a["data_hash"] == v_b["data_hash"]
        size_diff = v_b["size"] - v_a["size"]

        return {
            "dataset_name": dataset_name,
            "version_a": version_a,
            "version_b": version_b,
            "hash_match": hash_match,
            "size_a": v_a["size"],
            "size_b": v_b["size"],
            "size_diff": size_diff,
            "data_hash_a": v_a["data_hash"],
            "data_hash_b": v_b["data_hash"],
        }

    def verify_integrity(
        self,
        dataset_name: str,
        version_id: str,
        data: list[dict[str, Any]],
    ) -> bool:
        start_time = time.time()

        version = self.get_version(dataset_name, version_id)
        if not version:
            DATASET_VERSION_CHECKS.labels(
                dataset_name=dataset_name,
                status="error",
            ).inc()
            return False

        current_hash = self._calculate_hash(data)
        is_valid = current_hash == version["data_hash"]

        status = "valid" if is_valid else "invalid"
        DATASET_VERSION_CHECKS.labels(
            dataset_name=dataset_name,
            status=status,
        ).inc()

        duration = time.time() - start_time
        DATASET_VERSION_LATENCY.labels(dataset_name=dataset_name).observe(duration)

        return is_valid

    def _calculate_hash(self, data: list[dict[str, Any]]) -> str:
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def get_dataset_info(
        self,
        dataset_name: str,
    ) -> dict[str, Any] | None:
        if dataset_name not in self.datasets:
            return None

        dataset = self.datasets[dataset_name]
        versions = self.list_versions(dataset_name)

        return {
            "name": dataset["name"],
            "description": dataset["description"],
            "created_at": dataset["created_at"],
            "updated_at": dataset["updated_at"],
            "latest_version": dataset["latest_version"],
            "total_versions": len(versions),
            "versions": versions,
        }

    def delete_version(
        self,
        dataset_name: str,
        version_id: str,
    ) -> bool:
        if dataset_name not in self.versions:
            return False

        if version_id not in self.versions[dataset_name]:
            return False

        del self.versions[dataset_name][version_id]

        if self.datasets[dataset_name]["latest_version"] == version_id:
            remaining_versions = list(self.versions[dataset_name].keys())
            self.datasets[dataset_name]["latest_version"] = (
                remaining_versions[-1] if remaining_versions else None
            )

        DATASET_VERSION_COUNTER.labels(
            dataset_name=dataset_name,
            status="deleted",
        ).inc()

        return True

    def export_version(
        self,
        dataset_name: str,
        version_id: str,
    ) -> str:
        version = self.get_version(dataset_name, version_id)
        if not version:
            raise ValueError(f"Version {version_id} not found in dataset {dataset_name}")

        export_data = {
            "dataset_name": version["dataset_name"],
            "version_id": version["id"],
            "version_number": version["version_number"],
            "description": version["description"],
            "metadata": version["metadata"],
            "tags": version["tags"],
            "data_hash": version["data_hash"],
            "size": version["size"],
            "created_at": version["created_at"],
            "data": version["data"],
        }

        return json.dumps(export_data, indent=2, default=str)
