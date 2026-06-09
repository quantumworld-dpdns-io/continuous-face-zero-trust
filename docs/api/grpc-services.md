# gRPC Service Documentation

## Overview

This document describes the gRPC services used in the CFZT system.

## Service Definitions

### Auth Service

```protobuf
syntax = "proto3";

package cfzt.auth;

service AuthService {
  rpc Login(LoginRequest) returns (LoginResponse);
  rpc Enroll(EnrollRequest) returns (EnrollResponse);
  rpc RefreshToken(RefreshRequest) returns (RefreshResponse);
  rpc Logout(LogoutRequest) returns (LogoutResponse);
  rpc ContinuousVerify(VerifyRequest) returns (VerifyResponse);
  rpc GetSession(GetSessionRequest) returns (Session);
}

message LoginRequest {
  string user_id = 1;
  string device_id = 2;
  bytes face_image = 3;
}

message LoginResponse {
  string token = 1;
  string refresh_token = 2;
  int64 expires_in = 3;
  string session_id = 4;
  float risk_score = 5;
}

message EnrollRequest {
  string user_id = 1;
  string device_id = 2;
  repeated bytes face_images = 3;
}

message EnrollResponse {
  bool success = 1;
  string user_id = 2;
  string embedding_id = 3;
}

message RefreshRequest {
  string refresh_token = 1;
}

message RefreshResponse {
  string token = 1;
  string refresh_token = 2;
  int64 expires_in = 3;
}

message LogoutRequest {}

message LogoutResponse {
  bool success = 1;
}

message VerifyRequest {
  bytes face_image = 1;
}

message VerifyResponse {
  bool success = 1;
  float similarity = 2;
  float risk_score = 3;
  string action = 4;
}

message GetSessionRequest {
  string session_id = 1;
}

message Session {
  string session_id = 1;
  string user_id = 2;
  string device_id = 3;
  string created_at = 4;
  string expires_at = 5;
  float risk_score = 6;
  string status = 7;
}
```

### Face ML Service

```protobuf
syntax = "proto3";

package cfzt.face;

service FaceMLService {
  rpc Detect(DetectRequest) returns (DetectResponse);
  rpc Embed(EmbedRequest) returns (EmbedResponse);
  rpc Compare(CompareRequest) returns (CompareResponse);
  rpc LivenessCheck(LivenessRequest) returns (LivenessResponse);
  rpc Search(SearchRequest) returns (SearchResponse);
  rpc QuantumEmbed(QuantumEmbedRequest) returns (QuantumEmbedResponse);
}

message DetectRequest {
  bytes image = 1;
}

message DetectResponse {
  repeated Face faces = 1;
}

message Face {
  BoundingBox bounding_box = 1;
  float confidence = 2;
  repeated Point landmarks = 3;
}

message BoundingBox {
  float x = 1;
  float y = 2;
  float width = 3;
  float height = 4;
}

message Point {
  float x = 1;
  float y = 2;
}

message EmbedRequest {
  bytes image = 1;
  int32 face_index = 2;
}

message EmbedResponse {
  repeated float embedding = 1;
  float quality_score = 2;
  string model_version = 3;
}

message CompareRequest {
  repeated float embedding1 = 1;
  repeated float embedding2 = 2;
}

message CompareResponse {
  float similarity = 1;
  bool match = 2;
}

message LivenessRequest {
  bytes image = 1;
  bytes video = 2;
}

message LivenessResponse {
  bool is_live = 1;
  float confidence = 2;
  string attack_type = 3;
}

message SearchRequest {
  repeated float embedding = 1;
  int32 limit = 2;
  float threshold = 3;
}

message SearchResponse {
  repeated SearchResult results = 1;
}

message SearchResult {
  string id = 1;
  string user_id = 2;
  float similarity = 3;
}

message QuantumEmbedRequest {
  bytes image = 1;
  bool quantum_enhancement = 2;
}

message QuantumEmbedResponse {
  repeated float embedding = 1;
  float quality_score = 2;
  bool quantum_enhancement = 3;
}
```

