from __future__ import annotations

from typing import Any

import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes import helm, v3

from ..config import Config
from ..utils import get_tag, resource_name


class KubernetesCluster(pulumi.ComponentResource):
    def __init__(
        self,
        name: str,
        config: Config,
        vpc_id: str,
        subnet_ids: list[str],
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__("cfzt:infra:KubernetesCluster", name, {}, opts)
        self._config = config
        self._vpc_id = vpc_id
        self._subnet_ids = subnet_ids
        self._tags = get_tag(config.project_name, config.environment, {"Component": "kubernetes"})

        self._create_cluster(name, config, opts)

    def _create_cluster(self, name: str, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        provider = config.cloud.provider
        if provider == "aws":
            self._create_eks_cluster(name, config, opts)
        elif provider == "gcp":
            self._create_gke_cluster(name, config, opts)
        elif provider == "azure":
            self._create_aks_cluster(name, config, opts)
        else:
            raise ValueError(f"Unsupported cloud provider: {provider}")

    def _create_eks_cluster(self, name: str, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        cluster_name = resource_name(config.environment, "k8s")
        k8s_version = config.kubernetes.version

        self.cluster_role = aws.iam.Role(
            f"{cluster_name}-cluster-role",
            assume_role_policy="""{
                "Version": "2012-10-17",
                "Statement": [{
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {"Service": "eks.amazonaws.com"}
                }]
            }""",
            tags=self._tags,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.cluster_policy_attachment = aws.iam.RolePolicyAttachment(
            f"{cluster_name}-cluster-policy",
            role=self.cluster_role.name,
            policy_arn="arn:aws:iam::policy/AmazonEKSClusterPolicy",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.cluster_security_group = aws.ec2.SecurityGroup(
            f"{cluster_name}-sg",
            description="EKS cluster security group",
            vpc_id=self._vpc_id,
            ingress=[],
            egress=[{
                "from_port": 0,
                "to_port": 0,
                "protocol": "-1",
                "cidr_blocks": ["0.0.0.0/0"],
            }],
            tags=self._tags,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.cluster = aws.eks.Cluster(
            f"{cluster_name}",
            version=k8s_version,
            role_arn=self.cluster_role.arn,
            vpc_config={
                "subnet_ids": self._subnet_ids,
                "security_group_ids": [self.cluster_security_group.id],
                "endpoint_private_access": True,
                "endpoint_public_access": True,
            },
            enabled_cluster_log_types=["api", "audit", "authenticator", "controllerManager", "scheduler"],
            tags=self._tags,
            opts=pulumi.ResourceOptions(parent=self, depends_on=[self.cluster_policy_attachment]),
        )

        node_role = aws.iam.Role(
            f"{cluster_name}-node-role",
            assume_role_policy="""{
                "Version": "2012-10-17",
                "Statement": [{
                    "Action": "sts:AssumeRole",
                    "Effect": "Allow",
                    "Principal": {"Service": "ec2.amazonaws.com"}
                }]
            }""",
            tags=self._tags,
            opts=pulumi.ResourceOptions(parent=self),
        )

        for policy_arn in [
            "arn:aws:iam::policy/AmazonEKSWorkerNodePolicy",
            "arn:aws:iam::policy/AmazonEKS_CNI_Policy",
            "arn:aws:iam::policy/AmazonEC2ContainerRegistryReadOnly",
        ]:
            aws.iam.RolePolicyAttachment(
                f"{cluster_name}-node-{policy_arn.split('/')[-1]}",
                role=node_role.name,
                policy_arn=policy_arn,
                opts=pulumi.ResourceOptions(parent=self),
            )

        self.node_group = aws.eks.NodeGroup(
            f"{cluster_name}-node-group",
            cluster_name=self.cluster.name,
            node_role_arn=node_role.arn,
            subnet_ids=self._subnet_ids,
            instance_types=[config.kubernetes.node_type or "t3.large"],
            scaling_config={
                "desired_size": config.kubernetes.node_count or 3,
                "min_size": config.kubernetes.min_nodes or 2,
                "max_size": config.kubernetes.max_nodes or 10,
            },
            update_config={
                "max_unavailable": 1,
            },
            labels={
                "role": "worker",
                "environment": config.environment,
            },
            tags=self._tags,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.k8s_provider = k8s.Provider(
            f"{cluster_name}-provider",
            kubeconfig=self.cluster.kubeconfig_json,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self._install_metrics_server(config, opts)

    def _create_gke_cluster(self, name: str, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        cluster_name = resource_name(config.environment, "k8s")
        k8s_version = config.kubernetes.version

        network = gcp.compute.Network(
            f"{cluster_name}-network",
            auto_create_subnetworks=False,
            opts=pulumi.ResourceOptions(parent=self),
        )

        subnet = gcp.compute.Subnetwork(
            f"{cluster_name}-subnet",
            ip_cidr_range="10.0.0.0/24",
            region=config.cloud.region,
            network=network.id,
            secondary_ip_range=[
                {"range_name": "pods", "ip_cidr_range": config.kubernetes.pod_cidr or "10.244.0.0/16"},
                {"range_name": "services", "ip_cidr_range": config.kubernetes.service_cidr or "10.96.0.0/16"},
            ],
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.cluster = gcp.container.Cluster(
            f"{cluster_name}",
            initial_node_count=1,
            min_master_version=k8s_version,
            network=network.name,
            subnetwork=subnet.name,
            location=config.cloud.region or "us-west2-a",
            release_channel={"channel": "REGULAR"},
            logging_config={"enable_components": ["SYSTEM_COMPONENTS", "WORKLOADS"]},
            monitoring_config={"enable_components": ["SYSTEM_COMPONENTS"]},
            remove_default_node_pool=True,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.node_pool = gcp.container.NodePool(
            f"{cluster_name}-pool",
            cluster=self.cluster.name,
            location=config.cloud.region or "us-west2-a",
            initial_node_count=config.kubernetes.node_count or 3,
            autoscaling={
                "min_node_count": config.kubernetes.min_nodes or 2,
                "max_node_count": config.kubernetes.max_nodes or 10,
            },
            node_config={
                "machine_type": config.kubernetes.node_type or "e2-standard-4",
                "oauth_scopes": [
                    "https://www.googleapis.com/auth/cloud-platform",
                ],
                "labels": {
                    "role": "worker",
                    "environment": config.environment,
                },
            },
            management={
                "auto_repair": True,
                "auto_upgrade": True,
            },
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.k8s_provider = k8s.Provider(
            f"{cluster_name}-provider",
            kubeconfig=self._get_gke_kubeconfig(self.cluster, config),
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _create_aks_cluster(self, name: str, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        cluster_name = resource_name(config.environment, "k8s")
        k8s_version = config.kubernetes.version

        resource_group = azure.core.ResourceGroup(
            f"{cluster_name}-rg",
            location=config.cloud.region or "West US 2",
            tags=self._tags,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.resource_group = resource_group

        self.cluster = azure.containerservice.ManagedCluster(
            f"{cluster_name}",
            resource_group_name=resource_group.name,
            kubernetes_version=k8s_version,
            dns_prefix=cluster_name,
            network_profile={
                "network_plugin": "azure",
                "network_policy": "calico",
                "load_balancer_sku": "standard",
            },
            agent_pool_profiles=[{
                "name": "default",
                "count": config.kubernetes.node_count or 3,
                "vm_size": config.kubernetes.node_type or "Standard_D2s_v3",
                "os_type": "Linux",
                "mode": "System",
                "auto_scaling_enabled": True,
                "min_count": config.kubernetes.min_nodes or 2,
                "max_count": config.kubernetes.max_nodes or 10,
            }],
            identity={"type": "SystemAssigned"},
            enable_rbac=True,
            tags=self._tags,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.k8s_provider = k8s.Provider(
            f"{cluster_name}-provider",
            kubeconfig=self._get_aks_kubeconfig(self.cluster),
            opts=pulumi.ResourceOptions(parent=self),
        )

    def _get_gke_kubeconfig(self, cluster, config: Config) -> pulumi.Output:
        import base64

        return pulumi.Output.all(
            endpoint=cluster.endpoint,
            cluster_ca_certificate=cluster.master_auth[0].cluster_ca_certificate,
            token=data.gcp.client_config().token,
        ).apply(
            lambda args: f"""apiVersion: v1
kind: Config
clusters:
- cluster:
    certificate-authority-data: {base64.b64encode(args["cluster_ca_certificate"].encode()).decode()}
    server: https://{args["endpoint"]}
  name: gke-cluster
contexts:
- context:
    cluster: gke-cluster
    user: gcp-user
  name: gke-context
current-context: gke-context
users:
- name: gcp-user
  user:
    auth-provider:
      name: gcp
"""
        )

    def _get_aks_kubeconfig(self, cluster) -> pulumi.Output:
        return cluster.kube_config_raw

    def _install_metrics_server(self, config: Config, opts: pulumi.ResourceOptions | None) -> None:
        self.metrics_server = helm.v3.Release(
            "metrics-server",
            chart="metrics-server",
            version="3.11.0",
            namespace="kube-system",
            repository_opts={
                "repo": "https://kubernetes-sigs.github.io/metrics-server/",
            },
            set=[{
                "name": "args[0]",
                "value": "--kubelet-insecure-tls",
            }],
            opts=pulumi.ResourceOptions(
                parent=self,
                provider=self.k8s_provider,
            ) if hasattr(self, 'k8s_provider') else opts,
        )

    @property
    def cluster_name(self) -> pulumi.Output[str]:
        return self.cluster.name

    @property
    def cluster_endpoint(self) -> pulumi.Output[str]:
        return self.cluster.endpoint

    @property
    def cluster_ca_certificate(self) -> pulumi.Output[str]:
        return self.cluster.certificate_authority.data

    @property
    def provider(self) -> k8s.Provider:
        return self.k8s_provider
