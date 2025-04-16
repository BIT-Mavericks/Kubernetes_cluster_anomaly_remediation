# Kubernetes Remediation Phase II

## Overview

Welcome to the Kubernetes Remediation Phase II project! This innovative solution, developed for the Guidewire Solutions University Hackathon, leverages AI to detect and automatically remediate anomalies in Kubernetes clusters. Built with a focus on scalability and efficiency, the system integrates real-time data processing, intelligent anomaly detection, and automated remediation actions to enhance cluster reliability and security. This README provides a comprehensive guide to understanding, setting up, and using the project.

### Project Purpose

The project addresses the challenges of managing Kubernetes clusters at scale, where issues like DDoS attacks, resource exhaustion, and policy misconfigurations can lead to downtime or breaches. By combining tools like LangChain, n8n, Apache Kafka, Prometheus, Grafana, IPTables-Netflow, and Kubernetes, it offers a state-of-the-art, automated remediation system that minimizes human intervention and reduces mean time to resolution (MTTR).

---

## Key Features

- **AI-Driven Anomaly Detection**: Uses LangChain for log analysis and n8n for metric processing to detect issues like DDoS attacks and resource bottlenecks.
- **Real-Time Data Streaming**: Apache Kafka streams anomaly predictions and remediation logs for low-latency communication.
- **Comprehensive Monitoring**: Prometheus, Grafana, and IPTables-Netflow collect metrics and network data for analysis.
- **Automated Remediation**: A Python-based agent scales deployments, blocks IPs, and adjusts resources based on detected anomalies.
- **Kubernetes-Native**: Deployed and managed entirely within a Minikube cluster.

---

## Prerequisites

Before setting up the project, ensure your environment meets the following requirements:

