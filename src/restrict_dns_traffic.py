import logging
from kubernetes import client
from kubernetes.client.rest import ApiException
from .base import Remedy

logger = logging.getLogger(__name__)

class RestrictDNSTraffic(Remedy):
    def __init__(self, namespace="kube-system"):
        self.namespace = namespace
        self.networking_v1 = client.NetworkingV1Api()

    def execute(self):
        try:
            try:
                self.networking_v1.read_namespaced_network_policy(
                    name="restrict-dns",
                    namespace=self.namespace
                )
                logger.info(f"NetworkPolicy restrict-dns already exists in {self.namespace}")
                return
            except ApiException as e:
                if e.status != 404:
                    raise
            policy = {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "NetworkPolicy",
                "metadata": {
                    "name": "restrict-dns",
                    "namespace": self.namespace
                },
                "spec": {
                    "podSelector": {
                        "matchLabels": {
                            "k8s-app": "kube-dns"
                        }
                    },
                    "policyTypes": ["Egress"],
                    "egress": [{
                        "to": [{
                            "ipBlock": {
                                "cidr": "0.0.0.0/0",
                                "except": []
                            }
                        }],
                        "ports": [{
                            "protocol": "UDP",
                            "port": 53
                        }]
                    }]
                }
            }
            self.networking_v1.create_namespaced_network_policy(
                namespace=self.namespace,
                body=policy
            )
            logger.info(f"Restricted DNS traffic in {self.namespace}")
        except Exception as e:
            logger.error(f"Failed to restrict DNS traffic: {str(e)}")
            raise
