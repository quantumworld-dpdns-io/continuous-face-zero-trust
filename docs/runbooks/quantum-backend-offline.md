# Quantum Backend Offline - Incident Playbook

## Severity: Medium

## Impact
- QRNG falls back to simulator mode
- QKD key exchange fails
- VQC enhancement unavailable
- Reduced randomness quality

## Detection
- Alert: `qrng_hardware_offline`
- Alert: `qkd_connection_lost`
- Alert: `vqc_service_unavailable`

## Immediate Actions

### 1. Assess Impact (2 minutes)
```bash
# Check QRNG service status
kubectl get pods -n cfzt -l app=quantum-rng-service

# Check hardware connection
kubectl exec -it <pod-name> -n cfzt -- python -c "from qiskit import Aer; print(Aer.backends())"

# Check QKD status
kubectl exec -it <pod-name> -n cfzt -- curl -s http://localhost:8085/api/v1/quantum/qkd/status | jq .
```

### 2. Check Logs (2 minutes)
```bash
# Service logs
kubectl logs -n cfzt -l app=quantum-rng-service --tail=100

# Check for hardware errors
kubectl exec -it <pod-name> -n cfzt -- dmesg | grep -i quantum
```

### 3. Check Network (1 minute)
```bash
# Check QKD network connectivity
kubectl exec -it <pod-name> -n cfzt -- ping qkd-trust-node.cfzt.io

# Check firewall rules
kubectl exec -it <pod-name> -n cfzt -- iptables -L -n | grep 8084
```

## Resolution Steps

### Scenario 1: Hardware QRNG Failure
```bash
# Check USB connection
kubectl exec -it <pod-name> -n cfzt -- lsusb | grep HockeyPuck

# Restart QRNG service
kubectl rollout restart deployment/quantum-rng-service -n cfzt

# Verify fallback to simulator
kubectl exec -it <pod-name> -n cfzt -- curl -s http://localhost:8085/api/v1/quantum/rng/health | jq .
```

### Scenario 2: Simulator Issues
```bash
# Check Qiskit installation
kubectl exec -it <pod-name> -n cfzt -- python -c "import qiskit; print(qiskit.__version__)"

# Reinstall Qiskit
kubectl exec -it <pod-name> -n cfzt -- pip install qiskit-aer --upgrade

# Restart service
kubectl rollout restart deployment/quantum-rng-service -n cfzt
```

### Scenario 3: QKD Network Failure
```bash
# Check QKD trust node
kubectl exec -it <pod-name> -n cfzt -- curl -s https://qkd-trust-node.cfzt.io/health

# Restart QKD connection
kubectl exec -it <pod-name> -n cfzt -- python -c "from cfzt.quantum import QKDClient; client = QKDClient(); client.restart()"

# Fallback to PQC key exchange
kubectl exec -it <pod-name> -n cfzt -- python -c "from cfzt.quantum import KeyExchange; exchange = KeyExchange(mode='pqc'); print(exchange.status())"
```

### Scenario 4: VQC Service Issues
```bash
# Check VQC backend
kubectl exec -it <pod-name> -n cfzt -- python -c "from qiskit import Aer; backend = Aer.get_backend('qasm_simulator'); print(backend.status())"

# Restart VQC service
kubectl rollout restart deployment/vqc-service -n cfzt

# Fallback to classical ML
kubectl exec -it <pod-name> -n cfzt -- python -c "from cfzt.quantum import VQCConfig; config = VQCConfig(enabled=False); print(config)"
```

## Fallback Procedures

### QRNG Fallback
```python
class QRNGFallback:
    def __init__(self):
        self.hardware_available = False
        self.simulator_available = True
        self.csprng_available = True
    
    def generate_random(self, num_bits: int) -> bytes:
        if self.hardware_available:
            return self.hardware_qrng.generate(num_bits)
        elif self.simulator_available:
            return self.simulator_qrng.generate(num_bits)
        elif self.csprng_available:
            return self.csprng.generate(num_bits)
        else:
            raise QRNGUnavailable()
```

### QKD Fallback
```python
class QKDFallback:
    def __init__(self):
        self.qkd_available = False
        self.pqc_available = True
    
    def exchange_key(self) -> bytes:
        if self.qkd_available:
            return self.qkd.exchange_key()
        elif self.pqc_available:
            return self.pqc.kem_encapsulate()
        else:
            raise KeyExchangeUnavailable()
```

## Post-Incident

### 1. Verify Recovery
```bash
# Test QRNG
curl -X POST http://quantum-rng-service:8085/api/v1/quantum/rng/generate \
  -H "Content-Type: application/json" \
  -d '{"num_bits": 256}'

# Test QKD
curl -X POST http://quantum-rng-service:8085/api/v1/quantum/qkd/exchange \
  -H "Content-Type: application/json" \
  -d '{"key_size": 256}'
```

### 2. Monitor Metrics
```bash
# Watch QRNG throughput
kubectl port-forward -n cfzt svc/prometheus 9090:9090

# Check Grafana dashboard
open http://grafana:3000/d/quantum-rng
```

### 3. Document Incident
- Create incident report
- Update runbook if needed
- Schedule post-mortem

## Prevention

### Redundancy
```yaml
# Multiple QRNG backends
apiVersion: v1
kind: ConfigMap
metadata:
  name: quantum-rng-config
  namespace: cfzt
data:
  backends: |
    - type: hardware
      enabled: true
      fallback: simulator
    - type: simulator
      enabled: true
      fallback: csprng
    - type: csprng
      enabled: true
      fallback: none
```

### Health Monitoring
```python
class QuantumHealthMonitor:
    def check_health(self) -> HealthStatus:
        return HealthStatus(
            hardware=self.check_hardware(),
            simulator=self.check_simulator(),
            qkd=self.check_qkd(),
            vqc=self.check_vqc()
        )
```

### Automated Failover
```python
class QuantumFailover:
    def auto_failover(self):
        if not self.hardware_available:
            self.switch_to_simulator()
            self.alert("QRNG hardware unavailable, using simulator")
        
        if not self.simulator_available:
            self.switch_to_csprng()
            self.alert("QRNG simulator unavailable, using CSPRNG")
```

## Escalation

| Time | Action |
|------|--------|
| 0-5 min | On-call engineer |
| 5-15 min | Quantum team lead |
| 15-30 min | Engineering manager |
| 30+ min | VP Engineering |

## Communication

### Internal
- Slack: #incidents
- PagerDuty: Quantum Backend Offline

### External
- Status page: status.cfzt.io
- Email: support@cfzt.io