### PQC Crypto Service

```protobuf
syntax = "proto3";

package cfzt.pqc;

service PQCCryptoService {
  rpc KemEncapsulate(KEMEncapsulateRequest) returns (KEMEncapsulateResponse);
  rpc KemDecapsulate(KEMDecapsulateRequest) returns (KEMDecapsulateResponse);
  rpc Sign(SignRequest) returns (SignResponse);
  rpc Verify(VerifyRequest) returns (VerifyResponse);
  rpc Encrypt(EncryptRequest) returns (EncryptResponse);
  rpc Decrypt(DecryptRequest) returns (DecryptResponse);
  rpc GetAlgorithms(GetAlgorithmsRequest) returns (AlgorithmsResponse);
}

message KEMEncapsulateRequest {
  string algorithm = 1;
  bytes public_key = 2;
}

message KEMEncapsulateResponse {
  bytes ciphertext = 1;
  bytes shared_secret = 2;
  string algorithm = 3;
}

message KEMDecapsulateRequest {
  string algorithm = 1;
  bytes ciphertext = 2;
  bytes private_key = 3;
}

message KEMDecapsulateResponse {
  bytes shared_secret = 1;
  string algorithm = 2;
}

message SignRequest {
  string algorithm = 1;
  bytes message = 2;
  bytes private_key = 3;
}

message SignResponse {
  bytes signature = 1;
  string algorithm = 2;
}

message VerifyRequest {
  string algorithm = 1;
  bytes message = 2;
  bytes signature = 3;
  bytes public_key = 4;
}

message VerifyResponse {
  bool valid = 1;
  string algorithm = 2;
}

message EncryptRequest {
  string algorithm = 1;
  bytes plaintext = 2;
  bytes public_key = 3;
}

message EncryptResponse {
  bytes ciphertext = 1;
  bytes nonce = 2;
  string algorithm = 3;
}

message DecryptRequest {
  string algorithm = 1;
  bytes ciphertext = 2;
  bytes nonce = 3;
  bytes private_key = 4;
}

message DecryptResponse {
  bytes plaintext = 1;
  string algorithm = 2;
}

message GetAlgorithmsRequest {}

message AlgorithmsResponse {
  repeated string kem = 1;
  repeated string signatures = 2;
  repeated string encryption = 3;
}
```

### ZK Proofs Service

```protobuf
syntax = "proto3";

package cfzt.zk;

service ZKProofsService {
  rpc GenerateProof(GenerateProofRequest) returns (GenerateProofResponse);
  rpc VerifyProof(VerifyProofRequest) returns (VerifyProofResponse);
  rpc GenerateFaceProof(FaceProofRequest) returns (FaceProofResponse);
  rpc GenerateLivenessProof(LivenessProofRequest) returns (LivenessProofResponse);
  rpc AggregateProofs(AggregateProofsRequest) returns (AggregateProofsResponse);
}

message GenerateProofRequest {
  string circuit = 1;
  map<string, bytes> witness = 2;
  map<string, bytes> public_inputs = 3;
}

message GenerateProofResponse {
  bytes proof = 1;
  map<string, bytes> public_outputs = 2;
  int32 proving_time_ms = 3;
  string circuit = 4;
}

message VerifyProofRequest {
  string circuit = 1;
  bytes proof = 2;
  map<string, bytes> public_inputs = 3;
}

message VerifyProofResponse {
  bool valid = 1;
  int32 verification_time_ms = 2;
  string circuit = 3;
}

message FaceProofRequest {
  repeated float embedding = 1;
  string stored_hash = 2;
  float threshold = 3;
}

message FaceProofResponse {
  bytes proof = 1;
  string commitment = 2;
  int32 proving_time_ms = 3;
}

message LivenessProofRequest {
  repeated float image_features = 1;
  float liveness_threshold = 2;
  string model_hash = 3;
}

message LivenessProofResponse {
  bytes proof = 1;
  string commitment = 2;
  int32 proving_time_ms = 3;
}

message AggregateProofsRequest {
  repeated Proof proofs = 1;
}

message AggregateProofsResponse {
  bytes aggregated_proof = 1;
  int32 num_proofs = 2;
  int32 aggregation_time_ms = 3;
}

message Proof {
  string circuit = 1;
  bytes proof = 2;
  map<string, bytes> public_inputs = 3;
}
```