- **Operating System**: Linux, macOS, or Windows (with WSL2 recommended for Windows).
- **Memory**: At least 8GB RAM (7GB allocated to WSL2/Minikube).
- **CPU**: 6 or more cores.
- **Software**:
  - [Docker](https://docs.docker.com/get-docker/)
  - [Minikube](https://minikube.sigs.k8s.io/docs/start/)
  - [kubectl](https://kubernetes.io/docs/tasks/tools/)
  - [Helm](https://helm.sh/docs/intro/install/)
  - Python 3.9+ with `pip`
  - [Kafka Python](https://kafka-python.readthedocs.io/en/master/) and [Kubernetes Python Client](https://github.com/kubernetes-client/python)

---

## Setup Instructions

Follow these steps to set up and run the project on your local machine. Each step describes the actions needed without providing specific commands, allowing you to adapt based on your environment.

### Step 1: Prepare Your Environment

1. **Disable Swap Memory**  
   Ensure swap memory is disabled, as Kubernetes requires this for proper operation. Modify the system configuration to prevent swap from being enabled on reboot and confirm that swap usage is zero.

2. **Configure WSL2 (Windows Users)**  
   If using Windows with WSL2, adjust the resource allocation settings to provide sufficient memory and CPU cores for Minikube. Enable systemd support and local host forwarding, then restart the WSL2 environment to apply these changes.

3. **Configure Docker**  
   Set up Docker with a configuration that aligns with Kubernetes requirements, specifically using the systemd cgroup driver. Define logging and storage options to optimize performance, reload the Docker daemon, and restart the service to apply the changes. Verify that the cgroup driver is correctly set.

### Step 2: Start Minikube

Initiate a Minikube cluster, allocating adequate memory and CPU resources to support the deployment of Kubernetes applications. After starting the cluster, confirm that it is operational by checking the status of the Minikube host, kubelet, and API server, as well as verifying connectivity to the Kubernetes API.

### Step 3: Install Kafka for Event Handling

1. **Add Helm Repository**  
   Register the Bitnami Helm repository to access Kafka charts, and update the repository list to ensure the latest versions are available.

2. **Install Kafka**  
   Deploy a Kafka instance using Helm, configuring it with plaintext authentication for simplicity. Set a custom connection timeout to prevent issues and limit the number of replicas to conserve resources. Wait for the Kafka pod to become ready before proceeding.

3. **Create Kafka Topics**  
   Establish two Kafka topics: one for anomaly predictions and another for remediation logs. Configure these topics with a single partition and replication factor to keep the setup straightforward.

4. **Verify Topics**  
   Check that the created topics are listed and accessible within the Kafka cluster to ensure proper setup.

### Step 4: Deploy the Remediation Agent

1. **Create Agent Directory and Code**  
   Set up a directory for the remediation agent and place the Python script containing the agent’s logic, which handles anomaly detection and remediation actions.

2. **Create the Dockerfile**  
   Define a Dockerfile that specifies the base Python image, sets the working directory, copies the agent script, installs necessary Python dependencies, and defines the command to run the script.

3. **Build and Deploy the Agent**  
   Build a Docker image for the agent using the local Docker environment configured for Minikube. Apply a Kubernetes configuration file to deploy the agent, including a service account, RBAC permissions, and a deployment specification. Wait for the pod to be ready.

### Step 5: Deploy a Test Application

1. **Deploy the Nginx App**  
   Set up a test application using a deployment, service, and ingress resource to run an Nginx server. Configure the deployment with a single replica, expose it via a service, and define an ingress rule to route traffic to the application.

2. **Expose the App**  
   Enable network tunneling to make the application accessible externally, and test the connection using a curl command with the appropriate host header to verify the Nginx welcome page.

### Step 6: Simulate an Anomaly and Verify Remediation

1. **Simulate a DDoS**  
   Use a Kafka producer to send a simulated DDoS anomaly message to the predictions topic, specifying the anomaly type and a destination IP to trigger the remediation agent.

2. **Check Agent Logs**  
   Review the logs of the remediation agent pod to confirm that it has processed the anomaly and executed the remediation action successfully.

3. **Check Remediation Logs**  
   Consume messages from the remediation logs topic to verify that the agent has logged the outcome of the remediation action.

4. **Verify Scaling**  
   Check the status of the test application deployment to ensure that the replica count has been updated to reflect the scaling action performed by the agent.

---

## Usage

1. **Start the System**: Follow the setup steps to launch Minikube, Kafka, and the remediation agent.
2. **Test Remediation**: Use the Kafka producer to send a DDoS prediction and monitor the agent’s response.
3. **Monitor Results**: Check logs and deployment status to verify scaling and remediation success.

---

## Key Components

- **remediation_agent.py**: Python script that listens to Kafka, detects DDoS anomalies, and scales the `test-app` deployment.
- **Dockerfile**: Builds the agent container with Python dependencies.
- **agent-deployment.yaml**: Kubernetes configuration for deploying the agent with RBAC.
- **test-app Deployment**: A simple Nginx app for testing remediation actions.

---

## File Descriptions

The following files are included in this project, each serving a specific purpose:

- **Anomalyclassifier.py**  
  - **Description**: Contains the `AnomalyClassifier` class, which implements anomaly detection logic for network traffic. It classifies issues like DDoS attacks, port scans, and ICMP floods based on metrics such as packet bytes and port counts. The script processes a DataFrame with network flow data, applying rules to label anomalies (e.g., DDoS if packet bytes exceed 10,000 with multiple source IPs).

- **problem_statement.pdf**  
  - **Description**: Outlines the hackathon challenge from Guidewire Solutions, detailing Phase 1 (predicting Kubernetes issues) and Phase 2 (remediating predicted issues). It includes objectives, deliverables, and scoring criteria, providing the project’s context and goals.

- **remediation_agent.py**  
  - **Description**: Implements the `RemediationAgent` class, which listens to Kafka’s `predictions` topic for anomalies (e.g., DDoS) and applies remediation actions like scaling deployments. It uses the Kubernetes Python client and Kafka libraries to interact with the cluster and log actions to the `remediation_logs` topic.

- **agent-deployment.yaml**  
  - **Description**: A Kubernetes YAML file that defines the deployment configuration for the remediation agent. It includes a ServiceAccount, ClusterRole for RBAC permissions, ClusterRoleBinding, and a Deployment with one replica, using the locally built `remediation-agent:v1` image.

- **Dockerfile**  
  - **Description**: Specifies the container image for the remediation agent, based on `python:3.9-slim`. It copies `remediation_agent.py`, installs required Python packages (`kafka-python`, `kubernetes`), and sets the entry point to run the script.

- **rbac.yaml**  
  - **Description**: A Kubernetes YAML file that configures Role-Based Access Control (RBAC) for the remediation agent. It defines a ClusterRole with permissions to manage deployments and a ClusterRoleBinding to link it to the agent’s ServiceAccount, ensuring secure access to cluster resources.

- **requirements.txt**  
  - **Description**: A text file listing Python dependencies required by the remediation agent, such as `kafka-python` and `kubernetes`. It is used by `pip` during the Docker build process to install these libraries, ensuring the agent has the necessary tools to operate.

- **server.properties**  
  - **Description**: A configuration file for Kafka, specifying settings like authentication (e.g., SASL settings) and listener configurations. It is used to customize Kafka’s behavior within the cluster, such as enabling plaintext communication and managing connection timeouts.

- **istio-1.25.1-linux-amd64.tar.gz**  
  - **Description**: A compressed archive containing the Istio 1.25.1 distribution for Linux AMD64 architecture. Although not actively used in this Service Mesh-free implementation, it is included as a potential resource for future enhancements involving service mesh capabilities like mutual TLS or traffic management.

- **Pod_Failure_Issues_Phase_2.ipynb**  
  - **Description**: A Jupyter Notebook that analyzes pod failure issues in Kubernetes clusters as part of Phase 1 of the project. It loads a dataset (`k8s_raw_dataset.csv`) containing 100,000 rows with 13 columns, including timestamps, namespace, pod name, node name, CPU usage, memory usage, restarts, status, uptime, container count, host IP, pod IP, and a label (0 or 1 indicating failure). The notebook displays the dataset's structure, previews the first five rows, checks for missing values (none found), and includes a visualization of the data using a plot, likely to explore relationships between metrics and pod failures.

---

## Contributing

Contributions are welcome! Please fork the repository, create a feature branch, and submit a pull request with detailed changes.

---

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/concepts/overview/)
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Prometheus Documentation](https://prometheus.io/docs/introduction/overview/)
- Almaraz-Rivera, J. G., et al. "An Anomaly-based Detection System for Monitoring Kubernetes Infrastructures." [IEEE Latin America Transactions](https://latamt.ieeer9.org/index.php/transactions/article/view/7408)
- Kumar, V., et al. "A Survey on Anomaly Detection in Network Traffic." [International Journal of Computer Applications](https://www.ijcaonline.org/archives/volume176/number3/30938-2019915283)

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.