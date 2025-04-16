import logging
from kubernetes import client
from kubernetes.client.rest import ApiException
from .base import Remedy

logger = logging.getLogger(__name__)

class BlockIPPolicy(Remedy):
    def __init__(self, ip, namespace="default"):
        self.ip = ip
        self.namespace = namespace
        self.networking_v1 = client.NetworkingV1Api()

    def execute(self):
        try:
            policy_name = f"block-ip-policy" if not self.ip else f"block-{self.ip.replace('.', '-')}-policy"
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
            if not self.ip:
                logger.warning("No IP provided, skipping policy creation")
                return
            policy = {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "NetworkPolicy",
                "metadata": {
                    "name": policy_name,
                    "namespace": self.namespace
                },
                "spec": {
                    "podSelector": {},
                    "policyTypes": ["Ingress"],
                    "ingress": [{
                        "from": [{
                            "ipBlock": {
                                "cidr": f"{self.ip}/32"
                            }
                        }]
                    }]
                }
            }
            self.networking_v1.create_namespaced_network_policy(
                namespace=self.namespace,
                body=policy
            )
            logger.info(f"Created NetworkPolicy to block IP {self.ip} in {self.namespace}")
        except Exception as e:
            logger.error(f"Failed to block IP {self.ip}: {str(e)}")
            raise
