FROM rust:1.78-bookworm AS builder
WORKDIR /app
COPY pkg/rust/ /app/pkg/rust/
COPY services/zk-proofs/ /app/services/zk-proofs/
COPY proto/ /app/proto/
RUN cd services/zk-proofs && cargo build --release

FROM debian:bookworm-slim AS production
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/services/zk-proofs/target/release/zk-proofs /usr/local/bin/
EXPOSE 8002 50053
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8002/health
ENTRYPOINT ["zk-proofs"]
