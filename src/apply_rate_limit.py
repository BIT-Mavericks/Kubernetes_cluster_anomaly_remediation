import logging
from kubernetes import client
from kubernetes.client.rest import ApiException
from .base import Remedy

logger = logging.getLogger(__name__)

class ApplyRateLimit(Remedy):
    def __init__(self, service_name, namespace="default", rate=100):
        self.service_name = service_name
        self.namespace = namespace
        self.rate = rate
        self.networking_v1 = client.NetworkingV1Api()

    def execute(self):
        try:
            ingress = self.networking_v1.read_namespaced_ingress(
                name=self.service_name,
                namespace=self.namespace
            )
            if not ingress.metadata.annotations:
                ingress.metadata.annotations = {}
            ingress.metadata.annotations["nginx.ingress.kubernetes.io/limit-rps"] = str(self.rate)
            self.networking_v1.patch_namespaced_ingress(
                name=self.service_name,
                namespace=self.namespace,
                body=ingress
            )
            logger.info(f"Applied rate limit of {self.rate} rps to {self.service_name} in {self.namespace}")
        except ApiException as e:
            logger.error(f"Failed to apply rate limit to {self.service_name}: {str(e)}")
            raise
