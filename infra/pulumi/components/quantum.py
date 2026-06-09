from __future__ import annotations

from typing import Any

import pulumi
import pulumi_aws as aws

from ..config import Config
from ..utils import get_tag, resource_name


class QuantumBackend(pulumi.ComponentResource):
    def __init__(
        self,
        name: str,
        config: Config,
        vpc_id: str,
        subnet_ids: list[str],
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__("cfzt:infra:QuantumBackend", name, {}, opts)
        self._config = config
        self._vpc_id = vpc_id
        self._subnet_ids = subnet_ids
        self._tags = get_tag(config.project_name, config.environment, {"Component": "quantum"})

        if not config.quantum.enabled:
            self._create_stub(config)
            return

        self._create_s3_bucket(config, opts)
        self._create_iam_roles(config, opts)
        self._create_braket_config(config, opts)
        self._create_monitoring(config, opts)

    def _create_stub(self, config: Config) -> None:
        self.s3_bucket = None
        self.braket_role = None
        self.quantum_config = {"enabled": False}

    def _create_s3_bucket(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        bucket_name = config.quantum.s3_bucket or f"cfzt-{config.environment}-quantum-results"

        self.s3_bucket = aws.s3.Bucket(
            "quantum-results-bucket",
            bucket=bucket_name,
            versioning={"enabled": True},
            server_side_encryption_configuration={
                "rule": {
                    "apply_server_side_encryption_by_default": {
                        "sse_algorithm": "aws:kms",
                    },
                },
            },
            lifecycle_rules=[{
                "enabled": True,
                "id": "quantum-data-lifecycle",
                "transitions": [
                    {
                        "days": 30,
                        "storage_class": "STANDARD_IA",
                    },
                    {
                        "days": 90,
                        "storage_class": "GLACIER",
                    },
                ],
                "expiration": {
                    "days": 365,
                },
            }],
            tags=self._tags,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.s3_versioning = aws.s3.BucketVersioning(
            "quantum-bucket-versioning",
            bucket=self.s3_bucket.id,
            versioning_configuration={"status": "Enabled"},
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_iam_roles(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        role_name = resource_name(config.environment, "quantum-role")

        self.braket_role = aws.iam.Role(
            "quantum-braket-role",
            name=role_name,
            assume_role_policy="""{
                "Version": "2012-10-17",
                "Statement": [{
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "braket.amazonaws.com"
                    }
                }]
            }""",
            tags=self._tags,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.braket_policy = aws.iam.RolePolicy(
            "quantum-braket-policy",
            role=self.braket_role.id,
            policy=pulumi.Output.all(
                bucket_arn=self.s3_bucket.arn if self.s3_bucket else pulumi.Output.secret(""),
            ).apply(
                lambda args: f"""{{
                    "Version": "2012-10-17",
                    "Statement": [
                        {{
                            "Effect": "Allow",
                            "Action": [
                                "braket:*",
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:ListBucket",
                                "s3:DeleteObject",
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents"
                            ],
                            "Resource": [
                                "{args['bucket_arn']}",
                                "{args['bucket_arn']}/*",
                                "arn:aws:logs:*:*:*"
                            ]
                        }}
                    ]
                }}"""
            ),
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_braket_config(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        self.quantum_config = {
            "enabled": True,
            "provider": config.quantum.provider or "braket",
            "region": config.quantum.region or "us-east-1",
            "s3_bucket": self.s3_bucket.bucket if self.s3_bucket else "",
            "braket_role_arn": self.braket_role.arn if self.braket_role else "",
            "max_qubits": config.quantum.max_qubits or 32,
            "backend": config.quantum.backend or "amazon-braket-arn:::provider/quantum-device/simulator",
            "enable_hybrid": config.quantum.enable_hybrid,
            "shot_count": config.quantum.shot_count or 1000,
            "circuit_optimization": True,
            "error_mitigation": True,
            "noise_model": "depolarizing",
            "optimization_level": 2,
        }

    def _create_monitoring(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        self.cloudwatch_log_group = aws.logs.LogGroup(
            "quantum-logs",
            name=f"/cfzt/{config.environment}/quantum",
            retention_in_days=30,
            tags=self._tags,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.quantum_metric = aws.cloudwatch.MetricAlarm(
            "quantum-circuit-failure",
            comparison_operator="GreaterThanThreshold",
            evaluation_periods=1,
            metric_name="CircuitFailures",
            namespace="CFZT/Quantum",
            period=300,
            statistic="Sum",
            threshold=0,
            alarm_description="Quantum circuit execution failures",
            tags=self._tags,
            opts=pulumi.ResourceOptions(parent=self),
        )

    @property
    def bucket_name(self) -> pulumi.Output[str]:
        if self.s3_bucket:
            return self.s3_bucket.bucket
        return pulumi.Output.secret("")

    @property
    def role_arn(self) -> pulumi.Output[str]:
        if self.braket_role:
            return self.braket_role.arn
        return pulumi.Output.secret("")
