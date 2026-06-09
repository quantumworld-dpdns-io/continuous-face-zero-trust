# Key Rotation Procedures

## Classical Key Rotation

### JWT Signing Keys
1. Generate new Ed25519 key pair
2. Update Auth API config with new private key
3. Publish new public key to JWKS endpoint
4. Set old key as secondary (for verification only)
5. Wait for all tokens signed with old key to expire (24h)
6. Remove old key

### Redis Encryption Keys
1. Generate new AES-256 key
2. Update Redis config
3. Re-encrypt existing data
4. Remove old key from Secrets Manager

## PQC Key Rotation

### Kyber KEM Keys
1. Generate new Kyber-768 key pair
2. Re-encapsulate existing shared secrets
3. Update service configs
4. Verify NIST test vectors pass

### Dilithium Signature Keys
1. Generate new Dilithium-3 key pair
2. Re-sign critical data
3. Update verification keys in all services
4. Verify old signatures still validate

## Quantum Key Rotation

### QKD Session Keys
1. Initiate new BB84 key exchange
2. Verify QBER < 11%
3. Complete error reconciliation
4. Apply privacy amplification
5. Replace session keys
6. Secure-erase old keys

## Schedule
- JWT keys: Every 30 days
- PQC keys: Every 90 days
- QKD keys: Every session (automatic)
- Redis keys: Every 180 days
