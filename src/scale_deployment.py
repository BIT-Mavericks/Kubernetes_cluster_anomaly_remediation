import logging
from kubernetes import client
from .base import Remedy

logger = logging.getLogger(__name__)

class ScaleDeployment(Remedy):
    def __init__(self, service_name, namespace="default", replicas=3):
        self.service_name = service_name
        self.namespace = namespace
        self.replicas = replicas
        self.apps_v1 = client.AppsV1Api()

    def execute(self):
        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name=self.service_name,
                namespace=self.namespace
            )
            deployment.spec.replicas = self.replicas
            self.apps_v1.patch_namespaced_deployment(
                name=self.service_name,
                namespace=self.namespace,
                body=deployment
            )
            logger.info(f"Scaled deployment {self.service_name} in {self.namespace} to {self.replicas} replicas")
        except Exception as e:
            logger.error(f"Failed to scale deployment {self.service_name}: {str(e)}")
            raise
