# Local Quantum Simulation Setup

## Overview

This runbook covers setting up local quantum simulation for development and testing.

## Prerequisites

- Python 3.10+
- Docker (optional)
- 8GB+ RAM
- GPU (optional, for CUDA-Q)

## Installation

### 1. Install Qiskit

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install Qiskit
pip install qiskit qiskit-aer qiskit-ibm-provider

# Verify installation
python -c "import qiskit; print(qiskit.__version__)"
```

### 2. Install CUDA-Q (Optional)

```bash
# Install CUDA-Q
pip install cudaq

# Verify installation
python -c "import cudaq; print(cudaq.__version__)"
```

### 3. Install Quantum Libraries

```bash
# Install quantum libraries
pip install pennylane
pip install cirq
pip install amazon-braket-sdk

# Verify installation
python -c "import pennylane; print(pennylane.__version__)"
python -c "import cirq; print(cirq.__version__)"
```

## Configuration

### 1. Qiskit Configuration

```python
# qiskit_config.py
from qiskit import Aer
from qiskit.providers.aer import AerSimulator

# Configure simulator
simulator = AerSimulator()

# Configure backend
backend = Aer.get_backend('qasm_simulator')

# Configure provider
provider = Aer
```

### 2. CUDA-Q Configuration

```python
# cudaq_config.py
import cudaq

# Configure simulator
cudaq.set_target('qpp-cpu')  # CPU simulator
# cudaq.set_target('nvidia')  # GPU simulator (requires CUDA)

# Configure backend
backend = cudaq.get_backend('qpp-cpu')
```

### 3. PennyLane Configuration

```python
# pennylane_config.py
import pennylane as qml

# Configure device
dev = qml.device('default.qubit', wires=4)

# Configure simulator
simulator = qml.Simulator()
```

## Usage

### 1. QRNG Simulation

```python
# qrng_simulation.py
from qiskit import QuantumCircuit, Aer, execute
import numpy as np

def generate_random_bits(num_bits: int) -> list:
    """Generate random bits using quantum circuit."""
    # Create quantum circuit
    qc = QuantumCircuit(num_bits, num_bits)
    
    # Apply Hadamard gates
    for i in range(num_bits):
        qc.h(i)
    
    # Measure
    qc.measure(range(num_bits), range(num_bits))
    
    # Execute
    backend = Aer.get_backend('qasm_simulator')
    job = execute(qc, backend, shots=1)
    result = job.result()
    counts = result.get_counts()
    
    # Extract bits
    bits = list(counts.keys())[0]
    return [int(b) for b in bits]

# Generate 256 random bits
random_bits = generate_random_bits(256)
print(f"Generated {len(random_bits)} random bits")
```

### 2. VQC Simulation

```python
# vqc_simulation.py
import pennylane as qml
import numpy as np

# Configure device
dev = qml.device('default.qubit', wires=4)

@qml.qnode(dev)
def quantum_circuit(inputs, weights):
    """Variational quantum circuit."""
    # Encode inputs
    for i in range(4):
        qml.RY(inputs[i], wires=i)
    
    # Apply variational layers
    for layer in range(3):
        for i in range(4):
            qml.RY(weights[layer * 4 + i], wires=i)
        
        # Entangle
        qml.CNOT(wires=[0, 1])
        qml.CNOT(wires=[1, 2])
        qml.CNOT(wires=[2, 3])
    
    # Measure
    return [qml.expval(qml.PauliZ(i)) for i in range(4)]

# Initialize weights
weights = np.random.uniform(0, 2 * np.pi, 12)

# Run circuit
inputs = np.random.uniform(0, np.pi, 4)
result = quantum_circuit(inputs, weights)
print(f"VQC result: {result}")
```

### 3. QKD Simulation

```python
# qkd_simulation.py
from qiskit import QuantumCircuit, Aer, execute
import numpy as np