### Quantum RNG Service

```protobuf
syntax = "proto3";

package cfzt.quantum;

service QuantumRNGService {
  rpc GenerateRandom(GenerateRandomRequest) returns (GenerateRandomResponse);
  rpc GetHealth(GetHealthRequest) returns (HealthResponse);
  rpc GetEntropyPool(GetEntropyPoolRequest) returns (EntropyPoolResponse);
}

message GenerateRandomRequest {
  int32 num_bits = 1;
  string purpose = 2;
  bool require_hardware = 3;
}

message GenerateRandomResponse {
  bytes random_data = 1;
  string source = 2;
  float min_entropy = 3;
  bool health_passed = 4;
  int32 num_bits = 5;
}

message GetHealthRequest {}

message HealthResponse {
  string status = 1;
  bool hardware_available = 2;
  bool simulator_available = 3;
  string last_health_check = 4;
  int32 health_tests_passed = 5;
  int32 health_tests_failed = 6;
}

message GetEntropyPoolRequest {}

message EntropyPoolResponse {
  int32 pool_size_bits = 1;
  int32 available_bits = 2;
  float fill_rate = 3;
  string last_refill = 4;
}
```

## Usage Examples

### Python

```python
import grpc
from cfzt.auth import auth_pb2_grpc, auth_pb2

# Create channel
channel = grpc.insecure_channel('auth-service:8080')
stub = auth_pb2_grpc.AuthServiceStub(channel)

# Login
request = auth_pb2.LoginRequest(
    user_id="user-123",
    device_id="device-456",
    face_image=face_image_bytes
)
response = stub.Login(request)
print(f"Token: {response.token}")
```

### Go

```go
package main

import (
    "context"
    "log"
    
    "google.golang.org/grpc"
    pb "github.com/cfzt/proto/auth"
)

func main() {
    // Create connection
    conn, err := grpc.Dial("auth-service:8080", grpc.WithInsecure())
    if err != nil {
        log.Fatalf("did not connect: %v", err)
    }
    defer conn.Close()
    
    // Create client
    client := pb.NewAuthServiceClient(conn)
    
    // Login
    response, err := client.Login(context.Background(), &pb.LoginRequest{
        UserId:    "user-123",
        DeviceId:  "device-456",
        FaceImage: faceImageBytes,
    })
    if err != nil {
        log.Fatalf("could not login: %v", err)
    }
    
    log.Printf("Token: %s", response.Token)
}
```

### Rust

```rust
use tonic::transport::Channel;
use cfzt::auth::auth_client::AuthServiceClient;
use cfzt::auth::LoginRequest;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Create channel
    let channel = Channel::from_static("http://auth-service:8080")
        .connect()
        .await?;
    
    // Create client
    let mut client = AuthServiceClient::new(channel);
    
    // Login
    let request = tonic::Request::new(LoginRequest {
        user_id: "user-123".to_string(),
        device_id: "device-456".to_string(),
        face_image: face_image_bytes,
    });
    
    let response = client.login(request).await?;
    println!("Token: {}", response.into_inner().token);
    
    Ok(())
}
```

## Error Codes

| Code | Description |
|------|-------------|
| OK | Success |
| INVALID_ARGUMENT | Invalid request parameters |
| NOT_FOUND | Resource not found |
| ALREADY_EXISTS | Resource already exists |
| PERMISSION_DENIED | Permission denied |
| UNAUTHENTICATED | Authentication required |
| RESOURCE_EXHAUSTED | Resource limit exceeded |
| FAILED_PRECONDITION | Precondition failed |
| ABORTED | Operation aborted |
| INTERNAL | Internal error |
| UNAVAILABLE | Service unavailable |
| DATA_LOSS | Data loss detected |
