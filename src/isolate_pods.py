import logging
from kubernetes import client
from kubernetes.client.rest import ApiException
from .base import Remedy

logger = logging.getLogger(__name__)

class IsolatePods(Remedy):
    def __init__(self, service_name, namespace="default"):
        self.service_name = service_name
        self.namespace = namespace
        self.networking_v1 = client.NetworkingV1Api()

    def execute(self):
        try:
            policy_name = f"isolate-{self.service_name}-pods"
            try:
                self.networking_v1.read_namespaced_network_policy(
                    name=policy_name,
                    namespace=self.namespace
                )
                logger.info(f"NetworkPolicy {policy_name} already exists in {self.namespace}")
                return
            except ApiException as e:
                if e.status != 404:
                    raise
            policy = {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "NetworkPolicy",
                "metadata": {
                    "name": policy_name,
                    "namespace": self.namespace
                },
                "spec": {
                    "podSelector": {
                        "matchLabels": {
                            "app": self.service_name
                        }
                    },
                    "policyTypes": ["Ingress", "Egress"],
                    "ingress": [],
                    "egress": []
                }
            }
            self.networking_v1.create_namespaced_network_policy(
                namespace=self.namespace,
                body=policy
            )
            logger.info(f"Isolated pods for {self.service_name} in {self.namespace}")
        except Exception as e:
            logger.error(f"Failed to isolate pods for {self.service_name}: {str(e)}")
            raise