def bb84_simulation(key_length: int) -> tuple:
    """Simulate BB84 QKD protocol."""
    # Alice's bits and bases
    alice_bits = np.random.randint(0, 2, key_length)
    alice_bases = np.random.randint(0, 2, key_length)
    
    # Bob's bases
    bob_bases = np.random.randint(0, 2, key_length)
    
    # Create quantum circuit
    qc = QuantumCircuit(key_length, key_length)
    
    # Alice prepares qubits
    for i in range(key_length):
        if alice_bits[i] == 1:
            qc.x(i)
        if alice_bases[i] == 1:
            qc.h(i)
    
    # Bob measures
    for i in range(key_length):
        if bob_bases[i] == 1:
            qc.h(i)
        qc.measure(i, i)
    
    # Execute
    backend = Aer.get_backend('qasm_simulator')
    job = execute(qc, backend, shots=1)
    result = job.result()
    counts = result.get_counts()
    
    # Extract measurement results
    bob_bits = list(counts.keys())[0]
    bob_bits = [int(b) for b in bob_bits]
    
    # Key sifting
    matching_bases = alice_bases == bob_bases
    alice_key = alice_bits[matching_bases]
    bob_key = np.array(bob_bits)[matching_bases]
    
    return alice_key, bob_key

# Simulate QKD
alice_key, bob_key = bb84_simulation(256)
print(f"Alice's key length: {len(alice_key)}")
print(f"Bob's key length: {len(bob_key)}")
print(f"Keys match: {np.array_equal(alice_key, bob_key)}")
```

## Docker Setup

### 1. Dockerfile

```dockerfile
# Dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    qiskit \
    qiskit-aer \
    pennylane \
    numpy

# Set working directory
WORKDIR /app

# Copy application
COPY . .

# Run application
CMD ["python", "main.py"]
```

### 2. Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  quantum-simulator:
    build: .
    ports:
      - "8080:8080"
    environment:
      - SIMULATOR=qiskit
      - NUM_QUBITS=4
    volumes:
      - ./data:/app/data
```

## Testing

### 1. Unit Tests

```python
# test_quantum.py
import pytest
from qiskit import QuantumCircuit, Aer, execute

def test_qrng():
    """Test QRNG generation."""
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.h(1)
    qc.measure([0, 1], [0, 1])
    
    backend = Aer.get_backend('qasm_simulator')
    job = execute(qc, backend, shots=100)
    result = job.result()
    counts = result.get_counts()
    
    assert len(counts) > 1  # Should have multiple outcomes

def test_vqc():
    """Test VQC circuit."""
    import pennylane as qml
    import numpy as np
    
    dev = qml.device('default.qubit', wires=2)
    
    @qml.qnode(dev)
    def circuit(inputs, weights):
        qml.RY(inputs[0], wires=0)
        qml.RY(inputs[1], wires=1)
        qml.CNOT(wires=[0, 1])
        return qml.expval(qml.PauliZ(0))
    
    inputs = np.array([0.5, 0.5])
    weights = np.array([0.1, 0.2])
    result = circuit(inputs, weights)
    
    assert isinstance(result, float)
```

### 2. Integration Tests

```python
# test_integration.py
import pytest
from cfzt.quantum import QRNGSimulator, VQCSimulator, QKDSimulator

def test_qrng_integration():
    """Test QRNG integration."""
    simulator = QRNGSimulator()
    random_bits = simulator.generate(256)
    
    assert len(random_bits) == 256
    assert all(b in [0, 1] for b in random_bits)

def test_vqc_integration():
    """Test VQC integration."""
    simulator = VQCSimulator()
    result = simulator.predict([0.5, 0.5, 0.5, 0.5])
    
    assert isinstance(result, float)
    assert -1 <= result <= 1

def test_qkd_integration():
    """Test QKD integration."""
    simulator = QKDSimulator()
    alice_key, bob_key = simulator.exchange(256)
    
    assert len(alice_key) == 256
    assert len(bob_key) == 256
    assert np.array_equal(alice_key, bob_key)
```

## Monitoring

### Key Metrics

```yaml
# Quantum simulation metrics
- quantum_simulation_duration_seconds{type}
- quantum_simulation_success_total{type}
- quantum_simulation_failure_total{type}
- quantum_simulation_qubits{type}
```

### Alerts

```yaml
groups:
- name: quantum-simulation
  rules:
  - alert: SimulationSlow
    expr: rate(quantum_simulation_duration_seconds[5m]) > 10
    for: 5m
    labels:
      severity: warning
    
  - alert: SimulationFailing
    expr: rate(quantum_simulation_failure_total[5m]) > 0
    for: 5m
    labels:
      severity: critical
```

## Escalation

| Time | Action |
|------|--------|
| 0-5 min | Developer |
| 5-15 min | Quantum team lead |
| 15-30 min | Engineering manager |
| 30+ min | VP Engineering |

## Communication

### Internal
- Slack: #quantum-simulation
- PagerDuty: Quantum Simulation Issues

### External
- Status page: status.cfzt.io
- Email: support@cfzt.io
