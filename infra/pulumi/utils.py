from __future__ import annotations

import hashlib
import json
from typing import Any

import pulumi


def get_tag(name: str, environment: str, additional: dict[str, str] | None = None) -> dict[str, str]:
    tags = {
        "Project": name,
        "Environment": environment,
        "ManagedBy": "pulumi",
        "Infrastructure": "continuous-face-zero-trust",
    }
    if additional:
        tags.update(additional)
    return tags


def merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def resource_name(environment: str, name: str, separator: str = "-") -> str:
    return separator.join(["cfzt", environment, name])


def hash_config(config: dict[str, Any]) -> str:
    config_str = json.dumps(config, sort_keys=True)
    return hashlib.sha256(config_str.encode()).hexdigest()[:12]


def validate_cidr(cidr: str) -> bool:
    parts = cidr.split("/")
    if len(parts) != 2:
        return False
    octets = parts[0].split(".")
    if len(octets) != 4:
        return False
    try:
        for octet in octets:
            val = int(octet)
            if val < 0 or val > 255:
                return False
        prefix = int(parts[1])
        if prefix < 0 or prefix > 32:
            return False
        return True
    except ValueError:
        return False


def output_to_dict(outputs: dict[str, pulumi.Output[Any]]) -> dict[str, Any]:
    result = {}
    for key, value in outputs.items():
        result[key] = value
    return result


def apply_tags(
    resource_tags: dict[str, str],
    global_tags: dict[str, str],
) -> dict[str, str]:
    merged = global_tags.copy()
    merged.update(resource_tags)
    return merged


def create_security_group_rules(
    ingress_rules: list[dict[str, Any]],
    egress_rules: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "ingress": ingress_rules,
        "egress": egress_rules,
    }


def get_provider_config(cloud: str, region: str) -> dict[str, Any]:
    configs = {
        "aws": {
            "region": region,
            "default_tags": {"tags": {"ManagedBy": "pulumi"}},
        },
        "gcp": {
            "project": "cfzt-project",
            "zone": f"{region}-a",
        },
        "azure": {
            "location": region,
            "resource_group_name": "cfzt-rg",
        },
    }
    return configs.get(cloud, {})


def format_endpoint(host: str, port: int, protocol: str = "https") -> str:
    if port == 443 and protocol == "https":
        return f"{protocol}://{host}"
    if port == 80 and protocol == "http":
        return f"{protocol}://{host}"
    return f"{protocol}://{host}:{port}"


def sanitize_name(name: str) -> str:
    return name.lower().replace("_", "-").replace(" ", "-")
