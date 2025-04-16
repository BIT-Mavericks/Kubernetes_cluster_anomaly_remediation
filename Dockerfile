FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "remediation_agent.py"]
