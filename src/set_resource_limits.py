import logging
from kubernetes import client
from .base import Remedy

logger = logging.getLogger(__name__)

class SetResourceLimits(Remedy):
    def __init__(self, service_name, namespace="default"):
        self.service_name = service_name
        self.namespace = namespace
        self.apps_v1 = client.AppsV1Api()

    def execute(self):
        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name=self.service_name,
                namespace=self.namespace
            )
            container = deployment.spec.template.spec.containers[0]
            if not container.resources:
                container.resources = client.V1ResourceRequirements()
            container.resources.limits = {
                "cpu": "500m",
                "memory": "512Mi"
            }
            container.resources.requests = {
                "cpu": "200m",
                "memory": "256Mi"
            }
            self.apps_v1.patch_namespaced_deployment(
                name=self.service_name,
                namespace=self.namespace,
                body=deployment
            )
            logger.info(f"Set resource limits on {self.service_name} in {self.namespace}: CPU=500m, Memory=512Mi")
        except Exception as e:
            logger.error(f"Failed to set resource limits on {self.service_name}: {str(e)}")
            raise
