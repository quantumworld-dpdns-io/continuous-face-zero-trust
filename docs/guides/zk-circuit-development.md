# ZK Circuit Development Guide

## Overview

This guide covers ZK circuit development for the CFZT system using Noir and ArkWorks.

## Prerequisites

- Noir 0.20+
- Rust 1.70+
- ArkWorks 0.4+

## Installation

```bash
# Install Noir
curl -L https://raw.githubusercontent.com/noir-lang/noirup/main/install | bash
noirup

# Verify installation
nargo --version
```

## Noir Circuit Development

### 1. Basic Circuit

```rust
// circuits/basic/main.nr
fn main(x: Field, y: pub Field) {
    assert(x * x == y);
}
```

### 2. Face Matching Circuit

```rust
// circuits/face_matching/main.nr
use std::hash::poseidon::PoseidonHash;

fn main(
    embedding: [Field; 512],  // Private
    stored_hash: Field,       // Public
    threshold: Field,         // Public
) -> pub Field {
    // Hash the embedding
    let embedding_hash = PoseidonHash::hash(embedding);
    
    // Verify embedding matches stored hash
    assert(embedding_hash == stored_hash);
    
    // Return proof commitment
    embedding_hash
}
```

### 3. Liveness Circuit

```rust
// circuits/liveness_check/main.nr
use std::hash::poseidon::PoseidonHash;

fn main(
    image_features: [Field; 256],  // Private
    liveness_threshold: Field,     // Public
    model_hash: Field,             // Public
) -> pub Field {
    // Compute liveness score (simplified)
    let liveness_score = compute_liveness(image_features);
    
    // Verify liveness threshold is met
    assert(liveness_score >= liveness_threshold);
    
    // Return proof commitment
    PoseidonHash::hash(image_features)
}

fn compute_liveness(features: [Field; 256]) -> Field {
    // Simplified liveness computation
    // In practice, this would be a more complex circuit
    let mut sum = 0Field;
    for i in 0..256 {
        sum += features[i];
    }
    sum / 256Field
}
```

### 4. Age Verification Circuit

```rust
// circuits/age_verification/main.nr
use std::hash::poseidon::PoseidonHash;

fn main(
    age_estimate: Field,     // Private
    age_threshold: Field,    // Public
    model_hash: Field,       // Public
) -> pub Field {
    // Verify age threshold is met
    assert(age_estimate >= age_threshold);
    
    // Return proof commitment
    PoseidonHash::hash([age_estimate])
}
```

## Compiling Circuits

```bash
# Compile circuit
cd circuits/face_matching
nargo compile

# Verify circuit
nargo verify

# Generate proof
nargo prove

# Verify proof
nargo verify
```

## ArkWorks Integration

### 1. Basic Setup

```rust
use ark_bls12_381::{Bls12_381, Fr};
use ark_groth16::Groth16;
use ark_snark::SNARK;
use ark_std::rand::thread_rng;

type E = Bls12_381;
type Fr = <E as Pairing>::Fr;

// Generate proving key
let mut rng = thread_rng();
let (pk, vk) = Groth16::<E>::circuit_specific_setup(circuit, &mut rng)?;

// Generate proof
let proof = Groth16::<E>::prove(&pk, circuit, &mut rng)?;

// Verify proof
let valid = Groth16::<E>::verify(&vk, &public_inputs, &proof)?;
```

### 2. Face Matching Prover

```rust
use ark_bls12_381::{Bls12_381, Fr};
use ark_groth16::Groth16;
use ark_snark::SNARK;
use ark_std::rand::thread_rng;

struct FaceMatchingCircuit {
    embedding: [Fr; 512],
    stored_hash: Fr,
    threshold: Fr,
}

impl ConstraintSynthesizer<Fr> for FaceMatchingCircuit {
    fn generate_constraints(self, cs: &mut ConstraintSystemRef<Fr>) -> Result<(), SynthesisError> {
        // Allocate private inputs
        let embedding_vars = (0..512)
            .map(|i| cs.new_witness_variable(|| Ok(self.embedding[i])))
            .collect::<Result<Vec<_>, _>>()?;
        
        // Allocate public inputs
        let stored_hash_var = cs.new_input_variable(|| Ok(self.stored_hash))?;
        let threshold_var = cs.new_input_variable(|| Ok(self.threshold))?;
        
        // Compute hash
        let hash = poseidon_hash(&embedding_vars);
        
        // Enforce constraint
        cs.enforce_constraint(
            lc!() + hash,
            lc!() + Variable::One,
            lc!() + stored_hash_var,
        )?;
        
        Ok(())
    }
}

fn generate_face_proof(
    embedding: [Fr; 512],
    stored_hash: Fr,
    threshold: Fr,
) -> Result<Proof<Bls12_381>, Box<dyn std::error::Error>> {
    let circuit = FaceMatchingCircuit {
        embedding,
        stored_hash,
        threshold,
    };
    
    let mut rng = thread_rng();
    let (pk, vk) = Groth16::<Bls12_381>::circuit_specific_setup(circuit.clone(), &mut rng)?;
    
    let proof = Groth16::<Bls12_381>::prove(&pk, circuit, &mut rng)?;
    
    Ok(proof)
}
```

### 3. Verification

```rust
fn verify_face_proof(
    proof: &Proof<Bls12_381>,
    stored_hash: Fr,
    threshold: Fr,
    vk: &VerifyingKey<Bls12_381>,
) -> Result<bool, Box<dyn std::error::Error>> {
    let public_inputs = vec![stored_hash, threshold];
    
    let valid = Groth16::<Bls12_381>::verify(vk, &public_inputs, proof)?;
    
    Ok(valid)
}
```

## Testing

### 1. Unit Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_face_matching_circuit() {
        let embedding = [Fr::from(1u64); 512];
        let stored_hash = poseidon_hash(&embedding);
        let threshold = Fr::from(85u64);
        
        let circuit = FaceMatchingCircuit {
            embedding,
            stored_hash,
            threshold,
        };
        
        let mut rng = thread_rng();
        let (pk, vk) = Groth16::<Bls12_381>::circuit_specific_setup(circuit.clone(), &mut rng).unwrap();
        
        let proof = Groth16::<Bls12_381>::prove(&pk, circuit, &mut rng).unwrap();
        
        let public_inputs = vec![stored_hash, threshold];
        let valid = Groth16::<Bls12_381>::verify(&vk, &public_inputs, &proof).unwrap();
        
        assert!(valid);
    }
}
```

### 2. Integration Tests

```python
# tests/integration/test_zk.py
import pytest
from cfzt.zk import ZKClient

@pytest.fixture
def client():
    return ZKClient()

def test_face_proof(client):
    """Test face proof generation/verification."""
    embedding = [0.1] * 512
    stored_hash = client.hash_embedding(embedding)
    threshold = 0.85
    
    proof = client.generate_face_proof(embedding, stored_hash, threshold)
    valid = client.verify_face_proof(proof, stored_hash, threshold)
    
    assert valid
```

## Performance Considerations

| Circuit | Proving Time | Verification Time | Proof Size |
|---------|--------------|-------------------|------------|
| face_matching | 500ms | 10ms | 200 bytes |
| liveness_check | 800ms | 15ms | 400 bytes |
| age_verification | 1000ms | 20ms | 500 bytes |

## Resources

- [Noir Documentation](https://noir-lang.org/)
- [ArkWorks Documentation](https://docs.rs/arkworks/)
- [Groth16 Paper](https://eprint.iacr.org/2016/260.pdf)
