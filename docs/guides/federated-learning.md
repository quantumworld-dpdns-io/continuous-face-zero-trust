# Federated Learning Development Guide

## Overview

This guide covers federated learning for the CFZT system using Flower.

## Prerequisites

- Python 3.10+
- Flower 1.0+
- PyTorch 2.0+

## Installation

```bash
# Install Flower
pip install flwr

# Install PyTorch
pip install torch torchvision

# Verify installation
python -c "import flwr; print(flwr.__version__)"
```

## Basic Flower Setup

### 1. Server

```python
# server.py
import flwr as fl

def main():
    # Define strategy
    strategy = fl.server.strategy.FedAvg(
        fraction_fit=0.3,
        fraction_evaluate=0.2,
        min_fit_clients=3,
        min_evaluate_clients=2,
        min_available_clients=5,
    )
    
    # Start server
    fl.server.start_server(
        server_address="0.0.0.0:8080",
        config=fl.server.ServerConfig(num_rounds=3),
        strategy=strategy,
    )

if __name__ == "__main__":
    main()
```

### 2. Client

```python
# client.py
import flwr as fl
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

class FaceMatchingModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(512, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, 1)
    
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = torch.sigmoid(self.fc3(x))
        return x

class FlowerClient(fl.client.NumPyClient):
    def __init__(self, model, trainloader, valloader):
        self.model = model
        self.trainloader = trainloader
        self.valloader = valloader
    
    def get_parameters(self, config):
        return [val.cpu().numpy() for _, val in self.model.state_dict().items()]
    
    def set_parameters(self, parameters):
        params_dict = zip(self.model.state_dict().keys(), parameters)
        state_dict = {k: torch.tensor(v) for k, v in params_dict}
        self.model.load_state_dict(state_dict, strict=True)
    
    def fit(self, parameters, config):
        self.set_parameters(parameters)
        self.train()
        return self.get_parameters(config={}), len(self.trainloader.dataset), {}
    
    def evaluate(self, parameters, config):
        self.set_parameters(parameters)
        loss, accuracy = self.evaluate()
        return float(loss), len(self.valloader.dataset), {"accuracy": float(accuracy)}
    
    def train(self):
        criterion = nn.BCELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        
        self.model.train()
        for epoch in range(5):
            for batch in self.trainloader:
                inputs, labels = batch
                optimizer.zero_grad()
                outputs = self.model(inputs)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
    
    def evaluate(self):
        criterion = nn.BCELoss()
        correct = 0
        total = 0
        total_loss = 0
        
        self.model.eval()
        with torch.no_grad():
            for batch in self.valloader:
                inputs, labels = batch
                outputs = self.model(inputs)
                loss = criterion(outputs, labels)
                total_loss += loss.item()
                predicted = (outputs > 0.5).float()
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        
        accuracy = correct / total
        avg_loss = total_loss / len(self.valloader)
        return avg_loss, accuracy

def main():
    # Load data
    trainloader, valloader = load_data()
    
    # Create model
    model = FaceMatchingModel()
    
    # Start client
    fl.client.start_client(
        server_address="server:8080",
        client=FlowerClient(model, trainloader, valloader).to_client(),
    )

if __name__ == "__main__":
    main()
```

## Privacy-Preserving Federated Learning

### 1. Differential Privacy

```python
# dp_client.py
import flwr as fl
from flwr.common import DifferentialPrivacyConfig

def main():
    # Define DP strategy
    strategy = fl.server.strategy.FedAvg(
        fraction_fit=0.3,
        fraction_evaluate=0.2,
        min_fit_clients=3,
        min_evaluate_clients=2,
        min_available_clients=5,
    )
    
    # Add DP
    dp_config = DifferentialPrivacyConfig(
        noise_multiplier=1.0,
        num_samples=1000,
        clip_norm=1.0,
    )
    
    # Start server with DP
    fl.server.start_server(
        server_address="0.0.0.0:8080",
        config=fl.server.ServerConfig(num_rounds=3),
        strategy=strategy,
        dp_config=dp_config,
    )
```

### 2. Secure Aggregation

```python
# secure_aggregation.py
import flwr as fl

def main():
    # Define strategy with secure aggregation
    strategy = fl.server.strategy.FedAvg(
        fraction_fit=0.3,
        fraction_evaluate=0.2,
        min_fit_clients=3,
        min_evaluate_clients=2,
        min_available_clients=5,
        secure_aggregation=True,
    )
    
    # Start server with secure aggregation
    fl.server.start_server(
        server_address="0.0.0.0:8080",
        config=fl.server.ServerConfig(num_rounds=3),
        strategy=strategy,
    )
```

