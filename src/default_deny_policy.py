import logging
from kubernetes import client
from kubernetes.client.rest import ApiException
from .base import Remedy

logger = logging.getLogger(__name__)

class DefaultDenyPolicy(Remedy):
    def __init__(self, namespace="default"):
        self.namespace = namespace
        self.networking_v1 = client.NetworkingV1Api()

    def execute(self):
        try:
            try:
                self.networking_v1.read_namespaced_network_policy(
                    name="default-deny",
                    namespace=self.namespace
                )
                logger.info(f"NetworkPolicy default-deny already exists in {self.namespace}")
                return
            except ApiException as e:
                if e.status != 404:
                    raise
            policy = {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "NetworkPolicy",
                "metadata": {
                    "name": "default-deny",
                    "namespace": self.namespace
                },
                "spec": {
                    "podSelector": {},
                    "policyTypes": ["Ingress", "Egress"]
                }
            }
            self.networking_v1.create_namespaced_network_policy(
                namespace=self.namespace,
                body=policy
            )
            logger.info(f"Created default-deny NetworkPolicy in {self.namespace}")
        except Exception as e:
            logger.error(f"Failed to create default-deny NetworkPolicy: {str(e)}")
            raise
