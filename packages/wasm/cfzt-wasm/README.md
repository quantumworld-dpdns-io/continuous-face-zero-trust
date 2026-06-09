# cfzt-wasm

WebAssembly package for CFZT cryptographic operations.

## Building

```bash
# Install wasm-pack
cargo install wasm-pack

# Build
wasm-pack build --target web

# Test
wasm-pack test --headless --chrome
```

## Usage

```javascript
import init, { sha256, hmac_sha256 } from 'cfzt-wasm';

await init();

const hash = sha256(new TextEncoder().encode("hello"));
console.log(new Uint8Array(hash));
```

## Supported Operations
- SHA-256 hashing
- HMAC-SHA256
- Ed25519 signing (when available)
- Constant-time comparison