## Custom Strategy

```python
# custom_strategy.py
import flwr as fl
from flwr.common import FitRes, EvaluateRes, Parameters
from typing import List, Tuple
import numpy as np

class CustomStrategy(fl.server.strategy.FedAvg):
    def aggregate_fit(
        self,
        server_round: int,
        results: List[Tuple[fl.server.client_proxy.ClientProxy, FitRes]],
        failures: List[BaseException],
    ) -> Tuple[Parameters, dict]:
        # Custom aggregation logic
        if not results:
            return Parameters(), {}
        
        # Weight by accuracy
        weights = []
        for _, fit_res in results:
            accuracy = fit_res.metrics.get("accuracy", 0.5)
            weights.append(accuracy)
        
        # Normalize weights
        total = sum(weights)
        weights = [w / total for w in weights]
        
        # Aggregate parameters
        aggregated_parameters = self.aggregate_parameters(results, weights)
        
        return aggregated_parameters, {}
    
    def aggregate_parameters(
        self,
        results: List[Tuple[fl.server.client_proxy.ClientProxy, FitRes]],
        weights: List[float],
    ) -> Parameters:
        # Custom parameter aggregation
        aggregated = None
        
        for (_, fit_res), weight in zip(results, weights):
            parameters = fl.common.parameters_to_ndarrays(fit_res.parameters)
            
            if aggregated is None:
                aggregated = [p * weight for p in parameters]
            else:
                aggregated = [a + p * weight for a, p in zip(aggregated, parameters)]
        
        return fl.common.ndarrays_to_parameters(aggregated)
```

## Data Loading

```python
# data.py
import torch
from torch.utils.data import DataLoader, TensorDataset
import numpy as np

def load_data():
    """Load training and validation data."""
    # Generate synthetic data
    np.random.seed(42)
    X_train = np.random.randn(1000, 512).astype(np.float32)
    y_train = np.random.randint(0, 2, (1000, 1)).astype(np.float32)
    
    X_val = np.random.randn(200, 512).astype(np.float32)
    y_val = np.random.randint(0, 2, (200, 1)).astype(np.float32)
    
    # Create datasets
    train_dataset = TensorDataset(
        torch.tensor(X_train),
        torch.tensor(y_train),
    )
    
    val_dataset = TensorDataset(
        torch.tensor(X_val),
        torch.tensor(y_val),
    )
    
    # Create dataloaders
    trainloader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    valloader = DataLoader(val_dataset, batch_size=32, shuffle=False)
    
    return trainloader, valloader
```

## Testing

### 1. Unit Tests

```python
# tests/test_fl.py
import pytest
from fl.client import FlowerClient
from model import FaceMatchingModel

@pytest.fixture
def client():
    model = FaceMatchingModel()
    trainloader, valloader = load_data()
    return FlowerClient(model, trainloader, valloader)

def test_get_parameters(client):
    parameters = client.get_parameters(config={})
    assert len(parameters) > 0

def test_fit(client):
    parameters, num_examples, metrics = client.fit([], config={})
    assert num_examples > 0

def test_evaluate(client):
    loss, num_examples, metrics = client.evaluate([], config={})
    assert loss >= 0
    assert num_examples > 0
```

### 2. Integration Tests

```python
# tests/integration/test_fl.py
import pytest
import flwr as fl
from server import main as server_main
from client import main as client_main

def test_fl_training():
    """Test federated learning training."""
    # Start server in background
    # Start multiple clients
    # Verify training completes
    pass
```

## Deployment

### 1. Docker Compose

```yaml
# docker-compose-fl.yml
version: '3.8'

services:
  server:
    build: .
    command: python server.py
    ports:
      - "8080:8080"
  
  client-1:
    build: .
    command: python client.py
    depends_on:
      - server
  
  client-2:
    build: .
    command: python client.py
    depends_on:
      - server
  
  client-3:
    build: .
    command: python client.py
    depends_on:
      - server
```

### 2. Kubernetes

```yaml
# k8s/fl-server.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fl-server
  namespace: cfzt
spec:
  replicas: 1
  selector:
    matchLabels:
      app: fl-server
  template:
    metadata:
      labels:
        app: fl-server
    spec:
      containers:
      - name: fl-server
        image: cfzt/fl-server:latest
        ports:
        - containerPort: 8080
```

## Resources

- [Flower Documentation](https://flower.dev/docs/)
- [PyTorch Documentation](https://pytorch.org/docs/)
- [Federated Learning Paper](https://arxiv.org/abs/1602.05629)
