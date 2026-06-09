FROM python:3.12-slim AS base
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gcc g++ && rm -rf /var/lib/apt/lists/*

FROM base AS qiskit
RUN pip install --no-cache-dir qiskit qiskit-aer qiskit-ibm-provider
COPY services/quantum-rng/ /app/services/quantum-rng/
COPY services/quantum-key-exchange/ /app/services/quantum-key-exchange/
COPY services/quantum-ml/ /app/services/quantum-ml/
COPY pkg/python/ /app/pkg/python/
EXPOSE 8003 8004 8005
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8003/health
CMD ["python", "-m", "uvicorn", "services.quantum_rng.app.main:app", "--host", "0.0.0.0", "--port", "8003"]
