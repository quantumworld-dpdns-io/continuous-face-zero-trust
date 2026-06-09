# Event-Driven Architecture

## Overview

CFZT uses an event-driven architecture for asynchronous communication, audit logging, and analytics processing.

## Event Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        EVENT ARCHITECTURE                                │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Event Producers                                                   │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │ │
│  │  │  Auth    │  │  Face ML │  │  Quantum │  │  ZK      │         │ │
│  │  │  Service │  │  Service │  │  RNG     │  │  Proofs  │         │ │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘         │ │
│  │       │              │              │              │               │ │
│  │       └──────────────┼──────────────┼──────────────┘               │ │
│  │                      │              │                              │ │
│  └──────────────────────┼──────────────┼──────────────────────────────┘ │
│                         │              │                                │
│                  ┌──────┴──────┐  ┌────┴─────┐                        │
│                  │    Kafka    │  │  Redis   │                        │
│                  │   (Events)  │  │ (Pub/Sub)│                        │
│                  └──────┬──────┘  └────┬─────┘                        │
│                         │              │                                │
│  ┌──────────────────────┼──────────────┼──────────────────────────────┐ │
│  │  Event Consumers     │              │                              │ │
│  │  ┌──────────┐  ┌────┴─────┐  ┌────┴─────┐  ┌──────────┐         │ │
│  │  │Analytics │  │  Audit   │  │  Cache   │  │  Alert   │         │ │
│  │  │ Service  │  │  Service │  │  Service │  │  Service │         │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

## Event Types

### Domain Events

```typescript
// Event Schema
interface DomainEvent {
  event_id: string;
  event_type: string;
  aggregate_id: string;
  aggregate_type: string;
  timestamp: string;
  version: number;
  payload: Record<string, unknown>;
  metadata: {
    correlation_id: string;
    causation_id: string;
    user_id?: string;
    ip_address?: string;
    user_agent?: string;
  };
}

// Event Types
type EventType =
  | 'auth.login'
  | 'auth.logout'
  | 'auth.enroll'
  | 'auth.refresh'
  | 'auth.verify'
  | 'auth.challenge'
  | 'face.detect'
  | 'face.embed'
  | 'face.compare'
  | 'face.liveness'
  | 'face.search'
  | 'quantum.rng.generate'
  | 'quantum.rng.health'
  | 'zk.proof.generate'
  | 'zk.proof.verify'
  | 'pqc.key.generate'
  | 'pqc.sign'
  | 'pqc.verify'
  | 'session.create'
  | 'session.refresh'
  | 'session.expire'
  | 'session.invalidate'
  | 'security.anomaly'
  | 'security.breach'
  | 'system.health'
  | 'system.degradation';
```

### Event Schemas

```json
// Auth Success Event
{
  "event_id": "uuid",
  "event_type": "auth.login",
  "aggregate_id": "session-uuid",
  "aggregate_type": "Session",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": 1,
  "payload": {
    "user_id": "user-uuid",
    "device_id": "device-uuid",
    "face_similarity": 0.95,
    "risk_score": 0.1,
    "session_duration": 86400,
    "token_type": "paseTO"
  },
  "metadata": {
    "correlation_id": "corr-uuid",
    "causation_id": "cause-uuid",
    "ip_address": "hashed-ip",
    "user_agent": "Mozilla/5.0..."
  }
}

// Continuous Verify Event
{
  "event_id": "uuid",
  "event_type": "auth.verify",
  "aggregate_id": "session-uuid",
  "aggregate_type": "Session",
  "timestamp": "2024-01-01T00:00:30Z",
  "version": 2,
  "payload": {
    "user_id": "user-uuid",
    "face_similarity": 0.92,
    "risk_score": 0.15,
    "action": "allow",
    "refresh_interval": 300
  },
  "metadata": {
    "correlation_id": "corr-uuid",
    "causation_id": "auth.login-uuid"
  }
}

// Security Anomaly Event
{
  "event_id": "uuid",
  "event_type": "security.anomaly",
  "aggregate_id": "user-uuid",
  "aggregate_type": "User",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": 1,
  "payload": {
    "anomaly_type": "face_mismatch",
    "severity": "high",
    "face_similarity": 0.45,
    "expected_similarity": 0.85,
    "device_trust": 0.3,
    "action_taken": "step_up_auth"
  },
  "metadata": {
    "correlation_id": "corr-uuid",
    "user_id": "user-uuid",
    "ip_address": "hashed-ip"
  }
}
```

