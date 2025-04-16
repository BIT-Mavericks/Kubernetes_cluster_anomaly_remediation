import logging
from kubernetes import client
from kubernetes.client.rest import ApiException
from .base import Remedy

logger = logging.getLogger(__name__)

class EnableMTLS(Remedy):
    def __init__(self, service_name, namespace="default"):
        self.service_name = service_name
        self.namespace = namespace
        self.v1 = client.CoreV1Api()
        self.custom_objects_api = client.CustomObjectsApi()

    def execute(self):
        try:
            namespaces = self.v1.list_namespace()
            istio_system_exists = any(ns.metadata.name == "istio-system" for ns in namespaces.items)
            if not istio_system_exists:
                logger.warning(f"Istio not installed; skipping mTLS for {self.service_name}")
                return
            rule_name = f"{self.service_name}-mtls"
            try:
                self.custom_objects_api.get_namespaced_custom_object(
                    group="networking.istio.io",
                    version="v1alpha3",
                    namespace=self.namespace,
                    plural="destinationrules",
                    name=rule_name
                )
                logger.info(f"DestinationRule {rule_name} already exists in {self.namespace}")
                return
            except ApiException as e:
                if e.status != 404:
                    raise
            destination_rule = {
                "apiVersion": "networking.istio.io/v1alpha3",
                "kind": "DestinationRule",
                "metadata": {
                    "name": rule_name,
                    "namespace": self.namespace
                },
                "spec": {
                    "host": f"{self.service_name}.{self.namespace}.svc.cluster.local",
                    "trafficPolicy": {
                        "tls": {
                            "mode": "MUTUAL"
                        }
                    }
                }
            }
            self.custom_objects_api.create_namespaced_custom_object(
                group="networking.istio.io",
                version="v1alpha3",
                namespace=self.namespace,
                plural="destinationrules",
                body=destination_rule
            )
            logger.info(f"Enabled mTLS for {self.service_name} in {self.namespace}")
        except Exception as e:
            logger.error(f"Failed to enable mTLS for {self.service_name}: {str(e)}")
            raise
