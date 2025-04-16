import logging
import json
import time
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from remedies import (
    ScaleDeployment, ApplyRateLimit, BlockIPPolicy, IsolatePods,
    SetResourceLimits, EnableMTLS, DefaultDenyPolicy, RestrictDNSTraffic
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RemediationAgent:
    def __init__(self, kafka_server="kafka-controller-0.kafka-headless.default.svc.cluster.local:9092"):
        self.kafka_server = kafka_server
        try:
            config.load_incluster_config()
            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            logger.info("Loaded in-cluster Kubernetes configuration")
        except Exception as e:
            logger.error(f"Failed to load Kubernetes config: {str(e)}")
            raise
        self.producer = None
        self.consumer = None
        self.initialize_kafka()

    def initialize_kafka(self):
        max_retries = 5
        for attempt in range(max_retries):
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=[self.kafka_server],
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    request_timeout_ms=60000,
                    max_block_ms=60000,
                    retries=5
                )
                self.consumer = KafkaConsumer(
                    bootstrap_servers=[self.kafka_server],
                    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                    auto_offset_reset='earliest',
                    group_id='remediation-agent',
                    request_timeout_ms=60000
                )
                logger.info(f"Connected to Kafka at {self.kafka_server}")
                return
            except KafkaError as e:
                logger.warning(f"Kafka initialization attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(5)
        logger.warning("Failed to initialize Kafka after retries. Running without Kafka.")
        self.producer = None
        self.consumer = None

    def get_deployment_for_ip(self, ip):
        try:
            pods = self.v1.list_pod_for_all_namespaces(field_selector=f"status.podIP={ip}")
            for pod in pods.items:
                for owner in pod.metadata.owner_references:
                    if owner.kind == "ReplicaSet":
                        rs = self.apps_v1.read_namespaced_replica_set(owner.name, pod.metadata.namespace)
                        for owner_ref in rs.metadata.owner_references:
                            if owner_ref.kind == "Deployment":
                                return owner_ref.name, pod.metadata.namespace
            logger.warning(f"No deployment found for IP {ip}, using default")
            return "my-app", "default"
        except Exception as e:
            logger.error(f"Error mapping IP {ip} to deployment: {str(e)}")
            return "my-app", "default"

    def get_app_label_for_ip(self, ip):
        try:
            pods = self.v1.list_pod_for_all_namespaces(field_selector=f"status.podIP={ip}")
            for pod in pods.items:
                labels = pod.metadata.labels
                if labels and "app" in labels:
                    return labels["app"]
            logger.warning(f"No app label found for IP {ip}, using default")
            return "my-app"
        except Exception as e:
            logger.error(f"Error getting app label for IP {ip}: {str(e)}")
            return "my-app"

    def log_remediation(self, issue_type, status):
        if not self.producer:
            logger.warning("Kafka producer not available, skipping log")
            return
        try:
            log_entry = {
                "issue_type": issue_type,
                "status": status,
                "timestamp": logging.Formatter().formatTime(logging.makeLogRecord({}))
            }
            self.producer.send("remediation_logs", log_entry)
            self.producer.flush()
            logger.info(f"Logged remediation for {issue_type}: {status}")
        except KafkaError as e:
            logger.error(f"Failed to log remediation for {issue_type}: {str(e)}")

    def remediate(self, prediction):
        issue_type = prediction.get("anomaly_type")
        if not issue_type:
            logger.error("No anomaly type provided in prediction")
            return
        try:
            logger.info(f"Processing remediation for issue: {issue_type}")
            if issue_type == "DDoS":
                self.handle_ddos(prediction)
            elif issue_type == "PortScan":
                self.handle_portscan(prediction)
            elif issue_type == "ICMPFlood":
                self.handle_icmpflood(prediction)
            elif issue_type == "OverlayVulnerability":
                self.handle_overlay_vulnerability(prediction)
            elif issue_type == "PolicyMisconfiguration":
                self.handle_policy_misconfiguration(prediction)
            elif issue_type == "DNSAttack":
                self.handle_dns_attack(prediction)
            elif issue_type == "LateralMovement":
                self.handle_lateral_movement(prediction)
            elif issue_type == "ResourceExhaustion":
                self.handle_resource_exhaustion(prediction)
            else:
                logger.warning(f"No remediation defined for issue type: {issue_type}")
                return
            self.log_remediation(issue_type, "success")
        except Exception as e:
            logger.error(f"Error during remediation for {issue_type}: {str(e)}")
            self.log_remediation(issue_type, f"failed: {str(e)}")

    def handle_ddos(self, prediction):
        deployment_name, namespace = self.get_deployment_for_ip(prediction.get("dst_ip", ""))
        remedies = [
            ScaleDeployment(deployment_name, namespace, 3),
            ApplyRateLimit(deployment_name + "-ingress", namespace, 100)
        ]
        for remedy in remedies:
            remedy.execute()

    def handle_portscan(self, prediction):
        src_ip = prediction.get("src_ip", "")
        app_label = self.get_app_label_for_ip(prediction.get("dst_ip", ""))
        remedy = BlockIPPolicy(src_ip, namespace="default")
        remedy.execute()

    def handle_icmpflood(self, prediction):
        deployment_name, namespace = self.get_deployment_for_ip(prediction.get("dst_ip", ""))
        remedy = ApplyRateLimit(deployment_name + "-ingress", namespace, 50)
        remedy.execute()

    def handle_overlay_vulnerability(self, prediction):
        service_name, namespace = self.get_deployment_for_ip(prediction.get("dst_ip", ""))
        remedy = EnableMTLS(service_name, namespace)
        remedy.execute()

    def handle_policy_misconfiguration(self, prediction):
        _, namespace = self.get_deployment_for_ip(prediction.get("dst_ip", ""))
        remedy = DefaultDenyPolicy(namespace)
        remedy.execute()

    def handle_dns_attack(self, prediction):
        remedy = RestrictDNSTraffic("kube-system")
        remedy.execute()

    def handle_lateral_movement(self, prediction):
        app_label = self.get_app_label_for_ip(prediction.get("dst_ip", ""))
        remedy = IsolatePods(app_label, namespace="default")
        remedy.execute()

    def handle_resource_exhaustion(self, prediction):
        deployment_name, namespace = self.get_deployment_for_ip(prediction.get("dst_ip", ""))
        remedy = SetResourceLimits(deployment_name, namespace)
        remedy.execute()

    def run_kafka(self, topic="predictions"):
        if not self.consumer:
            logger.error("Kafka consumer not available, exiting")
            return
        logger.info(f"Listening for predictions on topic {topic} at {self.kafka_server}")
        try:
            self.consumer.subscribe([topic])
            for message in self.consumer:
                prediction = message.value
                logger.info(f"Received prediction: {prediction}")
                self.remediate(prediction)
        except KafkaError as e:
            logger.error(f"Kafka consumer error: {str(e)}")
            self.initialize_kafka()

    def run_simulation(self):
        predictions = [
            {"anomaly_type": "DDoS", "dst_ip": "10.0.0.1"},
            {"anomaly_type": "PortScan", "src_ip": "192.168.1.100", "dst_ip": "10.0.0.1"},
            {"anomaly_type": "ICMPFlood", "dst_ip": "10.0.0.1"},
            {"anomaly_type": "OverlayVulnerability", "dst_ip": "10.0.0.1"},
            {"anomaly_type": "PolicyMisconfiguration", "dst_ip": "10.0.0.1"},
            {"anomaly_type": "DNSAttack", "dst_ip": "10.0.0.1"},
            {"anomaly_type": "LateralMovement", "dst_ip": "10.0.0.1"},
            {"anomaly_type": "ResourceExhaustion", "dst_ip": "10.0.0.1"}
        ]
        for prediction in predictions:
            logger.info(f"Simulating remediation for {prediction['anomaly_type']}")
            self.remediate(prediction)

if __name__ == "__main__":
    agent = RemediationAgent()
    agent.run_kafka(topic="predictions")