## Kafka Topics

### Topic Configuration

```yaml
# Kafka Topic Configuration
topics:
  auth-events:
    partitions: 12
    replication_factor: 3
    retention_ms: 7776000000  # 90 days
    config:
      cleanup.policy: delete
      compression.type: lz4
      min.insync.replicas: 2

  enrollment-events:
    partitions: 6
    replication_factor: 3
    retention_ms: 7776000000
    config:
      cleanup.policy: delete
      compression.type: lz4

  verify-events:
    partitions: 12
    replication_factor: 3
    retention_ms: 2592000000  # 30 days
    config:
      cleanup.policy: delete
      compression.type: lz4

  proof-events:
    partitions: 6
    replication_factor: 3
    retention_ms: 2592000000
    config:
      cleanup.policy: delete
      compression.type: lz4

  security-events:
    partitions: 6
    replication_factor: 3
    retention_ms: 31536000000  # 1 year
    config:
      cleanup.policy: compact,delete
      compression.type: lz4
```

### Topic Partitioning

```
auth-events
├── Partition 0: user_id % 12 == 0
├── Partition 1: user_id % 12 == 1
├── ...
└── Partition 11: user_id % 12 == 11

# Ensures ordered processing per user
```

## CQRS Pattern

### Command Side

```
┌─────────────────────────────────────────────────────────────────┐
│  Command Side                                                    │
│                                                                  │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐               │
│  │  Command │────▶│  Command │────▶│  Event   │               │
│  │  Handler │     │  Bus     │     │  Store   │               │
│  └──────────┘     └──────────┘     └──────────┘               │
│                                                                  │
│  Commands:                                                       │
│  - LoginCommand                                                  │
│  - EnrollCommand                                                 │
│  - VerifyCommand                                                 │
│  - RefreshTokenCommand                                           │
└─────────────────────────────────────────────────────────────────┘
```

### Query Side

```
┌─────────────────────────────────────────────────────────────────┐
│  Query Side                                                      │
│                                                                  │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐               │
│  │  Query   │────▶│  Query   │────▶│  Read    │               │
│  │  Handler │     │  Bus     │     │  Model   │               │
│  └──────────┘     └──────────┘     └──────────┘               │
│                                                                  │
│  Queries:                                                        │
│  - GetSessionQuery                                               │
│  - GetUserSessionsQuery                                          │
│  - GetAuthHistoryQuery                                           │
│  - GetRiskScoreQuery                                             │
└─────────────────────────────────────────────────────────────────┘
```

### Event Store

```sql
-- Event Store Schema
CREATE TABLE events (
    event_id UUID PRIMARY KEY,
    event_type VARCHAR(255) NOT NULL,
    aggregate_id UUID NOT NULL,
    aggregate_type VARCHAR(255) NOT NULL,
    version INT NOT NULL,
    payload JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(aggregate_id, version)
);

-- Indexes
CREATE INDEX idx_events_aggregate ON events(aggregate_id);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_created ON events(created_at);
```

### Projection

```python
class SessionProjection:
    def project(self, event: DomainEvent):
        """Update read model based on event."""
        if event.event_type == "session.create":
            self.create_session(event.payload)
        elif event.event_type == "session.refresh":
            self.refresh_session(event.aggregate_id, event.payload)
        elif event.event_type == "session.expire":
            self.expire_session(event.aggregate_id)
        elif event.event_type == "session.invalidate":
            self.invalidate_session(event.aggregate_id)
    
    def create_session(self, payload: dict):
        """Create session read model."""
        session = SessionReadModel(
            session_id=payload["session_id"],
            user_id=payload["user_id"],
            device_id=payload["device_id"],
            created_at=payload["created_at"],
            expires_at=payload["expires_at"],
            risk_score=payload["risk_score"],
            status="active"
        )
        self.db.upsert(session)
```

## Event Processing

### Event Handlers

```python
class AuthEventHandler:
    def handle_login_success(self, event: DomainEvent):
        """Handle successful login."""
        # Update session state
        self.session_store.create(
            session_id=event.payload["session_id"],
            user_id=event.payload["user_id"],
            risk_score=event.payload["risk_score"]
        )
        
        # Update analytics
        self.analytics.track(
            event_type="login_success",
            user_id=event.payload["user_id"],
            risk_score=event.payload["risk_score"]
        )
        
        # Check for anomalies
        if event.payload["risk_score"] > 0.7:
            self.alert_service.trigger(
                alert_type="high_risk_login",
                user_id=event.payload["user_id"],
                severity="warning"
            )
    
    def handle_login_failure(self, event: DomainEvent):
        """Handle failed login."""
        # Track failure
        self.analytics.track(
            event_type="login_failure",
            user_id=event.payload["user_id"],
            reason=event.payload["reason"]
        )
        
        # Check for brute force
        failure_count = self.failure_store.increment(
            user_id=event.payload["user_id"],
            window=300  # 5 minutes
        )
        
        if failure_count > 5:
            self.alert_service.trigger(
                alert_type="brute_force_detected",
                user_id=event.payload["user_id"],
                severity="critical"
            )
```

### Event Sourcing

```python
class SessionAggregate:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.events = []
    
    def create(self, user_id: str, device_id: str, risk_score: float):
        """Create new session."""
        event = DomainEvent(
            event_type="session.create",
            aggregate_id=self.session_id,
            aggregate_type="Session",
            payload={
                "user_id": user_id,
                "device_id": device_id,
                "risk_score": risk_score,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
        )
        self.events.append(event)
    
    def refresh(self, risk_score: float):
        """Refresh session."""
        event = DomainEvent(
            event_type="session.refresh",
            aggregate_id=self.session_id,
            aggregate_type="Session",
            payload={
                "risk_score": risk_score,
                "refreshed_at": datetime.utcnow().isoformat()
            }
        )
        self.events.append(event)
    
    def expire(self):
        """Expire session."""
        event = DomainEvent(
            event_type="session.expire",
            aggregate_id=self.session_id,
            aggregate_type="Session",
            payload={
                "expired_at": datetime.utcnow().isoformat()
            }
        )
        self.events.append(event)
```

## Event Replay

### Replay Strategy

```python
class EventReplayService:
    def replay_events(self, aggregate_id: str, from_version: int = 0):
        """Replay events for an aggregate."""
        events = self.event_store.get_events(
            aggregate_id=aggregate_id,
            from_version=from_version
        )
        
        aggregate = SessionAggregate(aggregate_id)
        for event in events:
            aggregate.apply(event)
        
        return aggregate
    
    def replay_all(self, event_type: str, since: datetime):
        """Replay all events of a type since a timestamp."""
        events = self.event_store.get_events_by_type(
            event_type=event_type,
            since=since
        )
        
        for event in events:
            self.process_event(event)
```

## Dead Letter Queue

### DLQ Configuration

```yaml
# Kafka DLQ Configuration
topics:
  auth-events-dlq:
    partitions: 6
    replication_factor: 3
    retention_ms: 2592000000  # 30 days
    config:
      cleanup.policy: delete
      compression.type: lz4

# Consumer Configuration
consumers:
  auth-consumer:
    group_id: auth-service-group
    enable.auto.commit: false
    max.poll.interval.ms: 300000
    session.timeout.ms: 30000
    isolation.level: read_committed
```

### DLQ Processing

```python
class DLQProcessor:
    def process_dlq_message(self, message: ConsumerRecord):
        """Process dead letter queue message."""
        try:
            # Attempt to process again
            self.process_message(message)
        except Exception as e:
            # Log failure
            self.logger.error(f"DLQ processing failed: {e}")
            
            # Store for manual review
            self.failed_store.store({
                "topic": message.topic,
                "partition": message.partition,
                "offset": message.offset,
                "key": message.key,
                "value": message.value,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Alert if critical
            if self.is_critical(message):
                self.alert_service.trigger(
                    alert_type="dlq_critical_message",
                    severity="critical"
                )
```
